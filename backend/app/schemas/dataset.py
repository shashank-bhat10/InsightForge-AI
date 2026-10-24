from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DatasetResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_type: str
    file_size: int
    file_path: str
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
