from sqlalchemy.orm import Session

from app.models.chat import Chat


def save_chat(
    db: Session,
    user_id: int,
    conversation_id: int,
    prompt: str,
    response: str
):
    chat = Chat(
        user_id=user_id,
        conversation_id=conversation_id,
        prompt=prompt,
        response=response
    )

    db.add(chat)
    db.commit()
    db.refresh(chat)

    return chat


def get_all_chats(
    db: Session,
    conversation_id: int
):
    return (
        db.query(Chat)
        .filter(Chat.conversation_id == conversation_id)
        .order_by(Chat.created_at.asc())
        .all()
    )


def get_chat_by_id(
    db: Session,
    chat_id: int,
    user_id: int
):
    return (
        db.query(Chat)
        .filter(
            Chat.id == chat_id,
            Chat.user_id == user_id
        )
        .first()
    )


def get_chat_history(
    db: Session,
    conversation_id: int,
    user_id: int,
    skip: int = 0,
    limit: int = 20
):
    return (
        db.query(Chat)
        .filter(
            Chat.conversation_id == conversation_id,
            Chat.user_id == user_id
        )
        .order_by(Chat.created_at.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def delete_chat(
    db: Session,
    chat_id: int,
    user_id: int
):
    chat = get_chat_by_id(
        db,
        chat_id,
        user_id
    )

    if chat:
        db.delete(chat)
        db.commit()

    return chat