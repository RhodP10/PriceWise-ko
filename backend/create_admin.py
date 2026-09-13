import sys
from database import SessionLocal
from models import User
from auth import hash_password
from sqlalchemy import select

def create_or_update_admin(email: str, password: str):
    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.email == email.lower().strip()))
        if not user:
            print(f"User {email} not found. Creating new admin user...")
            user = User(
                email=email.lower().strip(),
                password_hash=hash_password(password),
                is_admin=True
            )
            db.add(user)
        else:
            print(f"User {email} found. Updating password and setting to admin...")
            user.password_hash = hash_password(password)
            user.is_admin = True
            
        db.commit()
        print(f"Success: {email} is now an admin with the requested password.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_or_update_admin("admin@gmail.com", "admin123")
