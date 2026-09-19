from pydantic import BaseModel

from app.modules.admins.schemas import AdminOut


class GoogleLoginRequest(BaseModel):
    id_token: str


class AuthResponse(BaseModel):
    admin: AdminOut
