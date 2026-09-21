import sys
from database import SessionLocal
from models import User
from sqlalchemy import select

def make_super_admin(email: str):
    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.email == email.lower().strip()))
        if not user:
            print(f"Error: User with email '{email}' not found.")
            return
        
        user.is_admin = True
        user.role = "super_admin"
        db.commit()
        print(f"Success: User '{email}' is now a Super Admin.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python make_admin.py <user_email>")
        sys.exit(1)
    
    make_super_admin(sys.argv[1])
