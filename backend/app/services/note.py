"""Note service — SQL + pgvector orchestration for the Second Brain."""

import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.repositories import note as note_repo
from app.schemas.note import NoteCreate, NoteUpdate

logger = logging.getLogger(__name__)
_embedding_service = None
_vector_store = None


def _get_embedding():
    global _embedding_service
    if _embedding_service is None:
        from app.core.config import settings
        from app.services.rag.embeddings import EmbeddingService
        _embedding_service = EmbeddingService(settings=settings.rag)
    return _embedding_service


def _get_vector_store():
    global _vector_store
    if _vector_store is None:
        from app.core.config import settings
        from app.services.rag.vectorstore import PgVectorStore
        _vector_store = PgVectorStore(
            settings=settings.rag, embedding_service=_get_embedding())
    return _vector_store


def _collection_for(user_id: UUID) -> str:
    return f"sb_{str(user_id).replace('-', '')}"


class NoteService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_for_user(self, *, user_id: UUID, skip: int = 0,
                            limit: int = 50, tag: str | None = None):
        return await note_repo.list_for_user(
            self.db, user_id=user_id, skip=skip, limit=limit, tag=tag)

    async def get_by_id(self, note_id: UUID, *, user_id: UUID):
        note = await note_repo.get_by_id(self.db, note_id=note_id)
        if not note or note.user_id != user_id:
            raise NotFoundError(
                message="Note not found",
                details={"note_id": str(note_id)})
        return note

    async def create(self, *, user_id: UUID, data: NoteCreate):
        note = await note_repo.create(
            self.db, user_id=user_id, title=data.title,
            content=data.content, tags=data.tags,
            is_archived=data.is_archived)
        try:
            await self._embed_and_store(note, user_id)
        except Exception:
            logger.exception("Failed to embed note %s", note.id)
        return note

    async def update(self, *, user_id: UUID, note_id: UUID, data: NoteUpdate):
        note = await self.get_by_id(note_id, user_id=user_id)
        update_data = data.model_dump(exclude_unset=True)
        if update_data.get("title") or update_data.get("content"):
            try:
                if note.document_id:
                    await _get_vector_store().delete_document(
                        _collection_for(user_id), note.document_id)
                await self._embed_and_store(note, user_id)
            except Exception:
                logger.exception("Failed to re-embed note %s", note.id)
        return await note_repo.update(
            self.db, db_note=note, update_data=update_data)

    async def delete(self, *, user_id: UUID, note_id: UUID) -> None:
        note = await self.get_by_id(note_id, user_id=user_id)
        try:
            if note.document_id:
                await _get_vector_store().delete_document(
                    _collection_for(user_id), note.document_id)
        except Exception:
            logger.exception("Failed to delete vector for note %s", note.id)
        await note_repo.delete_note(self.db, db_note=note)

    async def search(self, *, user_id: UUID, query: str, limit: int = 5):
        try:
            results = await _get_vector_store().search(
                _collection_for(user_id), query, limit=limit)
            return [{
                "content": r.content,
                "score": round(r.score, 4),
                "note_id": r.metadata.get("note_id", r.parent_doc_id),
            } for r in results]
        except Exception:
            logger.exception("Vector search failed for user %s", user_id)
            return []

    async def _embed_and_store(self, note, user_id: UUID) -> None:
        from app.services.rag.models import (
            Document, DocumentMetadata, DocumentPage, DocumentPageChunk)

        text = f"{note.title}\n\n{note.content}"
        store = _get_vector_store()
        collection = _collection_for(user_id)
        doc_id = str(note.id)

        doc = Document(
            id=doc_id,
            pages=[DocumentPage(page_num=1, content=text)],
            chunked_pages=[
                DocumentPageChunk(
                    page_num=1, content=text,
                    chunk_content=text, chunk_num=1,
                )
            ],
            metadata=DocumentMetadata(
                filename=f"note_{note.id}",
                filesize=len(text.encode()),
                filetype="text/plain",
                additional_info={"note_id": str(note.id), "title": note.title},
            ),
        )
        await store._ensure_collection(collection)
        await store.insert_document(collection, doc)
        note.document_id = doc_id
        await note_repo.update(self.db, db_note=note,
                               update_data={"document_id": doc_id})

    # ── Note Links ──────────────────────────────────────────

    async def link_notes(self, *, source_id: UUID, target_id: UUID,
                         link_type: str = "relates_to"):
        await self.get_by_id(source_id, user_id=UUID(int=0))
        await self.get_by_id(target_id, user_id=UUID(int=0))
        return await note_repo.create_link(
            self.db, source_note_id=source_id, target_note_id=target_id,
            link_type=link_type)

    async def unlink_notes(self, *, source_id: UUID, target_id: UUID) -> bool:
        return await note_repo.delete_link(
            self.db, source_note_id=source_id, target_note_id=target_id)

    async def get_links(self, *, note_id: UUID) -> list:
        return await note_repo.list_links(self.db, note_id=note_id)
