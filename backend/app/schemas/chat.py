from typing import Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=10000)
    dataset_id: Optional[int] = None
    conversation_id: Optional[int] = None


class ChatResponse(BaseModel):
    success: bool
    prompt: str
    response: str
    conversation_id: int
