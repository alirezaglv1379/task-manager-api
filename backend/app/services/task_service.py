from __future__ import annotations

import logging
from math import ceil

from fastapi import HTTPException
from sqlalchemy import asc, desc
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.types import utc_now
from app.models import TaskDB
from app.schemas.task import SortField, SortOrder

logger = logging.getLogger(__name__)
SORT_COLUMNS = {
    "created_at": TaskDB.created_at,
    "title": TaskDB.title,
    "is_completed": TaskDB.is_completed,
    "id": TaskDB.id,
}


def _commit(
    db: Session,
    *,
    conflict_message: str = "تغییر اطلاعات با محدودیت دیتابیس تعارض دارد.",
) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=conflict_message) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Database operation failed")
        raise HTTPException(status_code=500, detail="خطا در ذخیره اطلاعات.") from exc


def get_task_for_owner(db: Session, task_id: int, owner_id: int) -> TaskDB:
    task = db.query(TaskDB).filter(TaskDB.id == task_id, TaskDB.owner_id == owner_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="وظیفه پیدا نشد.")
    return task


def list_tasks(
    db: Session,
    owner_id: int,
    page: int,
    page_size: int,
    sort_by: SortField,
    order: SortOrder,
    is_completed: bool | None,
) -> dict:
    query = db.query(TaskDB).filter(TaskDB.owner_id == owner_id)
    if is_completed is not None:
        query = query.filter(TaskDB.is_completed.is_(is_completed))

    total = query.count()
    column = SORT_COLUMNS[sort_by]
    direction = asc if order == "asc" else desc
    ordering = [direction(column)]
    if sort_by != "id":
        ordering.append(direction(TaskDB.id))
    items = query.order_by(*ordering).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": ceil(total / page_size) if total else 0,
    }


def create_task(db: Session, owner_id: int, title: str, description: str | None) -> TaskDB:
    task = TaskDB(
        title=title,
        description=description,
        is_completed=False,
        created_at=utc_now(),
        owner_id=owner_id,
    )
    db.add(task)
    _commit(db, conflict_message="امکان ایجاد وظیفه وجود ندارد.")
    db.refresh(task)
    return task


def replace_task(db: Session, task: TaskDB, data: dict) -> TaskDB:
    task.title = data["title"]
    task.description = data["description"]
    task.is_completed = data["is_completed"]
    _commit(db)
    db.refresh(task)
    return task


def patch_task(db: Session, task: TaskDB, data: dict) -> TaskDB:
    for key, value in data.items():
        setattr(task, key, value)
    _commit(db)
    db.refresh(task)
    return task


def delete_task(db: Session, task: TaskDB) -> None:
    db.delete(task)
    _commit(db, conflict_message="امکان حذف وظیفه وجود ندارد.")
