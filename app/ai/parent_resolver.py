from sqlalchemy import select

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.parentchunks import ParentChunks

from typing import Any


RetrievedContexts = dict[str, Any]


async def resolve_parent_chunks(
    ranked_children: list[RetrievedContexts],
    db: AsyncSession,
) -> list[RetrievedContexts]:
    if not ranked_children:
        return []

    parent_ids = {
        child["parent_id"]
        for child in ranked_children
    }

    result = await db.execute(select(ParentChunks).where(ParentChunks.id.in_(parent_ids)))

    parent_lookup = {
        parent.id: parent
        for parent in result.scalars()
    }

    resolved_contexts: list[RetrievedContexts] = []

    seen_parent_ids: set[int] = set()

    for child in ranked_children:
        parent_id = child["parent_id"]

        if parent_id in seen_parent_ids:
            continue

        seen_parent_ids.add(parent_id)

        parent = parent_lookup.get(parent_id)

        if parent is None:
            continue

        resolved_contexts.append(
    {
        "document_id": parent.document_id,
        "parent_text": parent.text,
        "page_number": parent.page_number,
        "parent_index": parent.parent_index,
        "child_index": child["child_index"],
        "filename": child["filename"],
        "rerank_score": child["rerank_score"]
    }
)

    return resolved_contexts