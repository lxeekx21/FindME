from sqlalchemy import Column, Integer, Text, DateTime, func, ForeignKey, Enum, String
from sqlalchemy.orm import relationship
from .base import Base


class Comment(Base):
    id = Column(Integer, primary_key=True)
    submission_id = Column(Integer, ForeignKey("submission.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="SET NULL"), nullable=True)

    body = Column(Text, nullable=False)
    image_url = Column(String(1024), nullable=True)

    status = Column(Enum("pending", "approved", "rejected", name="comment_status_enum"), nullable=False, server_default="pending")
    rejection_reason = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # relationships
    submission = relationship("Submission", backref="comments")
    user = relationship("User", backref="comments")

    # Denormalized convenience props for API serialization
    @property
    def author_name(self):
        if not self.user:
            return None
        first = getattr(self.user, "first_name", None) or ""
        last = getattr(self.user, "last_name", None) or ""
        full = (first + " " + last).strip()
        return full or getattr(self.user, "email", None)

    @property
    def author_profile_image_url(self):
        return getattr(self.user, "profile_image_url", None)
