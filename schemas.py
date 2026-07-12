from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# tasks

class TaskCreate(BaseModel):
    title:str
    description:Optional[str]=None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    is_completed: Optional[bool] = None

class TaskResponse(BaseModel):
    id:int
    title:str
    description:Optional[str] = None
    is_completed:bool
    created_at:datetime
    owner_id : int

    
    class Config:
        from_attributes = True

# users

class UserCreate(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id : int
    username: str

    class Config:
        from_attributes= True

class Token(BaseModel):
    access_token: str
    token_type:str

class TokenData(BaseModel):
    user_id: Optional[int]= None