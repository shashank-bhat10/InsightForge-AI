from typing import Optional

from pydantic import BaseModel


class ChatRequest(BaseModel):
    prompt: str
    dataset_id: Optional[int] = None
    conversation_id: Optional[int] = None


class ChatResponse(BaseModel):
    success: bool
    prompt: str
    response: str
    conversation_id: int