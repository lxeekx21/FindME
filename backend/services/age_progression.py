import os
import io
import urllib.parse
from typing import Optional
from loguru import logger
from PIL import Image, ImageOps, ImageFilter
import aiohttp
from gradio_client import Client, file as gradio_file

# Choose public Hugging Face Spaces known for face aging.
# We will try them in order until one succeeds. You can override via env var
# AGE_PROGRESSION_SPACES as a comma-separated list of Space IDs. For backward
# compatibility, AGE_PROGRESSION_SPACE (single value) is also supported.
_env_spaces = os.getenv("AGE_PROGRESSION_SPACES")
_env_space = os.getenv("AGE_PROGRESSION_SPACE")
if _env_spaces:
    HF_SPACES = [s.strip() for s in _env_spaces.split(",") if s.strip()]
elif _env_space:
    HF_SPACES = [_env_space.strip()]
else:
    # Default priority list (try alternatives before the previous default)
    HF_SPACES = [
        "akhaliq/Photo-to-Older",  # alternative that often stays up
        "akhaliq/Face-Aging",      # previous default
    ]

CACHE_DIR = os.path.join("files", "age_progression")
os.makedirs(CACHE_DIR, exist_ok=True)


async def _download_image_to_bytes(url: str) -> bytes:
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=60) as resp:
            resp.raise_for_status()
            return await resp.read()


def _save_bytes_as_jpeg(content: bytes, path: str) -> None:
    try:
        with Image.open(io.BytesIO(content)) as img:
            rgb = img.convert("RGB")
            rgb.save(path, format="JPEG", quality=90)
    except Exception:
        # If Pillow can't parse, just write raw bytes
        with open(path, "wb") as f:
            f.write(content)


def _enhance_image_bytes(content: bytes, min_side: int = 1024) -> bytes:
    """Enhance visibility: upscale to a reasonable size, autocontrast, mild sharpen."""
    try:
        with Image.open(io.BytesIO(content)) as img:
            img = img.convert("RGB")
            w, h = img.size
            # Upscale so the shortest side is at least min_side (keep aspect ratio)
            short = min(w, h)
            if short < min_side:
                scale = min_side / float(short)
                new_size = (int(w * scale), int(h * scale))
                img = img.resize(new_size, Image.LANCZOS)
            # Auto-contrast and slight sharpen
            img = ImageOps.autocontrast(img, cutoff=1)
            img = img.filter(ImageFilter.UnsharpMask(radius=1.2, percent=120, threshold=3))
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=92)
            return buf.getvalue()
    except Exception:
        # If enhancement fails, return original content
        return content


async def generate_age_progression(
    submission_id: int,
    source_image_url: str,
    years: int,
    base_url: str,
    target_age: Optional[int] = None,
) -> Optional[str]:
    """
    Generate or retrieve cached age-progression image for a submission.

    Returns a public URL (absolute) to the cached image, or None on failure.
    """
    years = max(1, int(years or 1))
    # We keep cache key sensitive to years and (optionally) target_age bucket to avoid mismatched outputs
    age_bucket = None
    if target_age is not None:
        # Bucket target age into decades for caching granularity
        if target_age < 20:
            age_bucket = "<20"
        elif target_age < 30:
            age_bucket = "20s"
        elif target_age < 40:
            age_bucket = "30s"
        elif target_age < 50:
            age_bucket = "40s"
        elif target_age < 60:
            age_bucket = "50s"
        else:
            age_bucket = "60+"
    cache_suffix = f"_{age_bucket}" if age_bucket else ""
    cache_filename = f"ap_{submission_id}_{years}{cache_suffix}.jpg"
    cache_path = os.path.join(CACHE_DIR, cache_filename)

    if os.path.exists(cache_path):
        return f"{base_url}/files/age_progression/{urllib.parse.quote(cache_filename)}"

    # Normalize source URL: allow stored relative paths like '/files/...'
    resolved_src_url = source_image_url or ""
    if resolved_src_url and not resolved_src_url.startswith("http://") and not resolved_src_url.startswith("https://"):
        # Ensure base_url has no trailing slash
        base = base_url.rstrip("/")
        # If source starts with '/', avoid double slash
        if resolved_src_url.startswith("/"):
            resolved_src_url = f"{base}{resolved_src_url}"
        else:
            resolved_src_url = f"{base}/{resolved_src_url}"

    # Download source image bytes
    try:
        src_bytes = await _download_image_to_bytes(resolved_src_url)
    except Exception as e:
        logger.error(f"Failed to download source image for submission {submission_id}: {resolved_src_url} :: {e}")
        return None

    # Try calling one of the HF Spaces via gradio_client (in priority order)
    # We attempt each candidate Space; if all fail, we fallback to enhanced original.
    # Map target age to an age group label expected by common Spaces
    if target_age is not None:
        if target_age < 25:
            age_group = "20-30"
        elif target_age < 35:
            age_group = "30-40"
        elif target_age < 45:
            age_group = "40-50"
        elif target_age < 60:
            age_group = "50-60"
        else:
            age_group = "60-70"
    else:
        # Fallback heuristic purely on elapsed years
        if years >= 15:
            age_group = "50-60"
        elif years >= 10:
            age_group = "40-50"
        else:
            age_group = "30-40"

    last_err = None
    for space in HF_SPACES:
        try:
            logger.info(f"Age progression: trying HF Space '{space}'")
            client = Client(space)
            result = None
            try:
                # Try a simple predict with two params (image, age_group)
                result = client.predict(
                    gradio_file(io.BytesIO(src_bytes), file_name="input.jpg"),
                    age_group,
                    api_name="predict",
                )
            except Exception:
                # Fallback: try single image param (some Spaces infer age increase)
                result = client.predict(
                    gradio_file(io.BytesIO(src_bytes), file_name="input.jpg"),
                    api_name="predict",
                )
            # The result can be a path or bytes. gradio_client returns a path-like or URL.
            out_bytes: Optional[bytes] = None
            if isinstance(result, (list, tuple)):
                result = result[0]
            if isinstance(result, bytes):
                out_bytes = result
            elif isinstance(result, str):
                # Possibly a temp file path or URL; try to read it
                if os.path.exists(result):
                    with open(result, "rb") as f:
                        out_bytes = f.read()
                else:
                    # assume URL
                    out_bytes = await _download_image_to_bytes(result)
            if not out_bytes:
                raise RuntimeError("Empty output from age progression space")

            # Enhance visibility before saving
            enhanced = _enhance_image_bytes(out_bytes)
            with open(cache_path, "wb") as f:
                f.write(enhanced)
            logger.info(f"Age progression succeeded with Space '{space}', cached at {cache_filename}")
            return f"{base_url}/files/age_progression/{urllib.parse.quote(cache_filename)}"
        except Exception as e:
            last_err = e
            logger.warning(f"Age progression failed with Space '{space}': {e}")
            continue

    # All Spaces failed → fallback: cache an enhanced version of the original so we don't re-hit every time
    try:
        if 'src_bytes' in locals() and src_bytes:
            enhanced_src = _enhance_image_bytes(src_bytes)
            with open(cache_path, "wb") as f:
                f.write(enhanced_src)
            logger.error(f"All HF Spaces failed for submission {submission_id}. Cached original (enhanced). Last error: {last_err}")
            return f"{base_url}/files/age_progression/{urllib.parse.quote(cache_filename)}"
    except Exception as e2:
        logger.error(f"Fallback caching failed: {e2}. Last model error: {last_err}")
    return None
