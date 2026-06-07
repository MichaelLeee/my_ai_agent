"""Agent dependency types — shared between agent wrappers and tools."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Deps:
    """Dependencies for the assistant agent.

    These are passed to tools via RunContext.
    """

    user_id: str | None = None
    user_name: str | None = None
    kb_collection_names: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
