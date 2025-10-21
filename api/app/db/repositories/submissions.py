from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List, Dict, Any, Tuple
from app.entities.submission import Submission
from app.entities.user import User
from app.entities.role import Role
from app.entities.user_role import UserRole
import os
from collections import defaultdict
from datetime import datetime


class SubmissionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: int) -> Optional[Submission]:
        res = await self.session.execute(select(Submission).where(Submission.id == id))
        return res.scalar_one_or_none()

    async def list(self, limit: int = 1000, offset: int = 0) -> List[Submission]:
        # Cap limit to 1000 and apply deterministic ordering (newest first)
        safe_limit = max(0, min(limit, 1000))
        res = await self.session.execute(
            select(Submission).order_by(Submission.created_at.desc()).limit(safe_limit).offset(offset)
        )
        return list(res.scalars().all())

    async def list_by_user(self, user_id: int, limit: int = 1000, offset: int = 0) -> List[Submission]:
        # Cap limit to 1000 and apply deterministic ordering (newest first)
        safe_limit = max(0, min(limit, 1000))
        res = await self.session.execute(
            select(Submission).where(Submission.user_id == user_id).order_by(Submission.created_at.desc()).limit(safe_limit).offset(offset)
        )
        return list(res.scalars().all())

    async def create(self, **kwargs) -> Submission:
        sub = Submission(**kwargs)
        self.session.add(sub)
        await self.session.flush()
        return sub

    async def update(self, id: int, **kwargs) -> Optional[Submission]:
        sub = await self.get_by_id(id)
        if not sub:
            return None
        for k, v in kwargs.items():
            if hasattr(sub, k) and v is not None:
                setattr(sub, k, v)
        return sub

    async def delete(self, id: int) -> bool:
        sub = await self.get_by_id(id)
        if not sub:
            return False
        await self.session.delete(sub)
        return True

    async def summarize(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {}

        # Total submissions
        res = await self.session.execute(select(func.count(Submission.id)))
        total = int(res.scalar() or 0)
        result["total_submissions"] = total

        # Counts by status
        res = await self.session.execute(
            select(Submission.status, func.count(Submission.id)).group_by(Submission.status)
        )
        status_counts = {str(k): int(v) for k, v in res.all()}
        result["status_counts"] = status_counts

        # Counts by province
        res = await self.session.execute(
            select(Submission.province, func.count(Submission.id)).group_by(Submission.province)
        )
        province_counts = {str(k): int(v) for k, v in res.all() if k is not None}
        result["province_counts"] = province_counts

        # Counts by gender
        res = await self.session.execute(
            select(Submission.gender, func.count(Submission.id)).group_by(Submission.gender)
        )
        gender_counts = {str(k): int(v) for k, v in res.all() if k is not None}
        result["gender_counts"] = gender_counts

        # Counts by race
        res = await self.session.execute(
            select(Submission.race, func.count(Submission.id)).group_by(Submission.race)
        )
        race_counts = {str(k): int(v) for k, v in res.all() if k is not None}
        result["race_counts"] = race_counts

        # Public vs non-public
        public_status = ("published", "found_alive", "found_dead")
        res = await self.session.execute(
            select(func.count(Submission.id)).where(Submission.status.in_(public_status))
        )
        public_count = int(res.scalar() or 0)
        non_public = max(0, total - public_count)
        result["public_counts"] = {"public": public_count, "non_public": non_public}

        # Found rate (both alive and dead)
        found_alive = int(status_counts.get("found_alive", 0))
        found_dead = int(status_counts.get("found_dead", 0))
        found_total = found_alive + found_dead
        result["found_rate"] = (found_total / total) if total > 0 else 0.0
        # Breakdown counts
        result["found_alive_count"] = found_alive
        result["found_dead_count"] = found_dead

        # Average images per submission
        res = await self.session.execute(select(Submission.images))
        images_lists = [row[0] for row in res.all()]
        img_total = 0
        items = 0
        for imgs in images_lists:
            if imgs is None:
                continue
            try:
                img_total += len(imgs)
            except Exception:
                # some backends may return text; ignore
                pass
            items += 1
        result["avg_images_per_submission"] = (img_total / items) if items > 0 else 0.0

        # Monthly new (last 12 months) using Python aggregation for portability
        res = await self.session.execute(select(Submission.created_at))
        months: Dict[str, int] = defaultdict(int)
        for (dt,) in res.all():
            if isinstance(dt, datetime):
                key = dt.strftime("%Y-%m")
                months[key] += 1
        # Build a sorted last 12 months timeline including zeros
        now = datetime.utcnow()
        timeline = []
        for i in range(11, -1, -1):
            y = (now.year if now.month - i > 0 else now.year - 1)
            m = ((now.month - i - 1) % 12) + 1
            key = f"{y:04d}-{m:02d}"
            timeline.append({"month": key, "count": int(months.get(key, 0))})
        result["monthly_new"] = timeline

        # User stats
        # Total users and active/inactive
        res = await self.session.execute(select(func.count(User.id)))
        result["users_total"] = int(res.scalar() or 0)
        res = await self.session.execute(select(func.count(User.id)).where(User.is_active == True))  # noqa: E712
        active = int(res.scalar() or 0)
        result["active_users"] = active
        result["inactive_users"] = max(0, result["users_total"] - active)
        # Admins
        # count users having role 'admin'
        res = await self.session.execute(
            select(func.count(User.id))
            .select_from(User)
            .join(UserRole, UserRole.user_id == User.id, isouter=True)
            .join(Role, Role.id == UserRole.role_id, isouter=True)
            .where(Role.name == "admin")
        )
        result["admins_total"] = int(res.scalar() or 0)

        # Top submitters (by number of submissions)
        res = await self.session.execute(
            select(Submission.user_id, func.count(Submission.id).label("cnt"))
            .group_by(Submission.user_id)
            .order_by(func.count(Submission.id).desc())
            .limit(5)
        )
        top = []
        for uid, cnt in res.all():
            if uid is None:
                continue
            top.append({"user_id": int(uid), "count": int(cnt)})
        result["top_submitters"] = top

        return result
