from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr
from backend.database.connection import get_db_connection
from backend.config import settings


class User(BaseModel):
    id: int
    email: EmailStr
    name: str
    provider: str = "google"
    provider_user_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class UserCreate(BaseModel):
    email: EmailStr
    name: str
    provider: str = "google"
    provider_user_id: str


class AuthStatus(BaseModel):
    authenticated: bool = False
    user: Optional[User] = None
    oauth_configured: bool = False
    message: str = "Authentication foundation initialized. OAuth pending configuration."


class AuthService:
    """Authentication service foundation supporting future OAuth integration."""

    @staticmethod
    def is_oauth_configured() -> bool:
        """Check if OAuth credentials have been provided via environment variables."""
        return bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET)

    @staticmethod
    def get_auth_status(current_user: Optional[User] = None) -> AuthStatus:
        """Retrieve current session authentication and configuration status."""
        configured = AuthService.is_oauth_configured()
        if current_user:
            return AuthStatus(
                authenticated=True,
                user=current_user,
                oauth_configured=configured,
                message="User is authenticated.",
            )
        return AuthStatus(
            authenticated=False,
            user=None,
            oauth_configured=configured,
            message="No active session. Google OAuth configuration pending." if not configured else "No active session.",
        )

    @staticmethod
    def get_user_by_email(email: str) -> Optional[User]:
        """Fetch user record from database by email."""
        with get_db_connection() as conn:
            row = conn.execute(
                "SELECT id, email, name, provider, provider_user_id, created_at, updated_at FROM users WHERE email = ?",
                (email,),
            ).fetchone()
            if row:
                return User(**dict(row))
        return None

    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[User]:
        """Fetch user record from database by primary key."""
        with get_db_connection() as conn:
            row = conn.execute(
                "SELECT id, email, name, provider, provider_user_id, created_at, updated_at FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
            if row:
                return User(**dict(row))
        return None

    @staticmethod
    def create_user(user_in: UserCreate) -> User:
        """Insert a new user record into the database."""
        with get_db_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO users (email, name, provider, provider_user_id)
                VALUES (?, ?, ?, ?)
                """,
                (user_in.email, user_in.name, user_in.provider, user_in.provider_user_id),
            )
            user_id = cursor.lastrowid

        user = AuthService.get_user_by_id(user_id)
        if not user:
            raise RuntimeError("Failed to retrieve created user record.")
        return user
