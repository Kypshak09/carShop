from typing import List, Union, Optional

from pydantic import BaseModel


class ProjectBase(BaseModel):
    title: str
    description: Union[str, None] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[Union[str, None]] = None


class Project(ProjectBase):
    id: int
    owner_id: int

    class Config:
        orm_mode = True


class UserBase(BaseModel):
    email: str
    f_name: str
    sr_name: str


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: Optional[str] = None
    f_name: Optional[str] = None
    sr_name: Optional[str] = None


class User(UserBase):
    id: int
    is_active: bool
    projects: List[Project] = []

    class Config:
        orm_mode = True
