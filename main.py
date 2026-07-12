from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta , timezone ,datetime


from database import engine, SessionLocal, Base
from models import TaskDB , UserDB
from schemas import TaskCreate , TaskResponse , TaskUpdate , Token , UserCreate , UserResponse
from auth import get_password_hash ,create_access_token ,authenticate_user , get_current_user
from config import ACCESS_TOKEN_EXPIRE_MINUTES



app = FastAPI(title="مدیریت تسک‌ها", version="1.0.0") 
# ایجاد جدول‌ها در دیتابیس
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# روت های ورود و اهراز هویت

@app.post('/signup' , response_model=UserResponse)
def signup(user_new:UserCreate , db: Session = Depends(get_db)):
    db_user=db.query(UserDB).filter(UserDB.username == user_new.username).first()
    if db_user :
        raise HTTPException(status_code=400,detail="این نام کاربری قبلاً ثبت شده است")
    
    pass_hash=get_password_hash(user_new.password)

    user= UserDB(username = user_new.username ,
                 hashed_password= pass_hash)
    
    db.add(user)
    db.commit()
    db.refresh(user)

    return user

@app.post('/login' , response_model=Token)
def login(user_form:OAuth2PasswordRequestForm = Depends() , db :Session = Depends(get_db)):
    user = authenticate_user(db,user_form.username,user_form.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="نام کاربری یا رمز عبور اشتباه است",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_experic=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token({'sub':str(user.id)},access_token_experic)
    return {'access_token':access_token , 'token_type':'bearer'}


# روت های اصلی برای هر کاربر


@app.get("/tasks",response_model=List[TaskResponse])

def get_tasks(
    current_user: UserDB = Depends(get_current_user),
    db:Session=Depends(get_db),
    is_completed:bool=None
    ):

    query = db.query(TaskDB).filter(TaskDB.owner_id == current_user.id)
    if is_completed :
        query = query.filter(TaskDB.is_completed == is_completed)
    return query.all()

@app.get('/tasks/{task_id}',response_model=TaskResponse)

def get_task(
    task_id:int,
    current_user: UserDB = Depends(get_current_user),
    db:Session=Depends(get_db)
    ):

    task=db.query(TaskDB).filter(TaskDB.id == task_id , TaskDB.owner_id == current_user.id).first()
    if task is None :
        raise HTTPException(status_code=404 , detail="id not found")
    else :
        return task
    
@app.post('/tasks',response_model=TaskResponse , status_code=201)

def create_task(
    new_task:TaskCreate,
    current_user: UserDB = Depends(get_current_user),
    db:Session=Depends(get_db)
    ):

    task=TaskDB(
        title = new_task.title , 
       description = new_task.description,
       is_completed=False,
       created_at = datetime.now(timezone.utc),
       owner_id = current_user.id
        )
    
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

@app.put('/tasks/{task_id}',response_model=TaskResponse)

def update_task(new_task:TaskCreate ,
                task_id:int ,
                db:Session = Depends(get_db),
                current_user: UserDB = Depends(get_current_user)   
                   ):
    task = db.query(TaskDB).filter(TaskDB.id == task_id , TaskDB.owner_id == current_user.id).first()
    if task is None:
        raise HTTPException(status_code=404 , detail="id not found")
    else:
        task.title = new_task.title
        task.description = new_task.description
        db.commit()
        db.refresh(task)
        return task

@app.patch('/tasks/{task_id}',response_model=TaskResponse)

def edite_task(
    task_id : int ,
    new_task:TaskUpdate ,
    db:Session= Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
    ):

    task_db=db.query(TaskDB).filter(TaskDB.id == task_id , TaskDB.owner_id == current_user.id).first()

    if task_db is None : 
        raise HTTPException(status_code=404 , detail='id not found')
    
    else :
        up_task=new_task.model_dump(exclude_unset=True)
        for key , value in up_task.items():
            setattr(task_db , key ,value)
        
        db.commit()
        db.refresh(task_db)
        return task_db

@app.delete('/tasks/{task_id}', status_code= 204)

def delete_task(task_id : int ,
                db :Session = Depends(get_db),
                current_user: UserDB = Depends(get_current_user)
                ):
    
    task = db.query(TaskDB).filter(TaskDB.id == task_id , TaskDB.owner_id == current_user.id).first()
    if task is None:
        raise HTTPException(status_code=404 , detail="id not found")
    else:
        db.delete(task)
        db.commit()