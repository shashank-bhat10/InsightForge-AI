from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User

from app.repositories.dataset_repository import get_dataset

from app.services.ml_service import (
    train_and_compare_models
)


router = APIRouter(
    prefix="/api/v1/ml",
    tags=["Machine Learning"]
)


class MLTrainRequest(BaseModel):
    target_column: str
    problem_type: str = "auto"


@router.post("/{dataset_id}/train")
def train_models(
    dataset_id: int,
    request: MLTrainRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    dataset = get_dataset(
        db=db,
        dataset_id=dataset_id,
        user_id=current_user.id
    )

    if dataset is None:
        raise HTTPException(
            status_code=404,
            detail="Dataset not found"
        )

    try:

        result = train_and_compare_models(
            file_path=dataset.file_path,
            target_column=request.target_column,
            problem_type=request.problem_type
        )

        return result

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )