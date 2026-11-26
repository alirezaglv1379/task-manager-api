from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models import UserDB
from app.schemas.task import (
    SortField,
    SortOrder,
    TaskCreate,
    TaskPageResponse,
    TaskPatch,
    TaskReplace,
    TaskResponse,
)
from app.services.task_service import (
    create_task,
    delete_task,
    get_task_for_owner,
    list_tasks,
    patch_task,
    replace_task,
)

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("", response_model=TaskPageResponse)
def get_tasks(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    sort_by: SortField = "created_at",
    order: SortOrder = "desc",
    is_completed: bool | None = None,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_tasks(db, current_user.id, page, page_size, sort_by, order, is_completed)


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: int,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_task_for_owner(db, task_id, current_user.id)


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task_endpoint(
    new_task: TaskCreate,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_task(db, current_user.id, new_task.title, new_task.description)


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    new_task: TaskReplace,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = get_task_for_owner(db, task_id, current_user.id)
    return replace_task(db, task, new_task.model_dump())


@router.patch("/{task_id}", response_model=TaskResponse)
def edit_task(
    task_id: int,
    new_task: TaskPatch,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    updates = new_task.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=422, detail="حداقل یک فیلد برای ویرایش ارسال کنید.")
    if "title" in updates and updates["title"] is None:
        raise HTTPException(status_code=422, detail="عنوان نمی‌تواند null باشد.")
    if "is_completed" in updates and updates["is_completed"] is None:
        raise HTTPException(status_code=422, detail="وضعیت انجام‌شدن نمی‌تواند null باشد.")
    task = get_task_for_owner(db, task_id, current_user.id)
    return patch_task(db, task, updates)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_task(
    task_id: int,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = get_task_for_owner(db, task_id, current_user.id)
    delete_task(db, task)
    return None
