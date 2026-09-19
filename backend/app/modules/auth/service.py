import logging

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from pymongo.errors import DuplicateKeyError

from app.config import get_settings
from app.core.errors import ConflictError, ForbiddenError, UnauthorizedError
from app.core.security import create_access_token, create_refresh_token
from app.modules.admins.repository import AdminRepository
from app.modules.admins.schemas import AdminOut

logger = logging.getLogger(__name__)


class AuthService:
    """Verifies a Google ID token and resolves/bootstraps the corresponding admin.

    Bootstrap rule: the first time a whitelisted email (settings.ADMIN_EMAILS)
    signs in, an `admins` record is created for it. After that, the `admins`
    collection is authoritative — being removed from ADMIN_EMAILS later does
    not revoke access; an admin must be deactivated explicitly (is_active).
    """

    def __init__(self, admin_repo: AdminRepository | None = None):
        self._admin_repo = admin_repo or AdminRepository()

    async def authenticate_with_google(self, google_id_token_str: str) -> tuple[AdminOut, str, str]:
        settings = get_settings()

        try:
            claims = google_id_token.verify_oauth2_token(
                google_id_token_str,
                google_requests.Request(),
                settings.google_client_id,
                # Tolerate a few seconds of clock drift between this machine and
                # Google's servers -- verify_oauth2_token has zero leeway by default,
                # so even normal NTP sync jitter can fail verification otherwise.
                clock_skew_in_seconds=10,
            )
        except ValueError as exc:
            logger.warning("Google ID token verification failed: %s", exc)
            raise UnauthorizedError("Invalid Google credential") from exc

        if not claims.get("email_verified", False):
            raise UnauthorizedError("Google email is not verified")

        email = claims["email"].lower()
        google_sub = claims["sub"]
        name = claims.get("name") or email

        admin = await self._admin_repo.find_by_google_sub(google_sub)

        if admin is None:
            if email not in settings.admin_email_list:
                raise ForbiddenError("This Google account is not an authorized admin")
            try:
                admin = await self._admin_repo.create(google_sub=google_sub, email=email, name=name)
            except DuplicateKeyError as exc:
                raise ConflictError("An admin with this email already exists") from exc
        elif not admin.is_active:
            raise ForbiddenError("Admin account is deactivated")

        access_token = create_access_token(admin.id, admin.email)
        refresh_token = create_refresh_token(admin.id)
        return admin, access_token, refresh_token
