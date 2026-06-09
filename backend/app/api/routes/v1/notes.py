"""Note API routes for the Second Brain."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.deps import CurrentUser, NoteSvc
from app.schemas.note import NoteCreate, NoteList, NoteRead, NoteUpdate
from app.schemas.note_link import NoteLinkCreate

router = APIRouter(prefix="/notes", tags=["notes"])


@router.get("", response_model=NoteList)
async def list_notes(
    service: NoteSvc, user: CurrentUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    tag: str | None = Query(None),
) -> Any:
    items, total = await service.list_for_user(
        user_id=user.id, skip=skip, limit=limit, tag=tag)
    return NoteList(items=items, total=total)


@router.post("", response_model=NoteRead, status_code=status.HTTP_201_CREATED)
async def create_note(
    data: NoteCreate, service: NoteSvc, user: CurrentUser,
) -> Any:
    return await service.create(user_id=user.id, data=data)


@router.get("/{note_id}", response_model=NoteRead)
async def get_note(
    note_id: UUID, service: NoteSvc, user: CurrentUser,
) -> Any:
    return await service.get_by_id(note_id, user_id=user.id)


@router.patch("/{note_id}", response_model=NoteRead)
async def update_note(
    note_id: UUID, data: NoteUpdate, service: NoteSvc, user: CurrentUser,
) -> Any:
    return await service.update(user_id=user.id, note_id=note_id, data=data)


@router.delete(
    "/{note_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_note(
    note_id: UUID, service: NoteSvc, user: CurrentUser,
) -> None:
    await service.delete(user_id=user.id, note_id=note_id)


@router.post("/search", response_model=None)
async def search_notes(
    service: NoteSvc, user: CurrentUser,
    query: str = Query(..., min_length=1),
    limit: int = Query(5, ge=1, le=20),
) -> Any:
    return await service.search(user_id=user.id, query=query, limit=limit)


@router.post("/{note_id}/links", response_model=None, status_code=status.HTTP_201_CREATED)
async def link_notes(
    note_id: UUID,
    data: NoteLinkCreate,
    service: NoteSvc,
    user: CurrentUser,
) -> Any:
    await service.get_by_id(note_id, user_id=user.id)
    await service.get_by_id(data.target_note_id, user_id=user.id)
    return await service.link_notes(source_id=note_id, target_id=data.target_note_id)


@router.delete("/{note_id}/links/{target_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def unlink_notes(
    note_id: UUID, target_id: UUID, service: NoteSvc, user: CurrentUser,
) -> None:
    await service.get_by_id(note_id, user_id=user.id)
    await service.unlink_notes(source_id=note_id, target_id=target_id)


@router.get("/{note_id}/links", response_model=None)
async def get_links(
    note_id: UUID, service: NoteSvc, user: CurrentUser,
) -> Any:
    await service.get_by_id(note_id, user_id=user.id)
    return await service.get_links(note_id=note_id)


@router.get("/graph", response_model=None)
async def get_graph(
    service: NoteSvc, user: CurrentUser,
) -> Any:
    items, _ = await service.list_for_user(user_id=user.id, skip=0, limit=200)
    nodes = [{"id": str(n.id), "title": n.title, "tags": n.tags or []} for n in items]
    node_ids = {n["id"] for n in nodes}
    edges = []
    for n in items:
        links = await service.get_links(note_id=n.id)
        for link in links:
            sid, tid = str(link.source_note_id), str(link.target_note_id)
            if sid in node_ids and tid in node_ids and sid < tid:
                edges.append({
                    "source": sid, "target": tid,
                    "link_type": getattr(link, "link_type", "relates_to"),
                })
    return {"nodes": nodes, "edges": edges}
