from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from .base import Base


class UserRole(Base):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    role_id = Column(Integer, ForeignKey("role.id", ondelete="CASCADE"), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uq_user_roles_user_role"),
        UniqueConstraint("user_id", name="uq_user_roles_user"),
    )

    # bridge table name
    __tablename__ = "user_roles"
