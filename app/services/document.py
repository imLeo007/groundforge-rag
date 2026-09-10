from typing import Any

from fastapi import HTTPException

from sqlalchemy import func, select

from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.orm import selectinload

from app.models.document import Document

from app.ai.chunker import ChildChunk, ParentChunk

from app.models.childchunks import ChildChunks

from app.models.parentchunks import ParentChunks



async def create_document(db: AsyncSession, filename: str, category: str) -> Document:
    document = Document(
        filename=filename,
        category=category,
        status="queued"
    )

    db.add(document)

    await db.commit()

    await db.refresh(document)

    return document


# Save Document Chunks: Saves both Parent & Child chunks into db given by Hybrid Chunker.


async def save_document_chunks(
    db: AsyncSession,
    document: Document,
    parent_chunks: list[ParentChunk],
    child_chunks: list[ChildChunk],
    child_embeddings: Any,
) -> Document:
    if len(child_chunks) != len(child_embeddings):
        raise ValueError("The number of chunks must be equal to number of embeddings")

    parent_models: list[ParentChunks] = []

    for parent_chunk in parent_chunks:
        parent_model = ParentChunks(
            document_id=document.id,
            text=parent_chunk["text"],
            heading=parent_chunk["heading"],
            page_number=parent_chunk["page_number"],
            parent_index=parent_chunk["parent_index"],
        )

        parent_models.append(parent_model)

    db.add_all(parent_models)

    await db.flush()

    parent_lookup: dict[tuple[int, int], ParentChunks] = {
        (
            parent.page_number,
            parent.parent_index,
        ): parent
        for parent in parent_models
    }

    child_models: list[ChildChunks] = []

    for child_chunk, embedding in zip(child_chunks, child_embeddings, strict=True):
        parent_key = (
            child_chunk["page_number"],
            child_chunk["parent_index"],
        )

        parent = parent_lookup.get(parent_key)

        if parent is None:
            raise ValueError("A child chunk not matched to it's parent chunk")

        child_model = ChildChunks(
            parent_id=parent.id,
            text=child_chunk["text"],
            child_index=child_chunk["child_index"],
            embeddings=embedding,
        )

        child_models.append(child_model)

    db.add_all(child_models)

    document.status = "ready"

    await db.commit()

    await db.refresh(document)

    return document



async def get_all_documents(db: AsyncSession) -> list[Document]:
    result = await db.execute(select(Document))

    return result.scalars().all()



async def get_document_by_id(document_id: int, db: AsyncSession) -> Document:

    result = await db.execute(
        select(Document).options(
            selectinload(Document.parent_chunks).selectinload(ParentChunks.child_chunks)
        ).where(Document.id == document_id)
    )

    document = result.scalar_one_or_none()

    if document is None:
        raise HTTPException(status_code=404, detail="Document was not found")

    return document



async def get_document_stats(document_id: int, db: AsyncSession) -> tuple[int, int]:

    parent_chunk_result = await db.execute(
            select(func.count(ParentChunks.id)
        ).where(ParentChunks.document_id == document_id)
    )

    child_chunks = await db.execute(
        select(func.count(ChildChunks.id))
        .join(ParentChunks, ParentChunks.id == ChildChunks.parent_id)
        .where(ParentChunks.document_id == document_id)
    )

    total_parent = int(parent_chunk_result.scalar_one())

    total_child = int(child_chunks.scalar_one())

    return total_parent, total_child



async def delete_document(db: AsyncSession, document_id: int) -> dict[str, int | str]:
    document = await get_document_by_id(db=db, document_id=document_id)

    await db.delete(document)

    await db.commit()

    return {
        "message": "Document was deleted",
        "document_id": document_id
    }