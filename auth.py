# ========================================
# توابع احراز هویت (JWT، هش کردن رمز)
# ========================================

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from database import SessionLocal
from models import UserDB
from schemas import TokenData
from config import SECRET_KEY, ALGORITHM,ACCESS_TOKEN_EXPIRE_MINUTES

# تنظیمات هش کردن رمز
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# تنظیمات OAuth2 (برای دریافت توکن از هدر Authorization)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# وابستگی برای دریافت سشن دیتابیس
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# توابع هش کردن و تأیید رمز
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# تأیید هویت کاربر
def authenticate_user(db: Session, username: str, password: str):
    user = db.query(UserDB).filter(UserDB.username == username).first()
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

# ساخت توکن JWT
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# دریافت کاربر فعلی از توکن
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=int(user_id))
    except JWTError:
        raise credentials_exception
    
    user = db.query(UserDB).filter(UserDB.id == token_data.user_id).first()
    if user is None:
        raise credentials_exception
    return user