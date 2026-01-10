from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from config import JWT_SECRET, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


def _normalize_password(password: str) -> str:
    pwd_bytes = password.encode("utf-8")
    if len(pwd_bytes) > 72:
        pwd_bytes = pwd_bytes[:72]
    return pwd_bytes.decode("utf-8", errors="ignore")


def hash_password(password: str) -> str:
    return pwd_context.hash(_normalize_password(password))


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(_normalize_password(plain), hashed)


def create_access_token(data: dict):
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)


def decode_token(token: str):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
    except JWTError:
        return None
