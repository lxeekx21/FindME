from sqlalchemy import Column, Integer, String, DateTime, func, Date, Enum, Boolean
from sqlalchemy.orm import relationship
from .base import Base


class User(Base):
    id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    phone = Column(String(15), nullable=True, index=True)
    profile_image_url = Column(String(1024), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    gender = Column(Enum('male', 'female', name='gender_enum'), nullable=True)
    dob = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Use async-friendly eager loading to avoid MissingGreenlet during Pydantic serialization
    roles = relationship("Role", secondary="user_roles", backref="users", lazy="selectin")
