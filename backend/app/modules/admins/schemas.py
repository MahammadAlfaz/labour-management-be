from datetime import datetime

from pydantic import BaseModel, EmailStr


class AdminOut(BaseModel):
    id: str
    email: EmailStr
    name: str
    is_active: bool
    created_at: datetime
