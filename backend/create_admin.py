import sys
from database import SessionLocal
from models import User
from auth import hash_password
from sqlalchemy import select

def create_or_update_super_admin(email: str, password: str):
    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.email == email.lower().strip()))
        if not user:
            print(f"User {email} not found. Creating new Super Admin user...")
            user = User(
                email=email.lower().strip(),
                password_hash=hash_password(password),
                is_admin=True,
                role="super_admin",
            )
            db.add(user)
        else:
            print(f"User {email} found. Updating password and promoting to Super Admin...")
            user.password_hash = hash_password(password)
            user.is_admin = True
            user.role = "super_admin"
            
        db.commit()
        print(f"Success: {email} is now a Super Admin with the requested password.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    email = sys.argv[1] if len(sys.argv) > 1 else "admin@gmail.com"
    password = sys.argv[2] if len(sys.argv) > 2 else "admin123"
    create_or_update_super_admin(email, password)
