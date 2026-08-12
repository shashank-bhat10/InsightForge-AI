from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User

from app.repositories.dataset_repository import get_dataset

from app.services.analytics_service import (
    get_dataset_summary,
    get_dataset_statistics,
    get_dataset_insights,
    get_grouped_analysis,
    get_dataset_quality,
    get_advanced_analytics,
)

from app.services.dataset_service import (
    get_dataset_preview
)

router = APIRouter(
    prefix="/api/v1/analytics",
    tags=["Analytics"]
)


@router.get("/{dataset_id}/summary")
def dataset_summary(
    dataset_id: int,
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

    return get_dataset_summary(dataset.file_path)


@router.get("/{dataset_id}/preview")
def dataset_preview(
    dataset_id: int,
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

    return get_dataset_preview(dataset.file_path)


@router.get("/{dataset_id}/statistics")
def dataset_statistics(
    dataset_id: int,
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

    return get_dataset_statistics(dataset.file_path)


@router.get("/{dataset_id}/insights")
def dataset_insights(
    dataset_id: int,
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

    return get_dataset_insights(dataset.file_path)


@router.get("/{dataset_id}/grouped-analysis")
def dataset_grouped_analysis(
    dataset_id: int,
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

    return get_grouped_analysis(dataset.file_path)


@router.get("/{dataset_id}/quality")
def dataset_quality(
    dataset_id: int,
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

    return get_dataset_quality(dataset.file_path)


@router.get("/{dataset_id}/advanced")
def dataset_advanced_analytics(
    dataset_id: int,
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

    return get_advanced_analytics(dataset.file_path)