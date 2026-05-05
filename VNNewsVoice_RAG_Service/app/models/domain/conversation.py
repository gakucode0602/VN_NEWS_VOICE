from datetime import datetime, timezone
from typing import List
from pydantic import BaseModel, Field

from app.models.enums import ConversationRole


class ConversationTurn(BaseModel):
    role: ConversationRole
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Conversation(BaseModel):
    conversation_id: str
    user_id: str
    turns: List[ConversationTurn] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
