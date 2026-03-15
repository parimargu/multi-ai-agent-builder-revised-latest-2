"""
Authentication API routes: register, login, current user.
"""
import logging
import re
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.core.security import hash_password, verify_password, create_access_token
from backend.core.dependencies import get_current_user
from backend.models.user import Tenant, User
from backend.schemas.auth import UserRegister, UserLogin, TokenResponse, UserResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    """Register a new user and create their organization."""
    logger.info("Registration attempt: email=%s, org=%s", data.email, data.organization_name)

    # Check if email already exists
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        logger.warning("Registration failed: email already exists: %s", data.email)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Create tenant
    slug = re.sub(r'[^a-z0-9]+', '-', data.organization_name.lower()).strip('-')
    # Ensure unique slug
    result = await db.execute(select(Tenant).where(Tenant.slug == slug))
    if result.scalar_one_or_none():
        import uuid
        slug = f"{slug}-{str(uuid.uuid4())[:8]}"

    tenant = Tenant(name=data.organization_name, slug=slug)
    db.add(tenant)
    await db.flush()

    # Create user
    user = User(
        tenant_id=tenant.id,
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        role="admin",
    )
    db.add(user)
    await db.flush()

    # Generate token
    token = create_access_token({"sub": str(user.id), "tenant_id": str(tenant.id)})
    logger.info("User registered successfully: id=%s, email=%s", user.id, user.email)

    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    """Authenticate user and return JWT token."""
    logger.info("Login attempt: email=%s", data.email)

    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.hashed_password):
        logger.warning("Login failed for email=%s", data.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    token = create_access_token({"sub": str(user.id), "tenant_id": str(user.tenant_id)})
    logger.info("User logged in: id=%s, email=%s", user.id, user.email)

    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user."""
    return UserResponse.model_validate(current_user)
