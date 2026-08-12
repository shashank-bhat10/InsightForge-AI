from sqlalchemy.orm import Session

from app.models.dataset import Dataset


def create_dataset(
    db: Session,
    filename: str,
    original_filename: str,
    file_type: str,
    file_size: int,
    file_path: str,
    user_id: int
):
    dataset = Dataset(
        filename=filename,
        original_filename=original_filename,
        file_type=file_type,
        file_size=file_size,
        file_path=file_path,
        user_id=user_id
    )

    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    return dataset


def get_all_datasets(
    db: Session,
    user_id: int
):
    return (
        db.query(Dataset)
        .filter(Dataset.user_id == user_id)
        .order_by(Dataset.created_at.desc())
        .all()
    )


def get_dataset(
    db: Session,
    dataset_id: int,
    user_id: int
):
    return (
        db.query(Dataset)
        .filter(
            Dataset.id == dataset_id,
            Dataset.user_id == user_id
        )
        .first()
    )


def delete_dataset(
    db: Session,
    dataset_id: int,
    user_id: int
):
    dataset = get_dataset(
        db,
        dataset_id,
        user_id
    )

    if dataset:
        db.delete(dataset)
        db.commit()

    return dataset