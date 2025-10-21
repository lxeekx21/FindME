from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.repositories.submissions import SubmissionRepository
from app.core.cache import ttl_cache
from app.models.submission_models import (
    SubmissionDTO,
    SubmissionCreateDTO,
    SubmissionUpdateDTO,
    SubmissionSummaryDTO,
)


class SubmissionService:
    def __init__(self, session: AsyncSession):
        self.repo = SubmissionRepository(session)

    async def get(self, id: int) -> Optional[SubmissionDTO]:
        sub = await self.repo.get_by_id(id)
        return SubmissionDTO.model_validate(sub) if sub else None

    async def list(self, limit: int = 1000, offset: int = 0) -> List[SubmissionDTO]:
        # Cap limit to 1000 to prevent excessive payloads
        safe_limit = max(0, min(limit, 1000))
        items = await self.repo.list(limit=safe_limit, offset=offset)
        return [SubmissionDTO.model_validate(x) for x in items]

    async def list_by_user(self, user_id: int, limit: int = 1000, offset: int = 0) -> List[SubmissionDTO]:
        # Cap limit to 1000 to prevent excessive payloads
        safe_limit = max(0, min(limit, 1000))
        items = await self.repo.list_by_user(user_id=user_id, limit=safe_limit, offset=offset)
        return [SubmissionDTO.model_validate(x) for x in items]

    async def create(self, data: SubmissionCreateDTO, user_id: Optional[int], images: Optional[List[str]] = None) -> SubmissionDTO:
        payload: Dict[str, Any] = {
            "title": data.title,
            "full_name": data.full_name,
            "dob": data.dob,
            "gender": data.gender,
            "race": data.race,
            "height": data.height,
            "weight": data.weight,
            "province": data.province,
            "description": data.description,
            "status": "pending",
            "last_seen_address": data.last_seen_address,
            "last_seen_place_id": data.last_seen_place_id,
            "last_seen_lat": data.last_seen_lat,
            "last_seen_lng": data.last_seen_lng,
            "images": images or [],
            "user_id": user_id,
        }
        sub = await self.repo.create(**payload)
        return SubmissionDTO.model_validate(sub)

    async def update(self, id: int, data: SubmissionUpdateDTO) -> Optional[SubmissionDTO]:
        sub = await self.repo.update(
            id,
            title=data.title,
            full_name=data.full_name,
            dob=data.dob,
            gender=data.gender,
            race=data.race,
            height=data.height,
            weight=data.weight,
            province=data.province,
            description=data.description,
            status=data.status,
            last_seen_address=data.last_seen_address,
            last_seen_place_id=data.last_seen_place_id,
            last_seen_lat=data.last_seen_lat,
            last_seen_lng=data.last_seen_lng,
            images=data.images,
        )
        return SubmissionDTO.model_validate(sub) if sub else None

    async def delete(self, id: int) -> bool:
        return await self.repo.delete(id)

    @ttl_cache(ttl_seconds=60)
    async def summarize(self) -> SubmissionSummaryDTO:
        result = await self.repo.summarize()
        return SubmissionSummaryDTO.from_dict(result)
