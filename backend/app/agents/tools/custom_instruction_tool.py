"""Agent tool for retrieving the user's active custom instructions.

This tool is called by the agent to check if the user has set any
custom behavior rules that should override the default system prompt.
"""

from pydantic_ai import RunContext

from app.agents.deps import Deps
from app.repositories import custom_instruction as instruction_repo
from app.db.session import async_session_maker


def _build_instruction_prompt(instructions: list) -> str:
    """Combine active instructions into a prompt block."""
    if not instructions:
        return ""
    blocks = [f"[Instruction: {inst.name}]\n{inst.content}" for inst in instructions]
    return "\n\n".join(blocks)


async def get_active_instructions(ctx: RunContext[Deps]) -> str:
    """Retrieve the current user's active custom instructions.

    Returns:
        The active instructions as a prompt string, or empty string if none.
    """
    user_id = ctx.deps.user_id
    if not user_id:
        return ""

    try:
        from uuid import UUID
        uid = UUID(user_id) if isinstance(user_id, str) else user_id
        async with async_session_maker() as db:
            instructions = await instruction_repo.get_active_for_user(db, user_id=uid)
            return _build_instruction_prompt(instructions)
    except Exception:
        return ""
