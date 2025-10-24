#!/usr/bin/env python3
"""
Seed script for FindSouth API

Features:
- Creates test admins and users with predictable emails and password 123456
  • Admin emails: admin[x]@test.com (x = 1..N)
  • User emails:  user[x]@test.com  (x = 1..M)
- Downloads random profile images and stores them under ./files, updating profile_image_url.
- Creates missing person submissions with at least 3 images each stored under ./files/submissions.

Defaults:
- 12 admins and 12 users
- 200 submissions

Usage examples:
  python api/scripts/seed_test_data.py
  python api/scripts/seed_test_data.py --admins 5 --users 10 --subs 40

Notes:
- The script is idempotent regarding user emails: it will skip creating a user if the email exists.
- Image URLs saved in DB are relative (/files/...) so they work regardless of host.
- Requires the API project's dependencies and a configured database.
"""
import asyncio
import argparse
import os
import uuid
import random
import string
import logging
import ssl
import socket
import math
from contextlib import asynccontextmanager
from datetime import date, timedelta, datetime, timezone
from typing import List, Optional, Tuple

import aiohttp
import certifi

# Ensure the project 'api' root is on sys.path so `app.*` imports work when running this script directly
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.db.session import AsyncSessionLocal
from app.db.repositories.users import UserRepository
from app.db.repositories.submissions import SubmissionRepository
from app.db.repositories.comments import CommentRepository
from app.auth.local_auth import hash_password

# ------------ Logging ------------
LOG_FORMAT = "[%(asctime)s] %(levelname)s %(name)s :: %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, datefmt="%H:%M:%S")
logger = logging.getLogger("seed")

# ------------ Paths (absolute to avoid CWD issues) ------------
BASE_DIR = Path(__file__).resolve().parents[1]        # .../api
FILES_DIR = BASE_DIR / "files"
SUBS_DIR  = FILES_DIR / "submissions"

# ---- Constants / helpers ----
PROFILE_IMAGES_SOURCES = [
    # RandomUser portraits (deterministic paths 0..99)
    "https://randomuser.me/api/portraits/men/{n}.jpg",
    "https://randomuser.me/api/portraits/women/{n}.jpg",
]

# Friendlier fallbacks than TPDNE
PROFILE_FALLBACKS = [
    "https://i.pravatar.cc/512?img={n}",        # n typically 1..70
    "https://picsum.photos/seed/{n}/512/512",   # stable by seed
]

# thispersondoesnotexist provides a random face at the root URL (often CF-protected)
MISSING_PERSON_IMAGE_SOURCE = "https://thispersondoesnotexist.com/"  # jpg bytes
TPDNE = MISSING_PERSON_IMAGE_SOURCE

GENDERS = ["male", "female"]
RACES = [
    "black_african",
    "coloured",
    "white",
    "asian_or_indian",
    "other",
]
PROVINCES = [
    "eastern_cape",
    "free_state",
    "gauteng",
    "kwazulu_natal",
    "limpopo",
    "mpumalanga",
    "north_west",
    "northern_cape",
    "western_cape",
]

# Submission statuses
SUBMISSION_STATUSES = ["pending", "published", "rejected", "found_alive", "found_dead"]

