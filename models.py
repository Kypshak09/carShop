import sqlalchemy
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, LargeBinary
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    f_name = Column(String(255))
    sr_name = Column(String(255))
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

    project = relationship("Project", back_populates="owner")

    def __repr__(self):
        return f"User(user_id {self.id!r}, name = {self.f_name!r}, surname={self.sr_name}"


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", backref='projects')


