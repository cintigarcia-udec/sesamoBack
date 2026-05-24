from typing import Any, Dict, List, Optional, cast
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import distinct, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.utilities.db import get_db
from app.schemas.user import TeacherPublicResponse, UserCreate, UserUpdate, UserResponse
from app.models.category import Category
from app.models.questionnaire import Questionnaire
from app.models.user_response import UserResponse as UserResponseModel
from app.repositories.user_repository import UserRepository
from app.repositories.user_response_repository import UserResponseRepository
from app.utilities.jwt import get_current_admin, get_current_user, get_current_admin_or_teacher

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[UserResponse])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user=Depends(get_current_admin_or_teacher)):
    """
    Retrieve users.
    """
    if getattr(current_user, "role_id", None) == 3:
        school_id = getattr(current_user, "school_id", None)
        if school_id is None:
            return []
        users = UserRepository.get_students_by_school_id(db, school_id=school_id, skip=skip, limit=limit)
    else:
        users = UserRepository.get_all(db, skip=skip, limit=limit)
    return users


@router.get("/teachers", response_model=List[TeacherPublicResponse])
def read_teachers(teacher_user_id: Optional[int] = None, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    school_id = None
    if getattr(current_user, "role_id", None) != 1:
        school_id = getattr(current_user, "school_id", None)

    rows = UserRepository.get_teachers_public(db, school_id=school_id, teacher_user_id=teacher_user_id)
    return [
        {"name": name, "last_name": last_name, "school_name": school_name}
        for name, last_name, school_name in rows
    ]

@router.get("/{user_id}", response_model=UserResponse)
def read_user(user_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_admin_or_teacher)):
    """
    Get user by ID.
    """
    if getattr(current_user, "role_id", None) == 3:
        school_id = getattr(current_user, "school_id", None)
        if school_id is None:
            raise HTTPException(status_code=404, detail="User not found")
        db_user = UserRepository.get_student_by_id_and_school_id(db, user_id=user_id, school_id=school_id)
    else:
        db_user = UserRepository.get_by_id(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.get("/{user_id}/dashboard")
def read_user_dashboard(user_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if getattr(current_user, "role_id", None) != 1 and getattr(current_user, "id", None) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para ver las métricas de otro usuario",
        )

    avg_score, total_responses, total_questionnaires_completed = (
        db.query(
            func.avg(UserResponseModel.score),
            func.count(UserResponseModel.id),
            func.count(distinct(UserResponseModel.questionnaire_id)),
        )
        .filter(UserResponseModel.user_id == user_id)
        .one()
    )

    average_score = float(avg_score) if avg_score is not None else 0.0

    week_start = datetime.now(timezone.utc) - timedelta(days=7)
    total_seconds_raw = (
        db.query(func.coalesce(func.sum(UserResponseModel.duration_seconds), 0))
        .filter(UserResponseModel.user_id == user_id, UserResponseModel.created_at >= week_start)
        .scalar()
    )
    total_seconds = int(total_seconds_raw or 0)
    weekly_study_minutes = int(round(total_seconds / 60))

    last_response = (
        db.query(UserResponseModel)
        .filter(UserResponseModel.user_id == user_id)
        .order_by(UserResponseModel.created_at.desc())
        .first()
    )

    last_questionnaire_id: Optional[int] = None
    last_questionnaire_name: Optional[str] = None
    last_module: Optional[str] = None
    last_category_id: Optional[int] = None

    if last_response is not None:
        last_questionnaire_id = cast(int, last_response.questionnaire_id)
        questionnaire = (
            db.query(Questionnaire)
            .filter(Questionnaire.id == last_response.questionnaire_id)
            .first()
        )
        if questionnaire is not None:
            questionnaire_category_id = cast(Optional[int], questionnaire.category_id)
            questionnaire_number = cast(int, questionnaire.questionnaire_number)
            last_category_id = questionnaire_category_id
            last_questionnaire_name = questionnaire.category_name or f"Cuestionario {questionnaire_number}"
            total_in_category = None
            if questionnaire_category_id is not None:
                total_in_category = (
                    db.query(func.count(Questionnaire.id))
                    .filter(Questionnaire.category_id == questionnaire_category_id)
                    .scalar()
                )
            if total_in_category:
                last_module = f"Módulo {questionnaire_number:02d}/{int(total_in_category):02d}"
            else:
                last_module = f"Módulo {questionnaire_number:02d}"

    return {
        "average_score": round(average_score, 1),
        "total_responses": int(total_responses or 0),
        "total_questionnaires_completed": int(total_questionnaires_completed or 0),
        "weekly_study_minutes": weekly_study_minutes,
        "weekly_goal_minutes": 300,
        "last_questionnaire_id": last_questionnaire_id,
        "last_questionnaire_name": last_questionnaire_name,
        "last_module": last_module,
        "last_category_id": last_category_id,
    }


@router.get("/{user_id}/categories-progress")
def read_user_categories_progress(user_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if getattr(current_user, "role_id", None) != 1 and getattr(current_user, "id", None) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para ver las métricas de otro usuario",
        )

    categories = db.query(Category).order_by(Category.id.asc()).all()

    total_questionnaires_by_category: Dict[int, int] = {}
    total_rows = (
        db.query(Questionnaire.category_id, func.count(Questionnaire.id))
        .group_by(Questionnaire.category_id)
        .all()
    )
    for category_id_value, total_value in total_rows:
        if category_id_value is None:
            continue
        total_questionnaires_by_category[cast(int, category_id_value)] = int(total_value or 0)

    progress_rows = (
        db.query(
            Questionnaire.category_id.label("category_id"),
            func.count(distinct(UserResponseModel.questionnaire_id)).label("completed_questionnaires"),
            func.avg(UserResponseModel.score).label("average_score"),
        )
        .join(Questionnaire, Questionnaire.id == UserResponseModel.questionnaire_id)
        .filter(UserResponseModel.user_id == user_id)
        .group_by(Questionnaire.category_id)
        .all()
    )
    progress_by_category: Dict[int, Dict[str, Any]] = {
        cast(int, row.category_id): {
            "completed_questionnaires": int(row.completed_questionnaires or 0),
            "average_score": float(row.average_score) if row.average_score is not None else 0.0,
        }
        for row in progress_rows
        if row.category_id is not None
    }

    result: List[Dict[str, Any]] = []
    for category in categories:
        category_id = cast(int, category.id)
        total_questionnaires = int(total_questionnaires_by_category.get(category_id, 0) or 0)
        completed_questionnaires = int(progress_by_category.get(category_id, {}).get("completed_questionnaires", 0))
        average_score = float(progress_by_category.get(category_id, {}).get("average_score", 0.0))

        if total_questionnaires == 0:
            status_text = "Bloqueado"
        elif completed_questionnaires == 0:
            status_text = "No iniciado"
        elif completed_questionnaires < total_questionnaires:
            status_text = "En progreso"
        else:
            status_text = "Completado"

        result.append(
            {
                "category_id": category_id,
                "category_name": category.name,
                "status": status_text,
                "average_score": round(average_score, 1),
                "total_questionnaires": total_questionnaires,
                "completed_questionnaires": completed_questionnaires,
            }
        )

    return result

@router.patch("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user: UserUpdate, db: Session = Depends(get_db), _: dict = Depends(get_current_admin)):
    """
    Update a user.
    """
    try:
        db_user = UserRepository.update(db=db, user_id=user_id, user_in=user)
        if db_user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return db_user
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except IntegrityError as e:
        db.rollback()
        error_msg = str(e.orig)
        if "users.email" in error_msg:
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está registrado."
            )
        if "school_id" in error_msg:
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La escuela especificada no existe."
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error de integridad de datos."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while updating the user: {str(e)}"
        )

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db), _: dict = Depends(get_current_admin)):
    """
    Delete a user.
    """
    success = UserRepository.delete(db=db, user_id=user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return None
