from fastapi import APIRouter
from backend.auth.service import AuthService, AuthStatus

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/status", response_model=AuthStatus)
async def get_auth_status():
    """Return the current authentication architecture status and OAuth configuration state."""
    return AuthService.get_auth_status()
