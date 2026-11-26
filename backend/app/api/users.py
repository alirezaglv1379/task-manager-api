from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user
from app.models import UserDB
from app.schemas.user import UserResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user: UserDB = Depends(get_current_user)):
    return current_user
