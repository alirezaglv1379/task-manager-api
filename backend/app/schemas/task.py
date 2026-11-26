from datetime import datetime
from typing import Literal

from pydantic import Field, field_validator

from app.schemas.common import ORMModel


class TaskCreate(ORMModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Title cannot be empty.")
        return value


class TaskReplace(ORMModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(..., max_length=2000)
    is_completed: bool

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Title cannot be empty.")
        return value


class TaskPatch(ORMModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    is_completed: bool | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("Title cannot be empty.")
        return value


class TaskResponse(ORMModel):
    id: int
    title: str
    description: str | None
    is_completed: bool
    created_at: datetime
    owner_id: int


class TaskPageResponse(ORMModel):
    items: list[TaskResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


SortField = Literal["created_at", "title", "is_completed", "id"]
SortOrder = Literal["asc", "desc"]
