from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL


# For SQLite, use DATABASE_URL as-is. For MySQL/PostgreSQL, append database name
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(f"{DATABASE_URL}/user-managment")

SessionLocal = sessionmaker(bind=engine)
