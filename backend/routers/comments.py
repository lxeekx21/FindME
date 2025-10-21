from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request
from sqlalchemy.ext.asyncio import AsyncSession
from database.session import get_db
from auth.dependencies import get_current_user, require_roles
from schemas.comments import CommentDTO, CommentCreateDTO, CommentModerateDTO
from schemas.users import UserDTO
from services.comment import CommentService
from repositories.comments import CommentRepository
import os
import uuid

router = APIRouter(prefix="/comments", tags=["comments"])


@router.get("/", response_model=List[CommentDTO])
async def list_comments(submission_id: int, db: AsyncSession = Depends(get_db)):
    service = CommentService(db)
    return await service.list_by_submission_public(submission_id=submission_id)


@router.post("/", response_model=CommentDTO, status_code=status.HTTP_201_CREATED)
async def create_comment(
    request: Request,
    submission_id: int = Form(...),
    body: str = Form(...),
    image: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    user: UserDTO = Depends(get_current_user),
):
    # Only regular authenticated users (not admins) can post public comments
    if any((r.name or '').lower() == 'admin' for r in user.roles):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Admins cannot post public comments')

    # Optional image upload
    image_url: Optional[str] = None
    if image is not None:
        if not image.content_type or not image.content_type.startswith("image/"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only image uploads are allowed")
        upload_dir = os.path.join("files", "comments")
        os.makedirs(upload_dir, exist_ok=True)
        _, ext = os.path.splitext(image.filename or "")
        if not ext:
            ext = {
                "image/jpeg": ".jpg",
                "image/png": ".png",
                "image/gif": ".gif",
                "image/webp": ".webp",
                "image/svg+xml": ".svg",
            }.get(image.content_type, ".img")
        filename = f"c_{user.id}_{uuid.uuid4().hex}{ext}"
        path = os.path.join(upload_dir, filename)
        content = await image.read()
        try:
            with open(path, "wb") as out:
                out.write(content)
        except Exception:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save image")
        base_url = str(request.base_url).rstrip("/")
        image_url = f"{base_url}/files/comments/{filename}"

    # Create comment in pending status
    repo = CommentRepository(db)
    item = await repo.create(
        submission_id=submission_id,
        user_id=user.id,
        body=body,
        image_url=image_url,
        status="pending",
    )
    await db.flush()
    await db.commit()
    # Reload with user eager-loaded to populate author_* properties without async lazy-load
    item = await repo.get_by_id(item.id)
    return CommentDTO.model_validate(item)


@router.get("/mine", response_model=List[CommentDTO])
async def my_comments(db: AsyncSession = Depends(get_db), user: UserDTO = Depends(get_current_user)):
    service = CommentService(db)
    return await service.list_by_user(user_id=user.id)


@router.get("/admin", response_model=List[CommentDTO])
@require_roles("admin")
async def admin_comments(status: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    if status and status not in ("pending", "approved", "rejected"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status")
    service = CommentService(db)
    return await service.list_admin(status=status)


@router.post("/{comment_id}/approve", response_model=CommentDTO)
@require_roles("admin")
async def approve_comment(comment_id: int, db: AsyncSession = Depends(get_db)):
    repo = CommentRepository(db)
    item = await repo.get_by_id(comment_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    item.status = "approved"
    item.rejection_reason = None
    await db.flush()
    await db.commit()
    return CommentDTO.model_validate(item)


@router.post("/{comment_id}/reject", response_model=CommentDTO)
@require_roles("admin")
async def reject_comment(comment_id: int, data: CommentModerateDTO, db: AsyncSession = Depends(get_db)):
    repo = CommentRepository(db)
    item = await repo.get_by_id(comment_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    item.status = "rejected"
    item.rejection_reason = data.reason
    await db.flush()
    await db.commit()
    return CommentDTO.model_validate(item)
