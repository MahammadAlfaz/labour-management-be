from fastapi import Cookie, Depends

from app.core.errors import ForbiddenError, UnauthorizedError
from app.core.security import TokenError, decode_token
from app.modules.admins.repository import AdminRepository
from app.modules.admins.schemas import AdminOut


def get_admin_repository() -> AdminRepository:
    return AdminRepository()


async def get_current_admin(
    access_token: str | None = Cookie(default=None),
    admin_repo: AdminRepository = Depends(get_admin_repository),
) -> AdminOut:
    """Resolve the authenticated admin from the access-token cookie.

    Re-fetches the admin record on every request (rather than trusting the
    JWT payload alone) so a deactivation takes effect immediately instead of
    waiting for the token to expire.
    """
    if not access_token:
        raise UnauthorizedError("Not authenticated")

    try:
        payload = decode_token(access_token, expected_type="access")
    except TokenError as exc:
        raise UnauthorizedError(str(exc)) from exc

    admin = await admin_repo.get_by_id(payload["sub"])
    if admin is None:
        raise UnauthorizedError("Admin not found")
    if not admin.is_active:
        raise ForbiddenError("Admin account is deactivated")

    return admin
