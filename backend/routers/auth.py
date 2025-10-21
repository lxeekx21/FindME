from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from sqlalchemy.ext.asyncio import AsyncSession
from auth.dependencies import get_current_user
from auth.local_auth import (
    hash_password, verify_password, create_access_token, create_refresh_token,
    verify_token, generate_password_reset_token, verify_password_reset_token
)
from database.session import get_db
from repositories.users import UserRepository
from schemas.users import UserDTO, UserUpdateDTO
from schemas.auth import (
    LoginRequest, RegisterRequest, TokenResponse, RefreshTokenRequest,
    PasswordResetRequest, PasswordResetConfirm, ChangePasswordRequest
)
import os
import uuid

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user."""
    repo = UserRepository(db)
    
    # Check if user already exists
    existing_user = await repo.get_by_email(request.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    password_hash = hash_password(request.password)
    user = await repo.create_user(
        email=request.email,
        password_hash=password_hash,
        first_name=request.first_name,
        last_name=request.last_name
    )

    # Assign default role to new user
    default_role = await repo.get_or_create_role("user")
    await repo.add_role(user.id, default_role.id)
    
    await db.commit()
    
    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login with email and password."""
    repo = UserRepository(db)

    # Get user by email
    user = await repo.get_by_email(request.email)
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is disabled"
        )

    # Get user's role
    roles = await repo.get_roles(user.id)
    role_name = roles[0].name if roles else "user"

    # Create tokens with role included
    access_token = create_access_token(data={"sub": str(user.id), "role": role_name})
    refresh_token = create_refresh_token(data={"sub": str(user.id), "role": role_name})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "role": role_name,
        "user_id": user.id
    }

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest):
    """Refresh access token using refresh token."""
    try:
        payload = verify_token(request.refresh_token, "refresh")
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Create new tokens
        access_token = create_access_token(data={"sub": user_id})
        refresh_token = create_refresh_token(data={"sub": user_id})
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.post("/forgot-password")
async def forgot_password(request: PasswordResetRequest, db: AsyncSession = Depends(get_db)):
    """Send password reset email."""
    repo = UserRepository(db)
    user = await repo.get_by_email(request.email)
    
    if user:
        # Generate reset token
        reset_token = generate_password_reset_token(request.email)
        # In a real application, you would send this token via email
        # For now, we'll just return success
        return {"message": "Password reset email sent", "token": reset_token}
    
    # Always return success to prevent email enumeration
    return {"message": "Password reset email sent"}


@router.post("/reset-password")
async def reset_password(request: PasswordResetConfirm, db: AsyncSession = Depends(get_db)):
    """Reset password using reset token."""
    email = verify_password_reset_token(request.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    repo = UserRepository(db)
    user = await repo.get_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found"
        )
    
    # Update password
    password_hash = hash_password(request.new_password)
    await repo.update_user(user.id, password_hash=password_hash)
    await db.commit()
    
    return {"message": "Password reset successfully"}


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: UserDTO = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Change password for authenticated user."""
    repo = UserRepository(db)
    user = await repo.get_by_id(current_user.id)
    
    if not verify_password(request.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    password_hash = hash_password(request.new_password)
    await repo.update_user(user.id, password_hash=password_hash)
    await db.commit()
    
    return {"message": "Password changed successfully"}


@router.get("/me", response_model=UserDTO)
async def me(user: UserDTO = Depends(get_current_user)):
    """Get current user information."""
    return user


@router.patch("/me", response_model=UserDTO)
async def update_me(
    request: UserUpdateDTO,
    current_user: UserDTO = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user's profile (excluding email)."""
    repo = UserRepository(db)

    # Explicitly prevent updates to restricted fields if they sneak in
    update_data = request.dict(exclude_unset=True)
    for forbidden in ("email", "is_active", "password_hash", "roles", "id"):
        update_data.pop(forbidden, None)

    if not update_data:
        # Nothing to update; return current state
        user = await repo.get_by_id(current_user.id)
        await db.refresh(user)
        return user

    user = await repo.update_user(current_user.id, **update_data)
    await db.commit()

    return user


@router.post("/me/profile-image", response_model=UserDTO)
async def upload_profile_image(
    request: Request,
    file: UploadFile = File(...),
    current_user: UserDTO = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload a new profile image for the authenticated user.
    Saves the file under ./files and updates profile_image_url to an absolute URL.
    """
    # Validate content type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only image uploads are allowed")

    # Ensure upload dir exists
    upload_dir = "files"
    os.makedirs(upload_dir, exist_ok=True)

    # Generate a unique filename preserving extension
    _, ext = os.path.splitext(file.filename or "")
    if not ext:
        # Try to infer from content type
        ext = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/gif": ".gif",
            "image/webp": ".webp",
            "image/svg+xml": ".svg",
        }.get(file.content_type, ".img")

    filename = f"user_{current_user.id}_{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(upload_dir, filename)

    # Save file
    try:
        with open(filepath, "wb") as out:
            content = await file.read()
            out.write(content)
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save file")

    # Build absolute URL
    base_url = str(request.base_url).rstrip("/")
    absolute_url = f"{base_url}/files/{filename}"

    # Update user
    repo = UserRepository(db)
    user = await repo.update_user(current_user.id, profile_image_url=absolute_url)
    await db.commit()

    return user
