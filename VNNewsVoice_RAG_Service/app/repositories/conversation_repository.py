from datetime import datetime, timezone
from typing import List, cast
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.db.conversation import DBConversation, DBMessage
from app.models.domain.conversation import ConversationTurn
from app.models.enums import ConversationRole


class ConversationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_history(
        self, conversation_id: str, limit: int = 10
    ) -> List[ConversationTurn]:
        # Sort by created_at DESC to get newest `limit` messages first
        stmt = (
            select(DBMessage)
            .filter(DBMessage.conversation_id == conversation_id)
            .order_by(DBMessage.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        messages = list(result.scalars().all())

        # Reverse so the language model gets them in chronological order
        messages.reverse()

        return self._convert_to_conversation_turn(messages)

    def _convert_to_conversation_turn(
        self, db_message_list: List[DBMessage]
    ) -> List[ConversationTurn]:
        return [
            ConversationTurn(
                role=r.role
                if isinstance(r.role, ConversationRole)
                else ConversationRole(r.role),
                content=str(r.content),
                created_at=r.created_at,
            )
            for r in db_message_list
        ]

    async def get_conversations_by_user(
        self, user_id: str, limit: int = 30
    ) -> List[DBConversation]:
        """List conversations for a user, ordered by most recently active."""
        stmt = (
            select(DBConversation)
            .filter(DBConversation.user_id == user_id)
            .order_by(DBConversation.updated_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_first_user_message(self, conversation_id: str) -> str | None:
        """Fetch the very first USER message content as a conversation title preview."""
        stmt = (
            select(DBMessage)
            .filter(
                DBMessage.conversation_id == conversation_id,
                DBMessage.role == ConversationRole.USER,
            )
            .order_by(DBMessage.created_at.asc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        msg = result.scalar_one_or_none()
        return str(msg.content) if msg else None

    async def append_turn(
        self, conversation_id: str, user_id: str, role: ConversationRole, content: str
    ):
        # Find existing conversation
        stmt = select(DBConversation).filter(DBConversation.id == conversation_id)
        result = await self.session.execute(stmt)
        db_conversation = result.scalar_one_or_none()

        # UPSERT logic: If not exists, create it
        if not db_conversation:
            db_conversation = DBConversation(
                id=conversation_id,
                user_id=user_id,
            )
            self.session.add(db_conversation)
        else:
            # Check user ownership
            if cast(str, db_conversation.user_id) != user_id:
                raise ValueError("Conversation belongs to another user")
            # Touch updated_at timestamp
            db_conversation.updated_at = cast(datetime, datetime.now(timezone.utc))

        # Add message
        new_msg = DBMessage(conversation_id=conversation_id, role=role, content=content)
        self.session.add(new_msg)
        await self.session.commit()
