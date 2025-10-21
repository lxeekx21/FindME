from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from database.session import get_db
from auth.dependencies import require_roles
from repositories.users import UserRepository
from schemas.users import UserDTO, RoleDTO, AdminUserUpdateDTO

router = APIRouter(prefix="/admin", tags=["admin"])  # role check via decorator per-call


@router.get("/users", response_model=List[UserDTO])
@require_roles("admin")
async def list_users(
    db: AsyncSession = Depends(get_db),
):
    repo = UserRepository(db)
    users = await repo.list_users()
    return [UserDTO.model_validate(u) for u in users]


@router.get("/roles", response_model=List[RoleDTO])
@require_roles("admin")
async def list_roles(
    db: AsyncSession = Depends(get_db),
):
    repo = UserRepository(db)
    roles = await repo.list_roles()
    return [RoleDTO.model_validate(r) for r in roles]


@router.patch("/users/{user_id}", response_model=UserDTO)
@require_roles("admin")
async def admin_update_user(
    user_id: int,
    request: AdminUserUpdateDTO,
    db: AsyncSession = Depends(get_db),
):
    """Admin updates user status and role.

    - is_active -> updates User.is_active
    - is_admin -> assigns 'admin' role when true, 'user' role when false
    """
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    payload = request.dict(exclude_unset=True)

    # 1) Update activation status if provided
    if "is_active" in payload:
        await repo.update_user(user_id, is_active=bool(payload["is_active"]))

    # 2) Update role if provided
    if "is_admin" in payload:
        role_name = "admin" if payload["is_admin"] else "user"
        role = await repo.get_or_create_role(role_name)
        await repo.add_role(user_id, role.id)

    await db.commit()

    # Return the updated user with roles
    updated = await repo.get_by_id(user_id)
    return UserDTO.model_validate(updated)


class SetRoleRequest(BaseModel):
    role_name: str


@router.put("/users/{user_id}/role", response_model=UserDTO)
@require_roles("admin")
async def set_user_role(
    user_id: int,
    body: SetRoleRequest,
    db: AsyncSession = Depends(get_db),
):
    """Assign a single role to a user (replaces existing roles)."""
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    role = await repo.get_or_create_role(body.role_name)
    await repo.add_role(user_id, role.id)
    await db.commit()

    # Return the updated user with roles
    updated = await repo.get_by_id(user_id)
    return UserDTO.model_validate(updated)
