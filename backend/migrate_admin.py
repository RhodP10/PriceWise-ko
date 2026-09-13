from database import engine
from sqlalchemy import text

def run_migration():
    print("Running migration to add is_admin column to users table...")
    try:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT FALSE;"))
            print("Migration successful: 'is_admin' column added.")
    except Exception as e:
        print(f"Migration failed or already applied: {e}")

if __name__ == "__main__":
    run_migration()