# Curated SA addresses with realistic coordinates (no random coords)
# Province codes match PROVINCES list values
ADDRESSES = [
    {"address": "Johannesburg, Gauteng", "province": "gauteng", "lat": -26.2041, "lng": 28.0473},
    {"address": "Pretoria, Gauteng", "province": "gauteng", "lat": -25.7479, "lng": 28.2293},
    {"address": "Soweto, Gauteng", "province": "gauteng", "lat": -26.2661, "lng": 27.8650},
    {"address": "Tembisa, Gauteng", "province": "gauteng", "lat": -25.9980, "lng": 28.2268},
    {"address": "Mamelodi, Gauteng", "province": "gauteng", "lat": -25.7150, "lng": 28.3910},
    {"address": "Soshanguve, Gauteng", "province": "gauteng", "lat": -25.5403, "lng": 28.1034},

    {"address": "Cape Town, Western Cape", "province": "western_cape", "lat": -33.9249, "lng": 18.4241},
    {"address": "Stellenbosch, Western Cape", "province": "western_cape", "lat": -33.9321, "lng": 18.8602},
    {"address": "Paarl, Western Cape", "province": "western_cape", "lat": -33.7342, "lng": 18.9621},
    {"address": "Worcester, Western Cape", "province": "western_cape", "lat": -33.6461, "lng": 19.4485},
    {"address": "George, Western Cape", "province": "western_cape", "lat": -33.9640, "lng": 22.4617},
    {"address": "Oudtshoorn, Western Cape", "province": "western_cape", "lat": -33.5906, "lng": 22.2013},
    {"address": "Knysna, Western Cape", "province": "western_cape", "lat": -34.0363, "lng": 23.0471},

    {"address": "Durban, KwaZulu-Natal", "province": "kwazulu_natal", "lat": -29.8587, "lng": 31.0218},
    {"address": "Pietermaritzburg, KwaZulu-Natal", "province": "kwazulu_natal", "lat": -29.6006, "lng": 30.3794},
    {"address": "Richards Bay, KwaZulu-Natal", "province": "kwazulu_natal", "lat": -28.7807, "lng": 32.0383},
    {"address": "Newcastle, KwaZulu-Natal", "province": "kwazulu_natal", "lat": -27.7579, "lng": 29.9318},
    {"address": "Umlazi, KwaZulu-Natal", "province": "kwazulu_natal", "lat": -29.9700, "lng": 30.9000},
    {"address": "Port Shepstone, KwaZulu-Natal", "province": "kwazulu_natal", "lat": -30.7414, "lng": 30.4545},

    {"address": "Gqeberha, Eastern Cape", "province": "eastern_cape", "lat": -33.9608, "lng": 25.6022},
    {"address": "East London, Eastern Cape", "province": "eastern_cape", "lat": -33.0153, "lng": 27.9116},
    {"address": "Mthatha, Eastern Cape", "province": "eastern_cape", "lat": -31.5889, "lng": 28.7844},
    {"address": "Makhanda (Grahamstown), Eastern Cape", "province": "eastern_cape", "lat": -33.3100, "lng": 26.5200},
    {"address": "Komani (Queenstown), Eastern Cape", "province": "eastern_cape", "lat": -31.8976, "lng": 26.8754},

    {"address": "Bloemfontein, Free State", "province": "free_state", "lat": -29.0852, "lng": 26.1596},
    {"address": "Welkom, Free State", "province": "free_state", "lat": -27.9864, "lng": 26.7066},
    {"address": "Bethlehem, Free State", "province": "free_state", "lat": -28.2300, "lng": 28.3100},
    {"address": "Kroonstad, Free State", "province": "free_state", "lat": -27.6500, "lng": 27.2333},

    {"address": "Polokwane, Limpopo", "province": "limpopo", "lat": -23.9045, "lng": 29.4689},
    {"address": "Thohoyandou, Limpopo", "province": "limpopo", "lat": -22.9556, "lng": 30.4417},
    {"address": "Musina, Limpopo", "province": "limpopo", "lat": -22.3510, "lng": 30.0405},

    {"address": "Mbombela (Nelspruit), Mpumalanga", "province": "mpumalanga", "lat": -25.4658, "lng": 30.9853},
    {"address": "eMalahleni (Witbank), Mpumalanga", "province": "mpumalanga", "lat": -25.8713, "lng": 29.2332},
    {"address": "Middelburg, Mpumalanga", "province": "mpumalanga", "lat": -25.7751, "lng": 29.4648},
    {"address": "Secunda, Mpumalanga", "province": "mpumalanga", "lat": -26.5500, "lng": 29.2000},

    {"address": "Mahikeng, North West", "province": "north_west", "lat": -25.8656, "lng": 25.6442},
    {"address": "Rustenburg, North West", "province": "north_west", "lat": -25.6676, "lng": 27.2421},
    {"address": "Klerksdorp, North West", "province": "north_west", "lat": -26.8521, "lng": 26.6667},
    {"address": "Potchefstroom, North West", "province": "north_west", "lat": -26.7167, "lng": 27.1000},
    {"address": "Vereeniging, Gauteng", "province": "gauteng", "lat": -26.6731, "lng": 27.9261},

    {"address": "Kimberley, Northern Cape", "province": "northern_cape", "lat": -28.7282, "lng": 24.7499},
    {"address": "Upington, Northern Cape", "province": "northern_cape", "lat": -28.4541, "lng": 21.2429},
    {"address": "Springbok, Northern Cape", "province": "northern_cape", "lat": -29.6643, "lng": 17.8860},
    {"address": "Kuruman, Northern Cape", "province": "northern_cape", "lat": -27.4524, "lng": 23.4325},
]

PRONOUNS = {
    "male": {"subj": "He", "obj": "him", "poss": "his"},
    "female": {"subj": "She", "obj": "her", "poss": "her"},
}

DEFAULT_HEADERS = {"User-Agent": "Mozilla/5.0 (FindSouth Seeder)"}


