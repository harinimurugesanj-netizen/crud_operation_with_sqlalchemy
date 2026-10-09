from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import Column, String
from sqlalchemy.orm import Session

from database import Base, get_db
router = APIRouter()
class Organisation(BaseModel):
    org_id: str
    org_name: str
    org_address: str
    org_email: str

class Organisation_table(Base):
    __tablename__ = "Organisation"

    Org_id = Column(String, primary_key=True, index=True)
    Org_name = Column(String)
    Org_address = Column(String)
    Org_email = Column(String)


@router.get("/get_organisation")
def get_organisation(
    org_id: str,
    db: Session = Depends(get_db)
):
    org = db.query(Organisation_table).filter(
        Organisation_table.Org_id == org_id
    ).first()

    if org is None:
        return {"message": "Organisation not found"}

    return org

@router.post("/create_organisation")
def add_organisation(
    organisation: Organisation,
    db: Session = Depends(get_db)
):
    new_organisation = Organisation_table(
        Org_id=organisation.org_id,
        Org_name=organisation.org_name,
        Org_address=organisation.org_address,
        Org_email=organisation.org_email
    )

    db.add(new_organisation)
    db.commit()
    db.refresh(new_organisation)

    return new_organisation

@router.put("/update/{org_id}")
def update_organisation(
    org_id: str,
    organisation: Organisation,
    db: Session = Depends(get_db)
):
    existing_organisation = db.query(Organisation_table).filter(
        Organisation_table.Org_id == org_id
    ).first()

    if existing_organisation is None:
        return {"message": "Organisation not found"}

    existing_organisation.Org_name = organisation.org_name
    existing_organisation.Org_address = organisation.org_address
    existing_organisation.Org_email = organisation.org_email
    db.commit()
    db.refresh(existing_organisation)
    return existing_organisation
@router.delete("/delete_organisation/{org_id}")
def delete_organisation(
    org_id: str,
    db: Session = Depends(get_db)
):
    organisation = db.query(Organisation_table).filter(
        Organisation_table.Org_id == org_id
    ).first()
    if organisation is None:
        return {
            "message": "Organisation not found"
        }
    db.delete(organisation)
    db.commit()
    return {
        "message": "deleted successfully",
        "org_id": org_id
    }