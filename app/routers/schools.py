from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.utilities.db import get_db
from app.schemas.school import SchoolCreate, SchoolUpdate, SchoolResponse
from app.repositories.school_repository import SchoolRepository
from app.utilities.jwt import get_current_admin

router = APIRouter(
    prefix="/schools",
    tags=["schools"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[SchoolResponse])
def read_schools(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve schools.
    """
    schools = SchoolRepository.get_all(db, skip=skip, limit=limit)
    return schools

@router.post("/", response_model=SchoolResponse, status_code=status.HTTP_201_CREATED)
def create_school(
    school: SchoolCreate,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    """
    Create a new school.
    """
    try:
        return SchoolRepository.create(db=db, school_in=school)
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error de integridad de datos al crear la escuela."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while creating the school: {str(e)}"
        )

@router.get("/{school_id}", response_model=SchoolResponse)
def read_school(
    school_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    """
    Get school by ID.
    """
    db_school = SchoolRepository.get_by_id(db, school_id=school_id)
    if db_school is None:
        raise HTTPException(status_code=404, detail="School not found")
    return db_school

@router.patch("/{school_id}", response_model=SchoolResponse)
def update_school(
    school_id: int,
    school: SchoolUpdate,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    """
    Update a school.
    """
    try:
        db_school = SchoolRepository.update(db=db, school_id=school_id, school_in=school)
        if db_school is None:
            raise HTTPException(status_code=404, detail="School not found")
        return db_school
    except HTTPException:
        raise
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error de integridad de datos al actualizar la escuela."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while updating the school: {str(e)}"
        )

@router.delete("/{school_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_school(
    school_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    """
    Delete a school.
    """
    success = SchoolRepository.delete(db=db, school_id=school_id)
    if not success:
        raise HTTPException(status_code=404, detail="School not found")
    return None
