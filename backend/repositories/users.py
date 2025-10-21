from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.future import select
from typing import Optional, List
from models.user_model import User
from models.role_model import Role
from models.user_role_model import UserRole


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_roles(self, user_id: int):
        result = await self.session.execute(
            select(Role).join(UserRole).where(UserRole.user_id == user_id)
        )
        return result.scalars().all()

    async def get_by_id(self, user_id: int) -> Optional[User]:
        res = await self.session.execute(
            select(User).options(selectinload(User.roles)).where(User.id == user_id)
        )
        return res.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        res = await self.session.execute(
            select(User).options(selectinload(User.roles)).where(User.email == email)
        )
        return res.scalar_one_or_none()

    async def create_user(self, email: str, password_hash: str, first_name: Optional[str] = None, last_name: Optional[str] = None) -> User:
        user = User(
            email=email,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name
        )
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        user = await self.get_by_id(user_id)
        if user:
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            await self.session.flush()
            await self.session.refresh(user)
        return user

    async def list_users(self, limit: int = 100, offset: int = 0) -> List[User]:
        res = await self.session.execute(
            select(User).options(selectinload(User.roles)).limit(limit).offset(offset)
        )
        return list(res.scalars().all())

    async def list_roles(self) -> List[Role]:
        res = await self.session.execute(select(Role))
        return list(res.scalars().all())

    async def get_role_by_name(self, name: str) -> Optional[Role]:
        res = await self.session.execute(select(Role).where(Role.name == name))
        return res.scalar_one_or_none()

    async def get_or_create_role(self, name: str) -> Role:
        role = await self.get_role_by_name(name)
        if role is None:
            role = Role(name=name)
            self.session.add(role)
            await self.session.flush()
            await self.session.refresh(role)
        return role

    async def add_role(self, user_id: int, role_id: int) -> None:
        # Enforce single role per user: remove any existing role mappings first
        await self.session.execute(
            delete(UserRole).where(UserRole.user_id == user_id)
        )
        # Now add the new role mapping
        self.session.add(UserRole(user_id=user_id, role_id=role_id))

    async def remove_role(self, user_id: int, role_id: int) -> None:
        res = await self.session.execute(
            select(UserRole).where(UserRole.user_id == user_id, UserRole.role_id == role_id)
        )
        ur = res.scalar_one_or_none()
        if ur:
            await self.session.delete(ur)
