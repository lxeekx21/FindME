from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Optional, List
from app.entities.comment import Comment


class CommentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: int) -> Optional[Comment]:
        res = await self.session.execute(
            select(Comment).options(selectinload(Comment.user)).where(Comment.id == id)
        )
        return res.scalar_one_or_none()

    async def create(self, **kwargs) -> Comment:
        item = Comment(**kwargs)
        self.session.add(item)
        await self.session.flush()
        return item

    async def list_by_submission(self, submission_id: int, status: Optional[str] = None) -> List[Comment]:
        stmt = select(Comment).options(selectinload(Comment.user)).where(Comment.submission_id == submission_id)
        if status:
            stmt = stmt.where(Comment.status == status)
        res = await self.session.execute(stmt.order_by(Comment.created_at.desc()))
        return list(res.scalars().all())

    async def list_by_user(self, user_id: int) -> List[Comment]:
        res = await self.session.execute(
            select(Comment).options(selectinload(Comment.user)).where(Comment.user_id == user_id).order_by(Comment.created_at.desc())
        )
        return list(res.scalars().all())

    async def list_admin(self, status: Optional[str] = None) -> List[Comment]:
        stmt = select(Comment).options(selectinload(Comment.user))
        if status:
            stmt = stmt.where(Comment.status == status)
        res = await self.session.execute(stmt.order_by(Comment.created_at.desc()))
        return list(res.scalars().all())
