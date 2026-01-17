from sqlalchemy import String, Integer, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, object_session
from pydantic import constr


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    @property
    def friends(self) -> list[int]:
        """Get list of friend IDs for this user"""
        session = object_session(self)
        if session is None:
            return []
        friend_records = session.query(Friends).filter(Friends.user_id == self.id).all()
        return [f.friend_id for f in friend_records]

class Friends(Base):
    __tablename__ = "friends"
    user_id = mapped_column(Integer, ForeignKey("users.id"), primary_key=True)
    friend_id = mapped_column(Integer, ForeignKey("users.id"), primary_key=True)
    name = mapped_column(String(50), nullable=False)
