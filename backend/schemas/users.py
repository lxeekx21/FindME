from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime


class RoleDTO(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class UserDTO(BaseModel):
    id: int
    email: str
    is_active: bool
    phone: Optional[str] = None
    profile_image_url: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    dob: Optional[date] = None
    gender: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    roles: List[RoleDTO] = Field(default_factory=list)

    class Config:
        from_attributes = True


class UserCreateDTO(BaseModel):
    email: str
    password: str
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    dob: Optional[date] = None
    gender: Optional[str] = None


class UserUpdateDTO(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    dob: Optional[date] = None
    gender: Optional[str] = None
    profile_image_url: Optional[str] = None
    phone: Optional[str] = None


class AdminUserUpdateDTO(BaseModel):
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
