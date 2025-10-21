from pydantic import BaseModel, Field
from typing import Optional, Any, Dict, List
from datetime import datetime, date


class SubmissionDTO(BaseModel):
    id: int
    title: str
    full_name: str
    dob: Optional[date] = None
    gender: Optional[str] = None
    race: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    province: Optional[str] = None
    description: Optional[str] = None
    status: str
    last_seen_address: Optional[str] = None
    last_seen_place_id: Optional[str] = None
    last_seen_lat: Optional[float] = None
    last_seen_lng: Optional[float] = None
    images: Optional[List[str]] = None
    user_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class SubmissionCreateDTO(BaseModel):
    title: str
    full_name: str
    dob: Optional[date] = None
    gender: Optional[str] = Field(default=None)
    race: Optional[str] = None
    height: Optional[float] = Field(default=None, ge=0)
    weight: Optional[float] = Field(default=None, ge=0)
    province: Optional[str] = None
    description: Optional[str] = None
    last_seen_address: Optional[str] = None
    last_seen_place_id: Optional[str] = None
    last_seen_lat: Optional[float] = None
    last_seen_lng: Optional[float] = None
    # images are handled via file upload in the controller


class SubmissionUpdateDTO(BaseModel):
    title: Optional[str] = None
    full_name: Optional[str] = None
    dob: Optional[date] = None
    gender: Optional[str] = None
    race: Optional[str] = None
    height: Optional[float] = Field(default=None, ge=0)
    weight: Optional[float] = Field(default=None, ge=0)
    province: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    last_seen_address: Optional[str] = None
    last_seen_place_id: Optional[str] = None
    last_seen_lat: Optional[float] = None
    last_seen_lng: Optional[float] = None
    images: Optional[List[str]] = None


class SubmissionSummaryDTO(BaseModel):
    total_submissions: int
    status_counts: Dict[str, int] | None = None
    province_counts: Dict[str, int] | None = None
    gender_counts: Dict[str, int] | None = None
    race_counts: Dict[str, int] | None = None
    monthly_new: List[Dict[str, Any]] | None = None  # [{month: 'YYYY-MM', count: n}]
    public_counts: Dict[str, int] | None = None  # { public: n, non_public: n }
    found_rate: float | None = None
    found_alive_count: int | None = None
    found_dead_count: int | None = None
    avg_images_per_submission: float | None = None
    users_total: int | None = None
    admins_total: int | None = None
    active_users: int | None = None
    inactive_users: int | None = None
    top_submitters: List[Dict[str, Any]] | None = None  # [{user_id: x, count: n}]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(**data)
