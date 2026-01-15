"""Domain models for session management."""

from dataclasses import dataclass, field
from datetime import datetime
from pydantic import BaseModel, Field
import uuid


class ConversationTurn(BaseModel):
    """A single turn in a conversation."""
    
    user_message: str
    assistant_message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    confidence: float = 0.0


@dataclass
class SessionState:
    """Immutable session state for Gradio."""
    
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    conversation_history: list[tuple[str, str]] = field(default_factory=list)
    context_chunks: list[str] = field(default_factory=list)
    last_confidence: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def with_message(self, user: str, assistant: str) -> "SessionState":
        """Return new state with added message (immutable)."""
        return SessionState(
            session_id=self.session_id,
            conversation_history=[*self.conversation_history, (user, assistant)],
            context_chunks=self.context_chunks,
            last_confidence=self.last_confidence,
            created_at=self.created_at,
        )
