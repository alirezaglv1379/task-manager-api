from sqlalchemy import Column, Integer, ForeignKey , String , Boolean , DateTime
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime , timezone

class TaskDB(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String , nullable= True)
    is_completed=Column(Boolean , default=False)
    created_at= Column(DateTime ,default=lambda: datetime.now(timezone.utc) ,nullable=False)

    owner_id = Column(Integer,ForeignKey('users.id') , nullable= False)

    owner = relationship ("UserDB", back_populates="tasks")

class UserDB(Base):
    __tablename__='users'

    id = Column(Integer , primary_key=True , index=True)
    username = Column (String , nullable= False , unique= True)
    hashed_password = Column(String , nullable= False)

    tasks= relationship ("TaskDB" , back_populates="owner")