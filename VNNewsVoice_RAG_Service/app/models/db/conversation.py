from datetime import datetime
import uuid
from sqlalchemy import DateTime, ForeignKey, String, func, Enum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.db.base import Base
from app.models.enums import ConversationRole


class DBConversation(Base):
    __tablename__ = "conversation"

    id: Mapped[str] = mapped_column(String(255), primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    messages: Mapped[list["DBMessage"]] = relationship(
        "DBMessage", back_populates="conversation", cascade="all, delete-orphan"
    )


class DBMessage(Base):
    __tablename__ = "message"
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )
    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("conversation.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[ConversationRole] = mapped_column(
        Enum(ConversationRole, name="conversation_role_enum")
    )
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    conversation: Mapped["DBConversation"] = relationship(back_populates="messages")
