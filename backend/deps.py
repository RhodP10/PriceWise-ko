from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from auth import decode_access_token
from database import SessionLocal
from models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    user_id = decode_access_token(token)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = db.get(User, int(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def get_super_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "super_admin" and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Super admin permission required")
    return current_user


def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Requires role to be admin or super_admin."""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin permission required")
    return current_user
