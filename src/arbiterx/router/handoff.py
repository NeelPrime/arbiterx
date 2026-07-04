"""Context handoff for serializing/deserializing conversation state between models."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Optional


@dataclass
class Message:
    """A single message in a conversation."""

    role: str  # "system", "user", "assistant"
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class ConversationState:
    """Complete conversation state that can be transferred between models.

    Captures messages, accumulated context, model metadata, and routing
    decisions so that a new model can continue seamlessly.
    """

    messages: list[Message] = field(default_factory=list)
    system_prompt: str = ""
    context_snippets: list[str] = field(default_factory=list)
    model_history: list[str] = field(default_factory=list)
    token_usage: dict[str, int] = field(default_factory=dict)
    task_metadata: dict[str, Any] = field(default_factory=dict)
    session_id: str = ""
    created_at: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)

    @property
    def message_count(self) -> int:
        """Return the number of messages in the conversation."""
        return len(self.messages)

    @property
    def total_tokens_used(self) -> int:
        """Sum of all token usage across models."""
        return sum(self.token_usage.values())

    def add_message(self, role: str, content: str, **metadata: Any) -> None:
        """Append a message to the conversation."""
        self.messages.append(Message(role=role, content=content, metadata=metadata))
        self.last_updated = time.time()

    def add_context(self, snippet: str) -> None:
        """Add a context snippet to the state."""
        if snippet not in self.context_snippets:
            self.context_snippets.append(snippet)
            self.last_updated = time.time()

    def record_model_usage(self, model: str, tokens: int) -> None:
        """Record token usage for a model."""
        self.model_history.append(model)
        self.token_usage[model] = self.token_usage.get(model, 0) + tokens
        self.last_updated = time.time()


class ContextHandoff:
    """Handles serialization and deserialization of conversation state for model handoffs.

    When routing escalates a task to a more capable model or falls back to
    an alternative, ContextHandoff ensures the full conversation context is
    preserved and formatted appropriately for the target model.

    Example:
        >>> handoff = ContextHandoff()
        >>> state = ConversationState(session_id="abc123")
        >>> state.add_message("user", "Explain monads")
        >>> serialized = handoff.serialize(state)
        >>> restored = handoff.deserialize(serialized)
        >>> restored.messages[0].content
        'Explain monads'
    """

    def serialize(self, state: ConversationState) -> str:
        """Serialize conversation state to a JSON string.

        Args:
            state: The ConversationState to serialize.

        Returns:
            JSON string representation of the state.
        """
        data = self._state_to_dict(state)
        return json.dumps(data, ensure_ascii=False, indent=None)

    def deserialize(self, payload: str) -> ConversationState:
        """Deserialize a JSON string back into ConversationState.

        Args:
            payload: JSON string previously produced by serialize().

        Returns:
            Reconstructed ConversationState.

        Raises:
            ValueError: If payload is malformed or missing required fields.
        """
        try:
            data = json.loads(payload)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid handoff payload: {e}") from e

        return self._dict_to_state(data)

    def prepare_handoff(
        self,
        state: ConversationState,
        target_model: str,
        reason: str = "",
        max_context_tokens: Optional[int] = None,
    ) -> ConversationState:
        """Prepare state for handoff to a new model.

        Optionally trims context to fit within the target model's token budget
        and records the handoff in model_history.

        Args:
            state: Current conversation state.
            target_model: Name of the model receiving the handoff.
            reason: Why the handoff is occurring.
            max_context_tokens: Optional token budget for the target model.

        Returns:
            A new ConversationState ready for the target model.
        """
        # Create a copy
        new_state = self.deserialize(self.serialize(state))

        # Record handoff metadata
        new_state.task_metadata["last_handoff_reason"] = reason
        new_state.task_metadata["handoff_target"] = target_model
        new_state.last_updated = time.time()

        # Trim context if budget specified
        if max_context_tokens is not None:
            new_state.context_snippets = self._trim_context(
                new_state.context_snippets, max_context_tokens
            )

        return new_state

    def _trim_context(self, snippets: list[str], max_tokens: int) -> list[str]:
        """Trim context snippets to fit within a token budget.

        Uses a rough 4-chars-per-token estimate. Keeps most recent snippets.
        """
        chars_budget = max_tokens * 4
        result: list[str] = []
        total_chars = 0

        # Keep most recent snippets (end of list) first
        for snippet in reversed(snippets):
            if total_chars + len(snippet) > chars_budget:
                break
            result.append(snippet)
            total_chars += len(snippet)

        result.reverse()
        return result

    def _state_to_dict(self, state: ConversationState) -> dict[str, Any]:
        """Convert state to a plain dictionary for serialization."""
        return {
            "messages": [
                {
                    "role": m.role,
                    "content": m.content,
                    "metadata": m.metadata,
                    "timestamp": m.timestamp,
                }
                for m in state.messages
            ],
            "system_prompt": state.system_prompt,
            "context_snippets": state.context_snippets,
            "model_history": state.model_history,
            "token_usage": state.token_usage,
            "task_metadata": state.task_metadata,
            "session_id": state.session_id,
            "created_at": state.created_at,
            "last_updated": state.last_updated,
        }

    def _dict_to_state(self, data: dict[str, Any]) -> ConversationState:
        """Reconstruct state from a plain dictionary."""
        messages = [
            Message(
                role=m["role"],
                content=m["content"],
                metadata=m.get("metadata", {}),
                timestamp=m.get("timestamp", 0.0),
            )
            for m in data.get("messages", [])
        ]

        return ConversationState(
            messages=messages,
            system_prompt=data.get("system_prompt", ""),
            context_snippets=data.get("context_snippets", []),
            model_history=data.get("model_history", []),
            token_usage=data.get("token_usage", {}),
            task_metadata=data.get("task_metadata", {}),
            session_id=data.get("session_id", ""),
            created_at=data.get("created_at", 0.0),
            last_updated=data.get("last_updated", 0.0),
        )