def rand_name(gender: Optional[str] = None) -> tuple[str, str]:
    """Return a random first and last name, without any race-based assumptions.
    Gender may be used only to bias first-name pool; otherwise names are random.
    """
    male_first_common = ["John", "Peter", "Sipho", "Thabo", "Liam", "Noah", "Ethan", "Jabulani"]
    female_first_common = ["Mary", "Thandi", "Emma", "Olivia", "Ava", "Isabella", "Keabetswe", "Naledi"]
    surnames_common = ["Smith", "Botha", "Dlamini", "Naidoo", "Pillay", "Brown", "Williams", "Jacobs", "Singh", "Molefe"]

    g = "male" if gender == "male" else ("female" if gender == "female" else random.choice(["male", "female"]))
    first_pool = male_first_common if g == "male" else female_first_common

    first = random.choice(first_pool)
    last = random.choice(surnames_common)
    return first, last


def rand_full_name(gender: Optional[str] = None) -> str:
    fn, ln = rand_name(gender)
    return f"{fn} {ln}"


def ensure_dirs() -> None:
    FILES_DIR.mkdir(exist_ok=True)
    SUBS_DIR.mkdir(parents=True, exist_ok=True)
    logger.debug("Ensured directories: %s , %s", FILES_DIR, SUBS_DIR)


@asynccontextmanager
async def _timed(section: str):
    start = datetime.now(timezone.utc)
    try:
        yield
    finally:
        dur = (datetime.now(timezone.utc) - start).total_seconds()
        logger.debug("%s took %.3fs", section, dur)


