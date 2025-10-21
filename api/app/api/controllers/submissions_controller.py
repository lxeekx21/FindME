from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.auth.dependencies import get_current_user, require_roles
from app.models.submission_models import (
    SubmissionDTO,
    SubmissionCreateDTO,
    SubmissionUpdateDTO,
    SubmissionSummaryDTO,
)
from app.services.submission_service import SubmissionService
from app.models.user_models import UserDTO
from app.services.age_progression_service import generate_age_progression
import os
import uuid
from datetime import date

router = APIRouter(prefix="/submissions", tags=["submissions"])


@router.get("/", response_model=List[SubmissionDTO])
async def list_submissions(
    db: AsyncSession = Depends(get_db),
    page: int = 1,
    limit: int = 100,
):
    # Normalize and cap pagination params
    page = max(1, page)
    limit = max(1, min(limit, 1000))
    offset = (page - 1) * limit
    service = SubmissionService(db)
    return await service.list(limit=limit, offset=offset)


@router.get("/mine", response_model=List[SubmissionDTO])
async def list_my_submissions(
    db: AsyncSession = Depends(get_db),
    user: UserDTO = Depends(get_current_user),
    page: int = 1,
    limit: int = 100,
):
    page = max(1, page)
    limit = max(1, min(limit, 1000))
    offset = (page - 1) * limit
    service = SubmissionService(db)
    return await service.list_by_user(user_id=user.id, limit=limit, offset=offset)


@router.get("/summary", response_model=SubmissionSummaryDTO)
@require_roles("admin")
async def submissions_summary(
    db: AsyncSession = Depends(get_db),
):
    service = SubmissionService(db)
    return await service.summarize()


@router.get("/{submission_id}", response_model=SubmissionDTO)
async def get_submission(submission_id: int, db: AsyncSession = Depends(get_db)):
    service = SubmissionService(db)
    item = await service.get(submission_id)
    if not item or (item.status not in ("published", "found_alive", "found_dead")):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return item


@router.get("/{submission_id}/age-progression")
async def age_progression(submission_id: int, request: Request, years: Optional[int] = None, db: AsyncSession = Depends(get_db)):
    service = SubmissionService(db)
    item = await service.get(submission_id)
    if not item or (item.status not in ("published", "found_alive", "found_dead")):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    if not item.images:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No images available for this submission")
    # Use first image as the primary source
    source_url = item.images[0]
    base_url = str(request.base_url).rstrip("/")

    # Compute years since missing (based on created_at), and target age if DOB provided
    from datetime import datetime
    created_at = None
    try:
        created_at = datetime.fromisoformat(str(item.created_at).replace("Z", "+00:00"))
    except Exception:
        created_at = None
    now = datetime.utcnow()
    years_since_missing = years if years is not None else 0
    if created_at:
        # Rough diff in whole years
        years_since_missing = max(0, now.year - created_at.year - ((now.month, now.day) < (created_at.month, created_at.day)))
    # Derive source age at missing and target age now
    target_age: Optional[int] = None
    if getattr(item, 'dob', None):
        try:
            dob_dt = datetime.fromisoformat(str(item.dob))
            source_age = created_at.year - dob_dt.year - ((created_at.month, created_at.day) < (dob_dt.month, dob_dt.day)) if created_at else None
            if source_age is not None:
                target_age = max(0, source_age + years_since_missing)
        except Exception:
            target_age = None

    url = await generate_age_progression(
        submission_id=submission_id,
        source_image_url=source_url,
        years=years_since_missing or 1,
        base_url=base_url,
        target_age=target_age,
    )
    if not url:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Age progression failed")
    return {"url": url}


@router.post("/", response_model=SubmissionDTO, status_code=status.HTTP_201_CREATED)
async def create_submission(
    request: Request,
    title: str = Form(...),
    full_name: str = Form(...),
    dob: Optional[str] = Form(None),
    gender: Optional[str] = Form(None),
    race: Optional[str] = Form(None),
    height: Optional[float] = Form(None),
    weight: Optional[float] = Form(None),
    province: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    last_seen_address: Optional[str] = Form(None),
    last_seen_place_id: Optional[str] = Form(None),
    last_seen_lat: Optional[float] = Form(None),
    last_seen_lng: Optional[float] = Form(None),
    images: list[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    user: UserDTO = Depends(get_current_user),
):
    if not images or len(images) < 3:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least 3 images are required")

    # Save images
    upload_dir = os.path.join("files", "submissions")
    os.makedirs(upload_dir, exist_ok=True)
    # Build base URL for absolute links
    base_url = str(request.base_url).rstrip("/")
    image_urls: list[str] = []

    for file in images:
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only image uploads are allowed")
        _, ext = os.path.splitext(file.filename or "")
        if not ext:
            # Infer extension from content type
            ext = {
                "image/jpeg": ".jpg",
                "image/png": ".png",
                "image/gif": ".gif",
                "image/webp": ".webp",
                "image/svg+xml": ".svg",
            }.get(file.content_type, ".img")
        filename = f"sub_{user.id}_{uuid.uuid4().hex}{ext}"
        path = os.path.join(upload_dir, filename)
        # Save
        content = await file.read()
        try:
            with open(path, "wb") as out:
                out.write(content)
        except Exception:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save files")
        image_urls.append(f"{base_url}/files/submissions/{filename}")

    # Create payload and persist
    service = SubmissionService(db)
    dto = SubmissionCreateDTO(
        title=title,
        full_name=full_name,
        dob=dob,
        gender=gender,
        race=race,
        height=height,
        weight=weight,
        province=province,
        description=description,
        last_seen_address=last_seen_address,
        last_seen_place_id=last_seen_place_id,
        last_seen_lat=last_seen_lat,
        last_seen_lng=last_seen_lng,
    )
    result = await service.create(dto, user_id=user.id, images=image_urls)
    await db.commit()
    return result


# Also accept POST without trailing slash to avoid redirect/CORS issues when clients post to '/submissions'
router.add_api_route(
    "",  # prefix is '/submissions'
    create_submission,
    methods=["POST"],
    response_model=SubmissionDTO,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)

# Accept GET without trailing slash as well (serve list at '/submissions') to avoid 405/redirect issues
router.add_api_route(
    "",  # prefix is '/submissions'
    list_submissions,
    methods=["GET"],
    response_model=List[SubmissionDTO],
    include_in_schema=False,
)


@router.put("/{submission_id}", response_model=SubmissionDTO)
async def update_submission(
    submission_id: int,
    data: SubmissionUpdateDTO,
    db: AsyncSession = Depends(get_db),
    user: UserDTO = Depends(get_current_user),
):
    service = SubmissionService(db)
    existing = await service.get(submission_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    user_roles = {r.name for r in user.roles}
    if existing.user_id != user.id and "admin" not in user_roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    updated = await service.update(submission_id, data)
    await db.commit()
    return updated


@router.delete("/{submission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_submission(
    submission_id: int,
    db: AsyncSession = Depends(get_db),
    user: UserDTO = Depends(get_current_user),
):
    service = SubmissionService(db)
    existing = await service.get(submission_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    user_roles = {r.name for r in user.roles}
    if existing.user_id != user.id and "admin" not in user_roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    ok = await service.delete(submission_id)
    await db.commit()
    return None


