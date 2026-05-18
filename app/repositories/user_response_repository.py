from typing import List, Optional, Dict, Any, cast
import json
from sqlalchemy.orm import Session
from app.models.user_response import UserResponse
from app.models.question import Question
from app.models.answer_option import AnswerOption
from app.schemas.user_response import UserResponseCreate, UserResponseUpdate

class UserResponseRepository:
    """
    Repository class for performing database operations on the UserResponse model.
    """

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[UserResponse]:
        return db.query(UserResponse).offset(skip).limit(limit).all()

    @staticmethod
    def get_by_id(db: Session, user_response_id: int) -> Optional[UserResponse]:
        return db.query(UserResponse).filter(UserResponse.id == user_response_id).first()

    @staticmethod
    def normalize_answers(user_answers: Any) -> Dict[str, Any]:
        if user_answers is None:
            return {}

        if isinstance(user_answers, dict):
            return {str(k): v for k, v in user_answers.items()}

        if isinstance(user_answers, list):
            normalized: Dict[str, Any] = {}
            for item in user_answers:
                if not isinstance(item, dict):
                    continue
                question_id = item.get("question_id", item.get("questionId", item.get("question")))
                if question_id is None:
                    continue
                value = (
                    item.get("option_key")
                    if item.get("option_key") is not None
                    else item.get("optionKey")
                )
                if value is None:
                    value = (
                        item.get("answer_option_id")
                        if item.get("answer_option_id") is not None
                        else item.get("answerOptionId")
                    )
                if value is None:
                    value = item.get("id")
                if value is None:
                    value = item.get("answer")
                normalized[str(question_id)] = value
            return normalized

        if isinstance(user_answers, str):
            candidate: Any = user_answers
            for _ in range(5):
                if not isinstance(candidate, str):
                    break
                try:
                    candidate = json.loads(candidate)
                except json.JSONDecodeError:
                    break
            return UserResponseRepository.normalize_answers(candidate)

        return {}

    @staticmethod
    def parse_answers_text(answers_text: Any) -> Dict[str, Any]:
        if answers_text is None:
            return {}
        if isinstance(answers_text, dict):
            return {str(k): v for k, v in answers_text.items()}
        if isinstance(answers_text, str):
            try:
                parsed = json.loads(answers_text)
            except json.JSONDecodeError:
                return {}
            if isinstance(parsed, dict):
                return {str(k): v for k, v in parsed.items()}
        return {}

    @staticmethod
    def calculate_score(db: Session, questionnaire_id: int, user_answers: Dict[str, Any]) -> float:
        questions = db.query(Question).filter(Question.questionnaire_id == questionnaire_id).all()
        
        if not questions:
            return 0.0
        
        correct_count = 0
        answered_count = 0
        
        for question in questions:
            question_id_str = str(question.id)
            
            if question_id_str not in user_answers:
                continue

            answered_count += 1
            
            user_answer_raw = user_answers[question_id_str]
            chosen_key: Optional[str] = None
            chosen_id: Optional[int] = None

            if isinstance(user_answer_raw, dict):
                if user_answer_raw.get("option_key") is not None:
                    chosen_key = str(user_answer_raw.get("option_key"))
                elif user_answer_raw.get("optionKey") is not None:
                    chosen_key = str(user_answer_raw.get("optionKey"))

                candidate_id = (
                    user_answer_raw.get("answer_option_id")
                    if user_answer_raw.get("answer_option_id") is not None
                    else user_answer_raw.get("answerOptionId")
                )
                if candidate_id is None:
                    candidate_id = user_answer_raw.get("id")
                if candidate_id is not None:
                    try:
                        chosen_id = int(candidate_id)
                    except (TypeError, ValueError):
                        chosen_id = None
            else:
                if isinstance(user_answer_raw, (int, float)) and int(user_answer_raw) == user_answer_raw:
                    chosen_id = int(user_answer_raw)
                else:
                    candidate_str = str(user_answer_raw).strip()
                    if candidate_str.isdigit():
                        chosen_id = int(candidate_str)
                    else:
                        chosen_key = candidate_str
            
            correct_option = db.query(AnswerOption).filter(
                AnswerOption.question_id == question.id,
                AnswerOption.is_correct.is_(True)
            ).first()
            
            if not correct_option or correct_option.option_key is None:
                continue

            correct_option_id = cast(int, correct_option.id)

            if chosen_key is not None and chosen_key.strip().upper() == str(correct_option.option_key).strip().upper():
                correct_count += 1
                continue

            if chosen_id is not None and correct_option_id == chosen_id:
                correct_count += 1
        
        if answered_count == 0:
            return 0.0
        
        score = (correct_count / answered_count) * 100
        return score

    @staticmethod
    def create(db: Session, user_response_in: UserResponseCreate) -> UserResponse:
        user_answers = UserResponseRepository.normalize_answers(user_response_in.answers)
        score = UserResponseRepository.calculate_score(
            db=db,
            questionnaire_id=user_response_in.questionnaire_id,
            user_answers=user_answers
        )
        
        db_user_response = UserResponse(
            user_id=user_response_in.user_id,
            questionnaire_id=user_response_in.questionnaire_id,
            score=score,
            answers=json.dumps(user_answers)
        )
        db.add(db_user_response)
        db.commit()
        db.refresh(db_user_response)
        return db_user_response

    @staticmethod
    def update(db: Session, user_response_id: int, user_response_in: UserResponseUpdate) -> Optional[UserResponse]:
        db_user_response = UserResponseRepository.get_by_id(db, user_response_id)
        if not db_user_response:
            return None
        
        update_data = user_response_in.model_dump(exclude_unset=True)
        update_data.pop("score", None)
        
        if "answers" in update_data or "questionnaire_id" in update_data:
            questionnaire_id = cast(int, update_data.get("questionnaire_id", db_user_response.questionnaire_id))
            if "answers" in update_data:
                user_answers_raw = update_data["answers"]
                del update_data["answers"]
            else:
                user_answers_raw = UserResponseRepository.parse_answers_text(cast(str, db_user_response.answers))

            user_answers = UserResponseRepository.normalize_answers(user_answers_raw)
            score = UserResponseRepository.calculate_score(
                db=db,
                questionnaire_id=questionnaire_id,
                user_answers=user_answers
            )
            setattr(db_user_response, "score", score)
            setattr(db_user_response, "answers", json.dumps(user_answers))
        
        for field, value in update_data.items():
            setattr(db_user_response, field, value)

        db.commit()
        db.refresh(db_user_response)
        return db_user_response

    @staticmethod
    def delete(db: Session, user_response_id: int) -> bool:
        db_user_response = UserResponseRepository.get_by_id(db, user_response_id)
        if not db_user_response:
            return False
            
        db.delete(db_user_response)
        db.commit()
        return True
