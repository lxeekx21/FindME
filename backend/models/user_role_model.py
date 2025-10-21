from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from .base import Base
from models.user_model import User
from models.role_model import Role

class UserRole(Base):
    __tablename__ = "user_roles"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    role_id = Column(Integer, ForeignKey("role.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    user = relationship("User", back_populates="roles")
    role = relationship("Role")

    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uq_user_roles_user_role"),
        UniqueConstraint("user_id", name="uq_user_roles_user"),
    )