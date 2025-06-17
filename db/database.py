from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///../fastapi_parser/orders.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# Dependency for FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ Helper: Check if table exists
def table_exists(table_name):
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()

# ✅ Helper: Check if table has rows
def table_has_data(table_name):
    if not table_exists(table_name):
        return False
    with engine.connect() as connection:
        result = connection.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = result.scalar()
        return count > 0
