from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User

from app.repositories.dataset_repository import get_dataset

from app.services.forecast_service import (
    generate_forecast,
    get_forecast_columns,
)

router = APIRouter(
    prefix="/api/v1/forecast",
    tags=["Forecasting"],
)


class ForecastRequest(BaseModel):
    date_column: str
    target_column: str
    periods: int = Field(default=12, ge=1, le=60)
    frequency: str = "auto"


@router.get("/{dataset_id}/columns")
def forecast_columns(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dataset = get_dataset(
        db=db,
        dataset_id=dataset_id,
        user_id=current_user.id,
    )

    if dataset is None:
        raise HTTPException(
            status_code=404,
            detail="Dataset not found",
        )

    try:
        return get_forecast_columns(dataset.file_path)
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


@router.post("/{dataset_id}/predict")
def forecast_dataset(
    dataset_id: int,
    request: ForecastRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dataset = get_dataset(
        db=db,
        dataset_id=dataset_id,
        user_id=current_user.id,
    )

    if dataset is None:
        raise HTTPException(
            status_code=404,
            detail="Dataset not found",
        )

    try:
        return generate_forecast(
            file_path=dataset.file_path,
            date_column=request.date_column,
            target_column=request.target_column,
            periods=request.periods,
            frequency=request.frequency,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )