from datetime import date
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Date,ForeignKey
from sqlalchemy.orm import Session
from database import Base, get_db
from org import Organisation_table
router = APIRouter()

class User(BaseModel):
    user_id: int
    org_id:str
    user_name: str
    mobile: str
    designation: str
    date_of_birth: date
class User_table(Base):
    __tablename__ = "users"

    User_id = Column(Integer, primary_key=True, index=True)
    User_name = Column(String)
    Mobile = Column(String)
    Designation = Column(String)
    Date_of_birth = Column(Date)
    Org_id = Column(String,ForeignKey("Organisation.Org_id",ondelete="CASCADE"))

@router.get("/users")
def get_users(
    user_id: int,
    db: Session = Depends(get_db)
):
    user = db.query(User_table).filter(
        User_table.User_id == user_id
    ).first()

    if user is None:
        return {"message": "User not found"}

    return user

@router.post("/addnewuser")
def add_user(user: User,db: Session = Depends(get_db)):
    organisation = db.query(Organisation_table).filter(
        Organisation_table.Org_id == user.org_id).first()
    if organisation is None:
        return {
            "message": "organstion doesnt exits"
        }
    new_user = User_table(
        User_id=user.user_id,
        User_name=user.user_name,
        Mobile=user.mobile,
        Designation=user.designation,
        Date_of_birth=user.date_of_birth,
        Org_id=user.org_id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.put("/updateUser")
def update_user(
    user_id: int,
    user: User,
    db: Session = Depends(get_db)
):
    existing_user = db.query(User_table).filter(
        User_table.User_id == user_id
    ).first()

    if existing_user is None:
        return {"message": "User not found"}

    existing_user.User_name = user.user_name
    existing_user.Mobile = user.mobile
    existing_user.Designation = user.designation
    existing_user.Date_of_birth = user.date_of_birth

    db.commit()
    db.refresh(existing_user)

    return existing_user


@router.delete("/deleteuser/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    user = db.query(User_table).filter(
        User_table.User_id == user_id
    ).first()

    if user is None:
        return {"message": "User not found"}

    db.delete(user)
    db.commit()

    return {
        "message": "User deleted successfully",
        "user_id": user_id
    }