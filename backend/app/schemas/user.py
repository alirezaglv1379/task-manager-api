from pydantic import Field, field_validator

from app.schemas.common import ORMModel


class UserCreate(ORMModel):
    username: str = Field(min_length=3, max_length=30)
    password: str = Field(min_length=8)

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        value = value.strip()
        if not 3 <= len(value) <= 30:
            raise ValueError("Username must contain 3 to 30 characters.")
        return value

    @field_validator("password")
    @classmethod
    def validate_password_bytes(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must not exceed 72 UTF-8 bytes for Bcrypt compatibility.")
        return value


class UserResponse(ORMModel):
    id: int
    username: str
