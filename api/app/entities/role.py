from sqlalchemy import Column, Integer, String, UniqueConstraint
from .base import Base


class Role(Base):
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)

    __table_args__ = (
        UniqueConstraint("name", name="uq_roles_name"),
    )
