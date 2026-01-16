from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    userId: int
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    friends: list[int]

    class Config:
        from_attributes = True

class FriendReq(BaseModel):
    user_id: int
    friend_id: int
    name: str