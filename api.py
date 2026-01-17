from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from db import SessionLocal
from models import User, Friends
from schemas import UserOut, UserCreate, FriendReq
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_token,
)


router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/users")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # Check if email already exists
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(400, "User already exists")
    
    # Check if userId already exists
    if db.query(User).filter(User.id == user.userId).first():
        raise HTTPException(400, "User ID already exists")

    new_user = User(id=user.userId, email=user.email, hashed_password=hash_password(user.password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"id": new_user.id, "email": new_user.email}


@router.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")

    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}

@router.post("/users/{user_id}/friends")
def add_friend(user_id: int, rq:FriendReq, db: Session = Depends(get_db)):
    # user_id is taken from the path parameter; request body user_id is ignored
    friend_id = rq.friend_id
    name = rq.name
    user = db.query(User).filter(User.id == user_id).first()
    friend = db.query(User).filter(User.id == friend_id).first()
    if not user or not friend:
        raise HTTPException(404, "User not found")
    
    if db.query(Friends).filter(Friends.user_id == user_id,Friends.friend_id==friend_id ).first():
        raise HTTPException(400, "Friendship already exists")

    db.add(Friends(user_id=user_id, friend_id=friend_id, name=name ))
    db.commit()
    return {"user_id": user_id, "friend_id":friend_id, "name":name}

@router.get("/users/{user_id}/friends")
def list_friends(user_id: int, skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    # Validate pagination parameters
    if skip < 0:
        raise HTTPException(400, "skip must be non-negative")
    if limit < 1:
        raise HTTPException(400, "limit must be at least 1")
    if limit > 100:
        raise HTTPException(400, "limit cannot exceed 100")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    
    # Get total count for pagination metadata
    total = db.query(Friends).filter(Friends.user_id == user_id).count()
    
    # Get paginated results
    friends = db.query(Friends).filter(Friends.user_id == user_id).offset(skip).limit(limit).all()
    
    return {
        "items": [
            {"friend_id": f.friend_id, "name": f.name}
            for f in friends
        ],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/users/me")
def me(token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    if not payload:
        raise HTTPException(401, "Invalid token")
    return payload


@router.get("/users/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return user