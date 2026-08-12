from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_conversations: int
    total_chats: int