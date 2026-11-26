from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UserDB(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)

    tasks = relationship("TaskDB", back_populates="owner", cascade="all, delete-orphan")
    refresh_sessions = relationship(
        "RefreshSessionDB", back_populates="user", cascade="all, delete-orphan"
    )
