from pathlib import Path
import uuid
from app.config.settings import settings
from app.services.dataset_service import load_dataset

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile
)
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User

from app.repositories.dataset_repository import (
    create_dataset,
    get_all_datasets,
    get_dataset,
    delete_dataset
)

from app.schemas.dataset import DatasetResponse


UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

router = APIRouter(
    prefix="/api/v1/datasets",
    tags=["Datasets"]
)


@router.post(
    "/",
    response_model=DatasetResponse
)
def upload_dataset(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    allowed_extensions = {
        ".csv",
        ".xlsx",
        ".xls"
    }

    extension = Path(file.filename or "").suffix.lower()

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="Only CSV and Excel files are allowed."
        )

    unique_filename = (
        f"{uuid.uuid4()}{extension}"
    )

    file_path = UPLOAD_DIR / unique_filename

    try:
        size = 0
        with open(file_path, "wb") as buffer:
            while chunk := file.file.read(65536):
                size += len(chunk)
                if size > settings.MAX_UPLOAD_BYTES:
                    raise HTTPException(status_code=413, detail="Upload exceeds the configured size limit.")
                buffer.write(chunk)
        load_dataset(str(file_path))
    except Exception:
        file_path.unlink(missing_ok=True)
        raise

    try:
        dataset = create_dataset(
            db=db,
            filename=unique_filename,
            original_filename=Path(file.filename).name[:255],
            file_type=extension,
            file_size=file_path.stat().st_size,
            file_path=str(file_path),
            user_id=current_user.id,
        )
    except Exception:
        db.rollback()
        file_path.unlink(missing_ok=True)
        raise

    return dataset


@router.get(
    "/",
    response_model=list[DatasetResponse]
)
def get_datasets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_all_datasets(
        db=db,
        user_id=current_user.id
    )


@router.get(
    "/{dataset_id}",
    response_model=DatasetResponse
)
def get_single_dataset(
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

    return dataset


@router.delete("/{dataset_id}")
def remove_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dataset = delete_dataset(
        db=db,
        dataset_id=dataset_id,
        user_id=current_user.id
    )

    if dataset is None:
        raise HTTPException(
            status_code=404,
            detail="Dataset not found"
        )

    Path(dataset.file_path).unlink(missing_ok=True)

    return {
        "success": True,
        "message": "Dataset deleted"
    }
