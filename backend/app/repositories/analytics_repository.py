from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.chat import Chat
from app.models.conversation import Conversation


def get_dashboard_stats(
    db: Session,
    user_id: int
):
    total_conversations = (
        db.query(func.count(Conversation.id))
        .filter(Conversation.user_id == user_id)
        .scalar()
    )

    total_chats = (
        db.query(func.count(Chat.id))
        .filter(Chat.user_id == user_id)
        .scalar()
    )

    return {
        "total_conversations": total_conversations,
        "total_chats": total_chats
    }