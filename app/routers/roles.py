from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.utilities.db import get_db
from app.schemas.role import RoleCreate, RoleUpdate, RoleResponse
from app.repositories.role_repository import RoleRepository
from app.utilities.jwt import get_current_admin

router = APIRouter(
    prefix="/roles",
    tags=["roles"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_admin)]
)

@router.get("/", response_model=List[RoleResponse])
def read_roles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve roles.
    """
    roles = RoleRepository.get_all(db, skip=skip, limit=limit)
    return roles

@router.post("/", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
def create_role(role: RoleCreate, db: Session = Depends(get_db)):
    """
    Create a new role.
    """
    try:
        return RoleRepository.create(db=db, role_in=role)
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error de integridad de datos al crear el rol."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while creating the role: {str(e)}"
        )

@router.get("/{role_id}", response_model=RoleResponse)
def read_role(role_id: int, db: Session = Depends(get_db)):
    """
    Get role by ID.
    """
    db_role = RoleRepository.get_by_id(db, role_id=role_id)
    if db_role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return db_role

@router.patch("/{role_id}", response_model=RoleResponse)
def update_role(role_id: int, role: RoleUpdate, db: Session = Depends(get_db)):
    """
    Update a role.
    """
    try:
        db_role = RoleRepository.update(db=db, role_id=role_id, role_in=role)
        if db_role is None:
            raise HTTPException(status_code=404, detail="Role not found")
        return db_role
    except HTTPException:
        raise
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error de integridad de datos al actualizar el rol."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while updating the role: {str(e)}"
        )

@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(role_id: int, db: Session = Depends(get_db)):
    """
    Delete a role.
    """
    success = RoleRepository.delete(db=db, role_id=role_id)
    if not success:
        raise HTTPException(status_code=404, detail="Role not found")
    return None
