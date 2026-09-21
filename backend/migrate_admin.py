from database import engine
from sqlalchemy import text

def run_migration():
    print("Running migration to add username, role, and admin_id columns to users table...")
    try:
        with engine.begin() as conn:
            dialect = conn.dialect.name
            if dialect == "postgresql":
                conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN NOT NULL DEFAULT FALSE;"))
                try:
                    conn.execute(text("ALTER TABLE users ALTER COLUMN email DROP NOT NULL;"))
                except Exception:
                    pass
                conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS username VARCHAR(100) UNIQUE;"))
                conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(50) DEFAULT 'admin' NOT NULL;"))
                conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS admin_id INTEGER REFERENCES users(id) ON DELETE CASCADE;"))
                conn.execute(text("UPDATE users SET role = 'super_admin' WHERE is_admin = TRUE OR email = 'admin@gmail.com';"))
                conn.execute(text("UPDATE users SET role = 'admin' WHERE role IS NULL OR (role != 'super_admin' AND role != 'employee');"))
                print("PostgreSQL migration completed successfully.")
            elif dialect == "sqlite":
                cols = [row[1] for row in conn.execute(text("PRAGMA table_info(users)")).fetchall()]
                if "is_admin" not in cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT 0;"))
                if "username" not in cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN username VARCHAR(100);"))
                if "role" not in cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(50) DEFAULT 'admin';"))
                if "admin_id" not in cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN admin_id INTEGER REFERENCES users(id);"))
                conn.execute(text("UPDATE users SET role = 'super_admin' WHERE is_admin = 1 OR email = 'admin@gmail.com';"))
                conn.execute(text("UPDATE users SET role = 'admin' WHERE role IS NULL OR (role != 'super_admin' AND role != 'employee');"))
                print("SQLite migration completed successfully.")
    except Exception as e:
        print(f"Migration notice/error: {e}")

if __name__ == "__main__":
    run_migration()
