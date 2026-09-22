from fastapi import APIRouter, Depends

from app.core.deps import get_current_admin
from app.modules.admins.schemas import AdminOut
from app.modules.chat.schemas import ChatRequest, ChatResponse
from app.modules.chat.service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/message", response_model=ChatResponse)
async def send_message(
    payload: ChatRequest, _current_admin: AdminOut = Depends(get_current_admin)
) -> ChatResponse:
    reply = await ChatService().send_message(message=payload.message, history=payload.history)
    return ChatResponse(reply=reply)
