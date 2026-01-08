from typing import Optional
from pydantic import BaseModel, HttpUrl
from enum import Enum
from datetime import datetime
from uuid import UUID


# =========================
# ENUM
# =========================
class UserRole(str, Enum):
    admin = "admin"
    user = "user"


# =========================
# CREATE
# =========================
class UserPayload(BaseModel):
    username: str
    picture_url: HttpUrl
    role: UserRole
    user_id_line: str


# =========================
# UPDATE (PATCH)
# =========================
class UserUpdatePayload(BaseModel):
    username: Optional[str] = None
    picture_url: Optional[HttpUrl] = None
    role: Optional[UserRole] = None


# =========================
# SYNC (POST /users/{id}/sync)
# =========================
class UserSyncPayload(BaseModel):
    username: Optional[str] = None
    picture_url: Optional[HttpUrl] = None
    role: Optional[UserRole] = None


# =========================
# RESPONSE
# =========================
class UserResponse(BaseModel):
    user_id: UUID
    username: str
    picture_url: HttpUrl
    role: UserRole
    created_at: datetime
    updated_at: datetime
    user_id_line: str

    class Config:
        orm_mode = True
