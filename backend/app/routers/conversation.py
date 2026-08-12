from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User

from app.repositories.conversation_repository import (
    create_conversation,
    get_all_conversations,
    get_conversation_by_id,
    update_conversation_title,
    delete_conversation
)

from app.schemas.conversation import (
    ConversationCreate,
    ConversationRename,
    ConversationResponse
)

router = APIRouter(
    prefix="/api/v1/conversations",
    tags=["Conversations"]
)


@router.post(
    "/",
    response_model=ConversationResponse
)
def create_new_conversation(
    request: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return create_conversation(
        db=db,
        user_id=current_user.id,
        title=request.title
    )


@router.get(
    "/",
    response_model=list[ConversationResponse]
)
def get_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_all_conversations(
        db=db,
        user_id=current_user.id
    )


@router.put(
    "/{conversation_id}",
    response_model=ConversationResponse
)
def rename_conversation(
    conversation_id: int,
    request: ConversationRename,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    conversation = get_conversation_by_id(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    return update_conversation_title(
        db=db,
        conversation=conversation,
        new_title=request.title
    )


@router.delete("/{conversation_id}")
def remove_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    conversation = delete_conversation(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id
    )

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    return {
        "success": True,
        "message": "Conversation deleted"
    }