from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User

from app.repositories.chat_repository import (
    save_chat,
    get_chat_history as get_chat_history_repo,
    delete_chat
)

from app.repositories.conversation_repository import (
    create_conversation,
    get_conversation_by_id
)

from app.repositories.dataset_repository import (
    get_dataset
)

from app.schemas.chat import ChatRequest, ChatResponse

from app.services.ai_service import (
    generate_ai_response,
    generate_dataset_ai_response
)


router = APIRouter(
    prefix="/api/v1/ai",
    tags=["AI"]
)


@router.get("/test")
def test_ai():
    return generate_ai_response(
        "Hello InsightForge AI"
    )


@router.post(
    "/chat",
    response_model=ChatResponse
)
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dataset = None

    # Validate dataset if one was selected
    if request.dataset_id is not None:
        dataset = get_dataset(
            db=db,
            dataset_id=request.dataset_id,
            user_id=current_user.id
        )

        if dataset is None:
            raise HTTPException(
                status_code=404,
                detail="Dataset not found"
            )

    # Reuse existing conversation if provided
    if request.conversation_id is not None:

        conversation = get_conversation_by_id(
            db=db,
            conversation_id=request.conversation_id,
            user_id=current_user.id
        )

        if conversation is None:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found"
            )

    # Otherwise create a new conversation
    else:

        conversation = create_conversation(
            db=db,
            user_id=current_user.id,
            title=request.prompt[:50]
        )

    # Get previous conversation messages
    previous_chats = get_chat_history_repo(
        db=db,
        conversation_id=conversation.id,
        user_id=current_user.id,
        skip=0,
        limit=50
    )

    conversation_history = [
        {
            "prompt": chat.prompt,
            "response": chat.response
        }
        for chat in previous_chats
    ]

    # Generate AI response
    if dataset is not None:

        result = generate_dataset_ai_response(
            prompt=request.prompt,
            file_path=dataset.file_path,
            conversation_history=conversation_history
        )

    else:

        result = generate_ai_response(
            prompt=request.prompt,
            conversation_history=conversation_history
        )

    if not result["success"]:
        raise HTTPException(
            status_code=500,
            detail=result["response"]
        )

    # Save current message and response
    save_chat(
        db=db,
        user_id=current_user.id,
        conversation_id=conversation.id,
        prompt=request.prompt,
        response=result["response"]
    )

    return {
        "success": True,
        "prompt": request.prompt,
        "response": result["response"],
        "conversation_id": conversation.id
    }


@router.get(
    "/history/{conversation_id}"
)
def get_chat_history(
    conversation_id: int,
    skip: int = Query(
        0,
        ge=0
    ),
    limit: int = Query(
        20,
        ge=1,
        le=100
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_chat_history_repo(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )


@router.delete(
    "/history/{chat_id}"
)
def delete_chat_history(
    chat_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    chat = delete_chat(
        db=db,
        chat_id=chat_id,
        user_id=current_user.id
    )

    if not chat:
        raise HTTPException(
            status_code=404,
            detail="Chat not found"
        )

    return {
        "success": True,
        "message": "Chat deleted"
    }