from pydantic import BaseModel, EmailStr, ConfigDict


class UserCreate(BaseModel):
    userId: int
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    email: EmailStr
    is_active: bool
    friends: list[int]

class FriendReq(BaseModel):
    friend_id: int
    name: str