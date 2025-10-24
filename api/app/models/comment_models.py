from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CommentDTO(BaseModel):
    id: int
    submission_id: int
    user_id: Optional[int] = None
    body: str
    image_url: Optional[str] = None
    status: str
    rejection_reason: Optional[str] = None
    created_at: datetime
    # Denormalized author info for display
    author_name: Optional[str] = None
    author_profile_image_url: Optional[str] = None

    class Config:
        from_attributes = True


class CommentCreateDTO(BaseModel):
    submission_id: int
    body: str = Field(min_length=1)
    # image handled as upload in controller


class CommentModerateDTO(BaseModel):
    reason: Optional[str] = None


class CommentListDTO(BaseModel):
    items: List[CommentDTO]
