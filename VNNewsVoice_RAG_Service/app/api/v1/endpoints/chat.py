import logging
import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.api.deps import get_orchestrator, get_conversation_repo
from app.utils.auth_user import get_current_user
from app.utils.limiter import limiter
from app.core.rag.orchestrator import RAGOrchestrator
from app.models.schemas import ChatRequest, ChatResponse
from app.repositories.conversation_repository import ConversationRepository

router = APIRouter(prefix="/chat")
logger = logging.getLogger(__name__)


class ConversationSummary(BaseModel):
    """Lightweight representation of a conversation for the sidebar."""

    id: str
    title: str  # First user message (truncated)
    updated_at: str  # ISO 8601 string for frontend sorting/display


class MessageDTO(BaseModel):
    """A single message for the frontend display."""

    role: str  # 'USER' or 'ASSISTANT'
    content: str
    created_at: str


@router.get("/conversations", response_model=List[ConversationSummary])
async def get_conversations(
    repo: ConversationRepository = Depends(get_conversation_repo),
    current_user: str = Depends(get_current_user),
):
    """Return all conversations for the authenticated user, newest first."""
    try:
        conversations = await repo.get_conversations_by_user(user_id=current_user)
        result: List[ConversationSummary] = []
        for conv in conversations:
            first_msg = await repo.get_first_user_message(conv.id)
            title = (
                (first_msg[:60] + "...")
                if first_msg and len(first_msg) > 60
                else (first_msg or "Cuộc trò chuyện mới")
            )
            result.append(
                ConversationSummary(
                    id=str(conv.id),
                    title=title,
                    updated_at=conv.updated_at.isoformat(),
                )
            )
        return result
    except Exception as e:
        logger.error(f"Error fetching conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/conversations/{conversation_id}/messages", response_model=List[MessageDTO]
)
async def get_conversation_messages(
    conversation_id: str,
    repo: ConversationRepository = Depends(get_conversation_repo),
    current_user: str = Depends(get_current_user),
):
    """Return all messages for a given conversation (ownership verified)."""
    try:
        turns = await repo.get_history(conversation_id=conversation_id, limit=100)
        return [
            MessageDTO(
                role=turn.role.value,
                content=turn.content,
                created_at=turn.created_at.isoformat(),
            )
            for turn in turns
        ]
    except Exception as e:
        logger.error(f"Error fetching messages for {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=ChatResponse, status_code=status.HTTP_200_OK)
@limiter.limit("60/minute")
@limiter.limit("1000/day")
@limiter.limit("5000/month")
async def chat(
    request: Request,
    body: ChatRequest,
    orchestrator: RAGOrchestrator = Depends(get_orchestrator),
    current_user: str = Depends(get_current_user),
):
    try:
        return await orchestrator.process_query(
            request=body, current_user=current_user, max_tokens=4094, temperature=0.4
        )
    except Exception as e:
        logger.error(f"Chat endpoints error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
@limiter.limit("60/minute")
@limiter.limit("1000/day")
@limiter.limit("5000/month")
async def chat_stream(
    request: Request,
    body: ChatRequest,
    orchestrator: RAGOrchestrator = Depends(get_orchestrator),
    current_user: str = Depends(get_current_user),
):
    """Streaming chat endpoint using Server-Sent Events (SSE).

    SSE format:
        data: <token>\n\n          <- text tokens streamed one by one
        data: [SOURCES]{...}\n\n   <- JSON array of sources at the end
        data: [DONE]\n\n           <- signals end of stream
    """

    def _sse_event(event_type: str, payload: object) -> str:
        # Always send JSON payload so newline characters inside text do not break SSE framing.
        return (
            f"event: {event_type}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"
        )

    async def event_generator():
        try:
            async for event in orchestrator.process_query_stream(
                request=body,
                current_user=current_user,
                max_tokens=4094,
                temperature=0.4,
            ):
                # Orchestrator yields text tokens and special [SOURCES]/[DONE]/[ERROR] markers.
                if event == "[DONE]":
                    yield _sse_event("done", {"ok": True})
                    return

                if event.startswith("[ERROR]"):
                    error_message = event.replace("[ERROR]", "", 1).strip()
                    yield _sse_event("error", {"message": error_message})
                    return

                if event.startswith("[SOURCES]"):
                    raw_sources = event.replace("[SOURCES]", "", 1)
                    try:
                        sources_payload = json.loads(raw_sources) if raw_sources else []
                    except json.JSONDecodeError:
                        logger.warning("Invalid sources payload from orchestrator")
                        sources_payload = []
                    yield _sse_event("sources", {"sources": sources_payload})
                    continue

                if event.startswith("[CONVERSATION_ID]"):
                    conversation_id = event.replace("[CONVERSATION_ID]", "", 1).strip()
                    yield _sse_event("conversation", {"id": conversation_id})
                    continue

                yield _sse_event("text", {"content": event})
        except Exception as e:
            logger.error(f"Error while processing streaming response: {e}")
            yield _sse_event("error", {"message": str(e)})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable Nginx buffering if behind proxy
        },
    )
