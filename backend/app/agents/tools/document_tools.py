"""Document tools — read full documents from the knowledge base."""

from pydantic_ai import RunContext

from app.agents.deps import Deps
from app.core.config import settings
from app.services.rag.retrieval import RetrievalService
from app.services.rag.vectorstore import PgVectorStore


_retrieval_service = None


def _get_retrieval():
    global _retrieval_service
    if _retrieval_service is None:
        from app.services.rag.embeddings import EmbeddingService
        embedder = EmbeddingService(settings=settings.rag)
        store = PgVectorStore(settings=settings.rag, embedding_service=embedder)
        _retrieval_service = RetrievalService(
            store=store, settings=settings.rag)
    return _retrieval_service


async def read_document(ctx: RunContext[Deps], doc_id: str) -> str:
    """Read the full content of a knowledge base document by its ID.

    Use when search_documents returns relevant results but you need the
    full document text to answer the user's question properly. Call this
    before citing specific claims or making detailed references.

    Args:
        doc_id: The document ID from search_documents results (parent_doc_id).

    Returns:
        Full document text with metadata, or an error.
    """
    user_id = ctx.deps.user_id
    if not user_id:
        return "Error: not authenticated."

    try:
        retrieval = _get_retrieval()
        results = await retrieval.retrieve_by_document(
            document_id=doc_id,
            query="*",  # Get all chunks
            limit=50,
            min_score=-1.0,  # No filtering
        )

        if not results:
            return f"Document '{doc_id}' not found in the knowledge base."

        chunks = []
        for r in results:
            meta = r.metadata
            filename = meta.get("filename", doc_id)
            page = meta.get("page_num", "?")
            chunks.append(f"[p{page}] {r.content}")

        filename = results[0].metadata.get("filename", doc_id)
        return f"**{filename}** ({len(chunks)} chunks)\n---\n" + "\n".join(chunks)

    except Exception as e:
        return f"Failed to read document: {e}"
