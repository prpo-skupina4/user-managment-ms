from sqlalchemy import String, Integer, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from pydantic import constr


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class Friends(Base):
    __tablename__ = "friends"
    user_id = mapped_column(Integer, ForeignKey("users.id"), primary_key=True)
    friend_id = mapped_column(Integer, ForeignKey("users.id"), primary_key=True)
    name = mapped_column(String(50), nullable=False)
