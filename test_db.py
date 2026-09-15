from sqlalchemy import text
from app.database.session import engine, SessionLocal

def test_database_connection():
    print("Testing database engine initialization...")
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
            print(f"Database connection successful! Test query returned: {result}")
    except Exception as e:
        print(f"Database connection failed: {e}")

if __name__ == "__main__":
    test_database_connection()