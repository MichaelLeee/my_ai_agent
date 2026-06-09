"""Second Brain agent tools — create, search, and list notes via chat."""

from uuid import UUID

from pydantic_ai import RunContext

from app.agents.deps import Deps
from app.db.session import async_session_maker
from app.repositories import note as note_repo
from app.services.note import NoteService


async def create_note_tool(
    ctx: RunContext[Deps], title: str, content: str, tags: str = "",
) -> str:
    """Create a new note in the Second Brain.

    Use this when the user wants to save something for later reference.

    Args:
        title: A short title for the note.
        content: The full content of the note (markdown supported).
        tags: Comma-separated tags, e.g. "database,devops".

    Returns:
        Confirmation with the note ID.
    """
    user_id = ctx.deps.user_id
    if not user_id:
        return "Error: not authenticated."

    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else None

    async with async_session_maker() as db:
        service = NoteService(db)
        from app.schemas.note import NoteCreate
        data = NoteCreate(title=title, content=content, tags=tag_list or None)
        note = await service.create(user_id=UUID(user_id), data=data)
        return f"Note saved: '{note.title}' (id: {note.id}). Tags: {note.tags or 'none'}"


async def search_notes_tool(
    ctx: RunContext[Deps], query: str, limit: int = 5,
) -> str:
    """Search the Second Brain using semantic search.

    Use this when the user asks about something they might have saved.

    Args:
        query: Search query (natural language).
        limit: Max results (default 5).

    Returns:
        Formatted search results with snippets.
    """
    user_id = ctx.deps.user_id
    if not user_id:
        return "Error: not authenticated."

    async with async_session_maker() as db:
        service = NoteService(db)
        results = await service.search(user_id=UUID(user_id), query=query, limit=limit)

    if not results:
        return "No matching notes found."

    lines = [f"Found {len(results)} notes:\n"]
    for i, r in enumerate(results, 1):
        snippet = r["content"][:300].replace("\n", " ")
        lines.append(f"{i}. [{r['note_id']}] {snippet}...")
    return "\n".join(lines)


async def list_notes_tool(
    ctx: RunContext[Deps], tag: str = "", limit: int = 10,
) -> str:
    """List recent Second Brain notes, optionally filtered by tag.

    Use this when the user wants to see what they've saved.

    Args:
        tag: Optional tag filter.
        limit: Max notes (default 10).

    Returns:
        Formatted list of recent notes.
    """
    user_id = ctx.deps.user_id
    if not user_id:
        return "Error: not authenticated."

    async with async_session_maker() as db:
        items, total = await note_repo.list_for_user(
            db, user_id=UUID(user_id), skip=0, limit=limit, tag=tag or None)

    if not items:
        return "No notes found." + (f" (tag: '{tag}')" if tag else "")

    lines = [f"Your {len(items)} most recent notes ({total} total):\n"]
    for i, n in enumerate(items, 1):
        tags_str = ", ".join(n.tags) if n.tags else "—"
        lines.append(f"{i}. **{n.title}**  [{tags_str}]")
    return "\n".join(lines)


async def link_notes_tool(
    ctx: RunContext[Deps], source_title: str, target_title: str,
    link_type: str = "relates_to",
) -> str:
    """Link two notes together by title.

    Use this when notes are related. Choose the link type:
    - supports: one note supports or confirms the other
    - contradicts: the notes disagree or conflict
    - depends_on: one note depends on or follows from the other
    - relates_to: general connection (default)

    Args:
        source_title: Title of the first note.
        target_title: Title of the second note.
        link_type: Type of link (supports/contradicts/depends_on/relates_to).

    Returns:
        Confirmation of the link.
    """
    user_id = ctx.deps.user_id
    if not user_id:
        return "Error: not authenticated."

    from uuid import UUID
    from app.db.session import async_session_maker
    from app.repositories import note as note_repo
    from app.services.note import NoteService

    async with async_session_maker() as db:
        service = NoteService(db)
        items, _ = await note_repo.list_for_user(db, user_id=UUID(user_id), skip=0, limit=200)

        source = next((n for n in items if n.title.lower() == source_title.lower()), None)
        target = next((n for n in items if n.title.lower() == target_title.lower()), None)

        if not source:
            return f"Note not found: '{source_title}'"
        if not target:
            return f"Note not found: '{target_title}'"

        await service.link_notes(source_id=source.id, target_id=target.id,
                                 link_type=link_type)
        type_str = f" ({link_type})" if link_type != "relates_to" else ""
        return f"Linked '{source.title}' ↔ '{target.title}'{type_str}"


async def weekly_summary_tool(ctx: RunContext[Deps]) -> str:
    """Retrieve the most recent weekly summary of the user's Second Brain.

    Use this when the user asks for their weekly summary or wants an overview
    of what they worked on this week.
    """
    user_id = ctx.deps.user_id
    if not user_id:
        return "Error: not authenticated."

    from uuid import UUID
    from app.db.session import async_session_maker
    from app.repositories import note as note_repo

    async with async_session_maker() as db:
        items, _ = await note_repo.list_for_user(
            db, user_id=UUID(user_id), skip=0, limit=20, tag="summary")

    if not items:
        return "No weekly summary available yet. Summaries are generated every Sunday."

    latest = items[0]
    return f"Weekly Summary — {latest.title}\n\n{latest.content}"
