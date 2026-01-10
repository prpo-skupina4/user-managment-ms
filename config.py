import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./auth.db")
JWT_SECRET = os.getenv("JWT_SECRET", "DEV_SECRET")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
