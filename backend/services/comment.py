from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from repositories.comments import CommentRepository
from schemas.comments import CommentDTO


class CommentService:
    def __init__(self, session: AsyncSession):
        self.repo = CommentRepository(session)

    async def get(self, id: int) -> Optional[CommentDTO]:
        item = await self.repo.get_by_id(id)
        return CommentDTO.model_validate(item) if item else None

    async def list_by_submission_public(self, submission_id: int) -> List[CommentDTO]:
        items = await self.repo.list_by_submission(submission_id=submission_id, status="approved")
        return [CommentDTO.model_validate(x) for x in items]

    async def list_by_submission_all(self, submission_id: int) -> List[CommentDTO]:
        items = await self.repo.list_by_submission(submission_id=submission_id)
        return [CommentDTO.model_validate(x) for x in items]

    async def list_by_user(self, user_id: int) -> List[CommentDTO]:
        items = await self.repo.list_by_user(user_id=user_id)
        return [CommentDTO.model_validate(x) for x in items]

    async def list_admin(self, status: Optional[str]) -> List[CommentDTO]:
        items = await self.repo.list_admin(status=status)
        return [CommentDTO.model_validate(x) for x in items]
