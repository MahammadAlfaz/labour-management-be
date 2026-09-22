from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Labour Management System"
    environment: str = "development"
    debug: bool = False

    mongodb_url: str
    mongodb_db_name: str = "labour_management"

    google_client_id: str = ""
    google_client_secret: str = ""

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 14

    # Comma-separated list of admin emails authorized to sign in.
    # This is the initial bootstrap mechanism; once an admin exists in the
    # `admins` collection, that record is authoritative going forward.
    admin_emails: str = ""

    cors_origins: str = "http://localhost:5173"

    supabase_url: str = ""
    supabase_publishable_key: str = ""
    supabase_secret_key: str = ""
    supabase_jwks_url: str = ""
    supabase_bucket: str = "labour-management"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.1-flash-lite"

    @property
    def admin_email_list(self) -> list[str]:
        return [e.strip().lower() for e in self.admin_emails.split(",") if e.strip()]

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
