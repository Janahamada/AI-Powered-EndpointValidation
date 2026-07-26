"""Authentication & user contracts."""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenPayload(BaseModel):
    sub: Optional[str] = None  # username
    exp: Optional[int] = None


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    email: EmailStr  # strict validation on input, where it matters
    role: Literal["admin", "analyst"] = "analyst"
    password: str = Field(min_length=6, max_length=128)


class UserOut(BaseModel):
    # email is a plain str on output: we don't re-validate stored values, and
    # internal TLDs like ".local" are legitimate for on-prem service accounts.
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    role: str
    is_active: int
    created_at: datetime
