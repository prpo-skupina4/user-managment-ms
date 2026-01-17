from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL


engine = create_engine(f"{DATABASE_URL}/user-managment")

SessionLocal = sessionmaker(bind=engine)