async def fetch_once(session: aiohttp.ClientSession, url: str, headers: Optional[dict] = None) -> Optional[bytes]:
    hdrs = {**DEFAULT_HEADERS, **(headers or {})}
    try:
        async with _timed(f"GET {url}"):
            async with session.get(url, headers=hdrs, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                ctype = (resp.headers.get("Content-Type") or "")
                if resp.status == 200 and ctype.startswith("image/"):
                    data = await resp.read()
                    logger.debug("Fetched %s (%d bytes, %s)", url, len(data), ctype)
                    return data
                logger.warning("Fetch failed: %s status=%s ctype=%s", url, resp.status, ctype)
                return None
    except Exception:
        logger.exception("Fetch error: %s", url)
        return None


async def fetch_with_retry(session: aiohttp.ClientSession, url: str, headers: Optional[dict] = None,
                           attempts: int = 3, backoff: float = 0.8) -> Optional[bytes]:
    for i in range(1, attempts + 1):
        data = await fetch_once(session, url, headers=headers)
        if data:
            if i > 1:
                logger.info("Succeeded after retry %d: %s", i - 1, url)
            return data
        if i < attempts:
            sleep_for = backoff * i
            logger.info("Retrying in %.1fs (attempt %d/%d) %s", sleep_for, i + 1, attempts, url)
            await asyncio.sleep(sleep_for)
    logger.error("All retries failed for %s", url)
    return None


def build_profile_filename(user_id: int, ext: str = ".jpg") -> str:
    return f"user_{user_id}_{uuid.uuid4().hex}{ext}"


def build_submission_filename(user_id: int, ext: str = ".jpg") -> str:
    return f"sub_{user_id}_{uuid.uuid4().hex}{ext}"


async def save_profile_image(session_http: aiohttp.ClientSession, user_id: int, gender: Optional[str] = None) -> Optional[str]:
    # Try RandomUser first with a random index
    n = random.randint(0, 99)
    if gender == "female":
        primary = PROFILE_IMAGES_SOURCES[1].format(n=n)
    elif gender == "male":
        primary = PROFILE_IMAGES_SOURCES[0].format(n=n)
    else:
        primary = random.choice(PROFILE_IMAGES_SOURCES).format(n=n)

    # Add friendlier fallbacks
    n2 = random.randint(1, 70)
    urls = [primary] + [u.format(n=n2) for u in PROFILE_FALLBACKS] + [TPDNE]

    logger.debug("Profile image attempt for user_id=%s gender=%s urls=%s", user_id, gender, urls)

    img = None
    for u in urls:
        img = await fetch_with_retry(session_http, u, headers={"User-Agent": DEFAULT_HEADERS["User-Agent"]})
        if img:
            logger.info("Profile image source chosen for user_id=%s: %s", user_id, u)
            break

    if not img:
        logger.error("Could not fetch profile image for user_id=%s", user_id)
        return None

    ensure_dirs()
    filename = build_profile_filename(user_id)
    path = FILES_DIR / filename
    path.write_bytes(img)
    logger.info("Wrote profile image: %s (%d bytes)", path, path.stat().st_size)

    # Return relative URL so it works regardless of host
    return f"http://localhost:8000/files/{filename}"


def _estimate_age_from_image_bytes(img_bytes: bytes) -> Optional[int]:
    """Try to estimate age from an image using DeepFace. Returns an integer age or None.
    This is optional: if dependencies/models are missing, we fail silently and return None.
    """
    try:
        import numpy as np  # type: ignore
        import cv2  # type: ignore
        from deepface import DeepFace  # type: ignore
        arr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            return None
        # DeepFace.analyze can return list or dict
        res = DeepFace.analyze(img, actions=['age'], enforce_detection=False, detector_backend='opencv', prog_bar=False)
        if isinstance(res, list):
            res = res[0] if res else {}
        age_val = res.get('age') if isinstance(res, dict) else None
        if age_val is None:
            return None
        try:
            return int(round(float(age_val)))
        except Exception:
            return None
    except Exception:
        return None


async def generate_missing_images(session_http: aiohttp.ClientSession, owner_user_id: int, count: int = 3, gender: Optional[str] = None) -> tuple[List[str], Optional[int]]:
    """
    Create multiple images for a single case from one base portrait so identity stays consistent.
    Prefer a gender-matched RandomUser portrait to avoid mismatches (e.g., female record with a boy photo).
    Also attempts to estimate age from the base image using DeepFace (optional).
    Returns: (image_urls, estimated_age_or_None)
    """
    ensure_dirs()
    urls: List[str] = []

    logger.debug("Generating %d images (owner_user_id=%s, gender=%s)", count, owner_user_id, gender)

    # 1) Fetch one base image — try TPDNE then RandomUser then pravatar
    base_img = await fetch_with_retry(
        session_http,
        TPDNE,
        headers={"User-Agent": DEFAULT_HEADERS["User-Agent"]},
    )

    if not base_img:
        # As a fallback only, try RandomUser with a random gender/index
        n = random.randint(0, 99)
        ru_url = random.choice(PROFILE_IMAGES_SOURCES).format(n=n)
        logger.info("Base image fallback -> %s", ru_url)
        base_img = await fetch_with_retry(session_http, ru_url)

    if not base_img:
        n = random.randint(1, 70)
        pv = PROFILE_FALLBACKS[0].format(n=n)
        logger.info("Second fallback -> %s", pv)
        base_img = await fetch_with_retry(session_http, pv)

    if not base_img:
        logger.error("Failed to obtain base image for owner_user_id=%s", owner_user_id)
        return urls, None  # give up gracefully

    # Attempt age estimation first
    estimated_age = _estimate_age_from_image_bytes(base_img)
    if estimated_age is not None:
        logger.debug("Estimated age from base image: %s", estimated_age)
    else:
        logger.debug("Estimated age unavailable (DeepFace not installed or detection failed)")

    # Convert to PIL Image for augmentations
    try:
        from PIL import Image, ImageEnhance, ImageFilter  # type: ignore
        from io import BytesIO
    except Exception:
        # If Pillow is not installed, fallback to saving identical copies
        logger.warning("Pillow not installed; saving %d identical copies", max(1, count))
        for _ in range(max(1, count)):
            filename = build_submission_filename(owner_user_id)
            path = SUBS_DIR / filename
            try:
                path.write_bytes(base_img)
                urls.append(f"/files/submissions/{filename}")
                logger.info("Saved submission image (raw copy): %s", path)
            except Exception:
                logger.exception("Failed to write submission image: %s", path)
        return urls, estimated_age

    try:
        img = Image.open(BytesIO(base_img)).convert("RGB")
    except Exception:
        logger.warning("PIL decode failed; writing raw copies")
        for _ in range(max(1, count)):
            filename = build_submission_filename(owner_user_id)
            path = SUBS_DIR / filename
            try:
                path.write_bytes(base_img)
                urls.append(f"/files/submissions/{filename}")
                logger.info("Saved submission image (raw copy): %s", path)
            except Exception:
                logger.exception("Failed to write submission image: %s", path)
        return urls, estimated_age

    def save_variant(pil_img, note: str) -> None:
        filename = build_submission_filename(owner_user_id)
        path = SUBS_DIR / filename
        try:
            pil_img.save(path, format="JPEG", quality=92)
            urls.append(f"/files/submissions/{filename}")
            logger.info("Saved submission image %s: %s", f"({note})" if note else "", path)
        except Exception:
            logger.exception("Failed to save variant (%s): %s", note, path)

    # Variant A: as-is
    save_variant(img, "as-is")

    # Variant B: slight crop + brightness tweak
    try:
        w, h = img.size
        crop = img.crop((int(0.05*w), int(0.05*h), int(0.95*w), int(0.95*h))).resize((w, h), Image.LANCZOS)
        bright = ImageEnhance.Brightness(crop).enhance(1.06)
        save_variant(bright, "crop+bright")
    except Exception:
        save_variant(img, "fallback-B")

    # Variant C: horizontal flip + mild blur + contrast tweak
    try:
        flip = img.transpose(Image.FLIP_LEFT_RIGHT)
        blur = flip.filter(ImageFilter.GaussianBlur(radius=0.3))
        contr = ImageEnhance.Contrast(blur).enhance(1.08)
        save_variant(contr, "flip+blur+contrast")
    except Exception:
        save_variant(img, "fallback-C")

    # If more requested, generate additional small variations (rotate, color)
    extra_needed = max(0, count - len(urls))
    for _ in range(extra_needed):
        try:
            angle = random.choice([-2, -1, 1, 2])
            rotated = img.rotate(angle, resample=Image.BICUBIC, expand=False)
            color = ImageEnhance.Color(rotated).enhance(random.uniform(0.9, 1.1))
            save_variant(color, f"rotate({angle})+color")
        except Exception:
            save_variant(img, "fallback-extra")

    logger.debug("Generated %d submission images", len(urls))
    return urls, estimated_age


async def create_or_get_user(repo: UserRepository, email: str, password_plain: str, first_name: Optional[str], last_name: Optional[str]) -> int:
    existing = await repo.get_by_email(email)
    if existing:
        return existing.id
    pw_hash = hash_password(password_plain)
    user = await repo.create_user(email=email, password_hash=pw_hash, first_name=first_name, last_name=last_name)
    return user.id


async def seed_users(db_session, admins: int, users: int) -> tuple[List[int], List[int]]:
    repo = UserRepository(db_session)
    admin_role = await repo.get_or_create_role("admin")
    user_role = await repo.get_or_create_role("user")

    created_admin_ids: List[int] = []
    created_user_ids: List[int] = []

    # Robust connector: certifi CA + IPv4 (avoids some IPv6 hiccups), honor proxies
    ssl_ctx = ssl.create_default_context(cafile=certifi.where())
    connector = aiohttp.TCPConnector(ssl=ssl_ctx, family=socket.AF_INET, limit_per_host=4)

    async with aiohttp.ClientSession(connector=connector, trust_env=True) as http:
        # Admins
        for i in range(1, admins + 1):
            gender = random.choice(GENDERS)
            fn, ln = rand_name(gender)
            email = f"admin{i}@test.com"
            user_id = await create_or_get_user(repo, email, "123456", fn, ln)
            # Assign admin role
            await repo.add_role(user_id, admin_role.id)
            logger.info("Created/loaded admin %s (id=%s)", email, user_id)
            # Profile image
            pic = await save_profile_image(http, user_id, gender)
            logger.debug("Profile image for user_id=%s -> %s", user_id, pic)
            if pic:
                await repo.update_user(user_id, profile_image_url=pic)
            created_admin_ids.append(user_id)

        # Users
        for i in range(1, users + 1):
            gender = random.choice(GENDERS)
            fn, ln = rand_name(gender)
            email = f"user{i}@test.com"
            user_id = await create_or_get_user(repo, email, "123456", fn, ln)
            # Assign user role
            await repo.add_role(user_id, user_role.id)
            logger.info("Created/loaded user %s (id=%s)", email, user_id)
            # Profile image
            pic = await save_profile_image(http, user_id, gender)
            logger.debug("Profile image for user_id=%s -> %s", user_id, pic)
            if pic:
                await repo.update_user(user_id, profile_image_url=pic)
            created_user_ids.append(user_id)

    return created_admin_ids, created_user_ids


def sample_age_years() -> int:
    """
    Sample a realistic age distribution for missing persons.
    Buckets: 5–12 (child), 13–17 (teen), 18–29 (young adult), 30–49 (adult), 50–79 (senior)
    Weights are illustrative for demo data only.
    """
    buckets = [range(5, 13), range(13, 18), range(18, 30), range(30, 50), range(50, 80)]
    weights = [0.12, 0.28, 0.32, 0.22, 0.06]
    bucket = random.choices(buckets, weights=weights, k=1)[0]
    return random.choice(list(bucket))


def rand_description(full_name: str, age: int, gender: Optional[str], last_seen_address: str, height_cm: float, weight_kg: float, race: Optional[str]) -> str:
    g = "female" if gender == "female" else ("male" if gender == "male" else random.choice(["male", "female"]))
    p = PRONOUNS[g]
    clothing_colors = ["blue", "black", "grey", "green", "red", "brown"]
    items_top = ["hoodie", "jacket", "t-shirt", "sweater"]
    items_bottom = ["jeans", "pants", "trousers", "shorts"]
    top = f"{random.choice(clothing_colors)} {random.choice(items_top)}"
    bottom = f"{random.choice(clothing_colors)} {random.choice(items_bottom)}"
    features = [
        "quiet and reserved",
        "friendly but shy",
        "may be disoriented",
        "requires regular medication",
        "has a small scar on the left eyebrow",
        "wears glasses",
    ]
    feat = random.choice(features)
    parts = [
        f"{full_name} ({age}) was last seen near {last_seen_address}.",
        f"{p['subj']} was wearing a {top} and {bottom}.",
        f"{p['subj']} is {feat}.",
        f"Approximate height {height_cm} cm and weight {weight_kg} kg.",
        "If you have any information, please contact the authorities or the family.",
    ]
    return " ".join(parts)


def rand_phone() -> str:
    return "0" + "".join(random.choices(string.digits, k=9))


def random_point_within_radius_km(lat_deg: float, lng_deg: float, max_km: float = 10.0) -> Tuple[float, float]:
    """
    Generate a random point within a circle of radius `max_km` around (lat_deg, lng_deg).
    Uses a forward geodesic on a spherical Earth to avoid distortion.
    Returns (lat, lng) in degrees.
    """
    R_km = 6371.0
    # Random distance 0..max_km, random bearing 0..2π
    distance_rad = (random.random() * max_km) / R_km
    bearing = random.uniform(0.0, 2.0 * math.pi)

    lat1 = math.radians(lat_deg)
    lon1 = math.radians(lng_deg)

    sin_lat1 = math.sin(lat1)
    cos_lat1 = math.cos(lat1)
    sin_d = math.sin(distance_rad)
    cos_d = math.cos(distance_rad)
    sin_b = math.sin(bearing)
    cos_b = math.cos(bearing)

    lat2 = math.asin(sin_lat1 * cos_d + cos_lat1 * sin_d * cos_b)
    lon2 = lon1 + math.atan2(sin_b * sin_d * cos_lat1, cos_d - sin_lat1 * math.sin(lat2))

    # Normalize longitude to [-180, 180]
    lon2 = (lon2 + 3 * math.pi) % (2 * math.pi) - math.pi

    return round(math.degrees(lat2), 6), round(math.degrees(lon2), 6)


def sample_created_at() -> datetime:
    """Return a realistic created_at spanning from now back to ~25 years."""
    now = datetime.now(timezone.utc)

    p = random.random()

    # Helpers to convert a fractional year span into a backdated datetime
    def pick_in_years_range(start_years: float, end_years: float) -> datetime:
        years = random.uniform(start_years, end_years)
        days_ago = max(1, int(years * 365.25) + random.randint(0, 364))
        seconds_in_day = 24 * 3600
        extra_seconds = random.randint(0, seconds_in_day)
        dt_inner = now - timedelta(days=days_ago, seconds=extra_seconds)
        if dt_inner > now:
            dt_inner = now - timedelta(seconds=random.randint(1, 3600))
        return dt_inner

    three_days_y = 3.0 / 365.25
    one_month_y = 30.0 / 365.25
    three_months_y = 0.25

    # 5%: within last 72 hours
    if p < 0.05:
        seconds_ago = random.randint(0, 72 * 3600)
        dt = now - timedelta(seconds=seconds_ago)
        if dt > now:
            dt = now - timedelta(seconds=random.randint(1, 3600))
        return dt

    # 15%: 3 days – 1 month
    if p < 0.20:
        return pick_in_years_range(three_days_y, one_month_y)

    # 20%: 1 – 3 months
    if p < 0.40:
        return pick_in_years_range(one_month_y, three_months_y)

    # 30%: 3 months – 1 year
    if p < 0.70:
        return pick_in_years_range(three_months_y, 1.0)

    # Remaining 30%: share equally across longer tails
    tail_buckets = [
        (1.0, 5.0),
        (5.0, 10.0),
        (10.0, 15.0),
        (15.0, 25.0),
    ]
    start_y, end_y = random.choice(tail_buckets)
    return pick_in_years_range(start_y, end_y)


async def seed_submissions(db_session, min_count: int, candidate_user_ids: List[int]) -> List[int]:
    repo = SubmissionRepository(db_session)
    created_ids: List[int] = []

    # Build a status plan targeting 50% published overall and at least some 'found'
    target_published = int(round(min_count * 0.5))
    target_published = max(0, min(min_count, target_published))
    remaining_after_published = max(0, min_count - target_published)

    # Keep a reasonable number of 'found' cases if possible (up to 10)
    must_found = min(10, remaining_after_published)

    planned_statuses: List[str] = []
    planned_statuses.extend(["published"] * target_published)

    # Split required 'found' quota between alive and dead
    alive_quota = must_found // 2
    dead_quota = must_found - alive_quota
    planned_statuses.extend(["found_alive"] * alive_quota)
    planned_statuses.extend(["found_dead"] * dead_quota)

    # Fill the rest with non-published statuses to preserve the 75% ratio
    rest = max(0, min_count - len(planned_statuses))
    non_published_statuses = [s for s in SUBMISSION_STATUSES if s != "published"]
    for _ in range(rest):
        planned_statuses.append(random.choice(non_published_statuses))

    # Shuffle to avoid clustering the same statuses
    random.shuffle(planned_statuses)

    ssl_ctx = ssl.create_default_context(cafile=certifi.where())
    connector = aiohttp.TCPConnector(ssl=ssl_ctx, family=socket.AF_INET, limit_per_host=4)

    async with aiohttp.ClientSession(connector=connector, trust_env=True) as http:
        for idx in range(min_count):
            if idx % 25 == 0:
                logger.info("...seeding submissions %d/%d", idx + 1, min_count)

            gender = random.choice(GENDERS)
            race = random.choice(RACES)
            full_name = rand_full_name(gender)
            # Choose a realistic address entry and derive province/coords from it
            addr = random.choice(ADDRESSES)
            province = addr["province"]

            owner_id = random.choice(candidate_user_ids) if candidate_user_ids else None

            images, est_age = await generate_missing_images(http, owner_user_id=owner_id or 0, count=3, gender=gender)

            # Sample a realistic age, then override with estimated if available
            age = sample_age_years()
            if est_age is not None:
                # Clamp to a reasonable range
                age = int(max(5, min(79, est_age)))
            # Randomize within the birth year
            days_offset = random.randint(0, 364)
            dob = date.today() - timedelta(days=age * 365 + days_offset)

            # Realistic height (cm) and weight (kg) based on (possibly adjusted) age and gender
            if age >= 18:
                h_cm = random.gauss(174, 7) if gender == "male" else random.gauss(161, 7)
            else:
                h_cm = random.gauss(160 if gender == "male" else 155, 10)
            h_cm = max(120, min(205, h_cm))

            bmi = random.uniform(19, 30) if age >= 18 else random.uniform(17, 28)
            weight_kg = bmi * (h_cm / 100) * (h_cm / 100)

            height = round(h_cm, 1)
            weight = round(weight_kg, 1)

            last_seen_address = addr["address"]
            description = rand_description(full_name, age, gender, last_seen_address, height, weight, race)
            # Randomize coordinates within 10 km from the base address to avoid clustering at one point
            last_seen_lat, last_seen_lng = random_point_within_radius_km(addr["lat"], addr["lng"], max_km=10)

            # Use planned status to ensure minimum counts
            status = planned_statuses[idx]
            created_at = sample_created_at()

            sub = await repo.create(
                title=f"Missing person: {full_name}",
                full_name=full_name,
                dob=dob,
                gender=gender,
                race=race,
                height=height,
                weight=weight,
                province=province,
                description=description,
                last_seen_address=last_seen_address,
                last_seen_place_id=None,
                last_seen_lat=last_seen_lat,
                last_seen_lng=last_seen_lng,
                images=images,
                user_id=owner_id,
                status=status,
                created_at=created_at,
            )
            created_ids.append(sub.id)

    return created_ids


async def seed_comments(db_session, submission_ids: List[int], candidate_user_ids: List[int], target_total: Optional[int] = None) -> int:
    """Seed realistic comments for given submissions, backdating their timestamps."""
    if not submission_ids or not candidate_user_ids:
        return 0

    sub_repo = SubmissionRepository(db_session)
    com_repo = CommentRepository(db_session)

    openings = [
        "I think I saw someone matching this description near",
        "Praying for a safe return. Last week there was a sighting around",
        "Please check hospitals in the area around",
        "Sharing to community groups in",
        "Noticed a person who looked similar at",
        "Spoke to a taxi driver who mentioned seeing someone near",
        "Have you checked with SAPS at",
        "Posting on neighbourhood watch for",
    ]
    places = [
        "the taxi rank",
        "the mall",
        "the train station",
        "the clinic",
        "Main Road",
        "the bus stop",
        "the market",
        "the sports ground",
    ]
    endings = [
        "around sunset yesterday.",
        "this morning at about 8am.",
        "on Friday night.",
        "earlier this week.",
        "over the weekend.",
        "two days ago.",
        "— hope this helps.",
        ", please DM me for more info.",
    ]

    total = 0
    for sub_id in submission_ids:
        sub = await sub_repo.get_by_id(sub_id)
        if not sub:
            continue

        if random.random() < 0.15:
            num_comments = 0
        else:
            num_comments = random.randint(2, 6)

        base_dt: datetime = getattr(sub, "created_at", datetime.now(timezone.utc))
        last_dt = base_dt

        for _ in range(num_comments):
            body = f"{random.choice(openings)} {random.choice(places)} {random.choice(endings)}"
            user_id = random.choice(candidate_user_ids)

            advance_minutes = random.randint(10, 60 * 72)  # up to 3 days after last comment
            created_at = last_dt + timedelta(minutes=advance_minutes)
            now_utc = datetime.now(timezone.utc)
            if created_at > now_utc:
                created_at = now_utc - timedelta(minutes=random.randint(1, 60))

            status = "approved" if random.random() < 0.85 else ("pending" if random.random() < 0.5 else "rejected")
            rejection_reason = None
            if status == "rejected" and random.random() < 0.6:
                rejection_reason = "Off-topic or unverifiable information"

            await com_repo.create(
                submission_id=sub_id,
                user_id=user_id,
                body=body,
                status=status,
                rejection_reason=rejection_reason,
                created_at=created_at,
            )
            total += 1
            last_dt = created_at

    if target_total is not None and total < target_total:
        remaining = target_total - total
        logger.info("Topping up comments by %d to hit target %d", remaining, target_total)
        while remaining > 0:
            sub_id = random.choice(submission_ids)
            sub = await sub_repo.get_by_id(sub_id)
            if not sub:
                continue
            base_dt: datetime = getattr(sub, "created_at", datetime.now(timezone.utc))
            advance_minutes = random.randint(30, 60 * 24 * 30)
            created_at = base_dt + timedelta(minutes=advance_minutes)
            now_utc = datetime.now(timezone.utc)
            if created_at > now_utc:
                created_at = now_utc - timedelta(minutes=random.randint(1, 60))

            body = f"{random.choice(openings)} {random.choice(places)} {random.choice(endings)}"
            user_id = random.choice(candidate_user_ids)
            status = "approved" if random.random() < 0.9 else ("pending" if random.random() < 0.6 else "rejected")
            rejection_reason = None
            if status == "rejected" and random.random() < 0.6:
                rejection_reason = "Off-topic or unverifiable information"

            await com_repo.create(
                submission_id=sub_id,
                user_id=user_id,
                body=body,
                status=status,
                rejection_reason=rejection_reason,
                created_at=created_at,
            )
            total += 1
            remaining -= 1

    return total


async def main() -> None:
    parser = argparse.ArgumentParser(description="Seed test data: users/admins and missing persons")
    parser.add_argument("--admins", type=int, default=12, help="Number of admin users to create (default: 12)")
    parser.add_argument("--users", type=int, default=12, help="Number of normal users to create (default: 12)")
    parser.add_argument("--subs", type=int, default=273, help="Number of missing person submissions to create (default: 200)")
    parser.add_argument("--comments", type=int, default=536, help="Total number of comments to create across submissions (default: 500)")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG","INFO","WARNING","ERROR","CRITICAL"], help="Logging level")
    args = parser.parse_args()

    logging.getLogger().setLevel(getattr(logging, args.log_level))
    logger.info("Seed start: admins=%d users=%d subs=%d comments=%d (log=%s)",
                args.admins, args.users, args.subs, args.comments, args.log_level)

    async with AsyncSessionLocal() as session:
        # Users
        admin_ids, user_ids = await seed_users(session, admins=args.admins, users=args.users)
        await session.commit()
        # Prefer non-admin users for ownership
        candidate_user_ids = user_ids or (admin_ids + user_ids)
        # Submissions
        created_sub_ids = await seed_submissions(session, min_count=args.subs, candidate_user_ids=candidate_user_ids)
        await session.commit()
        # Comments (use normal users as authors; if none, fall back to admins)
        comment_user_ids = user_ids or admin_ids
        created_comments = await seed_comments(session, created_sub_ids, comment_user_ids, target_total=args.comments)
        await session.commit()

    logger.info("Seed complete. Admins:%d Users:%d Submissions:%d Comments:%d",
                len(admin_ids), len(user_ids), len(created_sub_ids), created_comments)


if __name__ == "__main__":
    asyncio.run(main())
