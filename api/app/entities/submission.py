from sqlalchemy import Column, Integer, String, Text, DateTime, func, ForeignKey, Enum, Float, Date
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB  # type: ignore
from sqlalchemy.orm import relationship
from .base import Base
import os

# Use a portable JSON type depending on backend (SQLite vs Postgres)
JSONType = PG_JSONB if os.getenv("DB_DRIVER", "sqlite").startswith("postgres") else SQLITE_JSON


class Submission(Base):
    id = Column(Integer, primary_key=True)
    # Legacy fields (kept for compatibility)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)

    # Missing person fields
    full_name = Column(String(255), nullable=False)
    dob = Column(Date, nullable=True)
    gender = Column(Enum("male", "female", name="mp_gender_enum"), nullable=True)
    race = Column(Enum("black_african", "coloured", "white", "asian_or_indian", "other", name="race_enum"), nullable=True)
    height = Column(Float, nullable=True)
    weight = Column(Float, nullable=True)
    province = Column(Enum(
        "eastern_cape",
        "free_state",
        "gauteng",
        "kwazulu_natal",
        "limpopo",
        "mpumalanga",
        "north_west",
        "northern_cape",
        "western_cape",
        name="province_enum",
    ), nullable=True)
    description = Column(Text, nullable=True)

    # Status lifecycle
    status = Column(Enum("pending", "published", "rejected", "found_alive", "found_dead", name="submission_status_enum"), nullable=False, server_default="pending")

    # Last seen location
    last_seen_address = Column(String(512), nullable=True)
    last_seen_place_id = Column(String(128), nullable=True)
    last_seen_lat = Column(Float, nullable=True)
    last_seen_lng = Column(Float, nullable=True)

    # Images (array of URLs)
    images = Column(JSONType, nullable=True)

    user_id = Column(Integer, ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", backref="submissions")
