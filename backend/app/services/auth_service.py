"""Authentication business logic: register, login, token issuance and refresh."""

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User
from app.schemas.auth import TokenResponse, UserResponse

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------
SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS


def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "exp": expire,
        "type": "access",
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": user_id,
        "exp": expire,
        "type": "refresh",
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token. Raises JWTError if invalid."""
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


def create_token_response(user: User) -> TokenResponse:
    """Build a TokenResponse from a User ORM instance."""
    user_id_str = str(user.id)
    return TokenResponse(
        access_token=create_access_token(user_id_str),
        refresh_token=create_refresh_token(user_id_str),
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


# ---------------------------------------------------------------------------
# Auth service: register / login / refresh
# ---------------------------------------------------------------------------
class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(
        self, email: str, password: str, display_name: str
    ) -> TokenResponse:
        # Check for duplicate email
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            raise HTTPException(status_code=409, detail="Email already registered")

        # Create user
        user = User(
            id=uuid.uuid4(),
            email=email,
            password_hash=hash_password(password),
            display_name=display_name,
            email_verified=False,
        )
        self.db.add(user)
        await self.db.flush()

        return create_token_response(user)

    async def login(self, email: str, password: str) -> TokenResponse:
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()

        if user is None or user.password_hash is None:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        if not verify_password(password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        return create_token_response(user)

    async def refresh(self, refresh_token: str) -> TokenResponse:
        # Decode and validate the refresh token
        try:
            payload = decode_token(refresh_token)
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Token is not a refresh token")

        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        # Fetch the user to ensure they still exist
        user = await self.get_user_by_id(user_id)
        return create_token_response(user)

    async def get_user_by_id(self, user_id: str) -> User:
        result = await self.db.execute(
            select(User).where(User.id == uuid.UUID(user_id))
        )
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
