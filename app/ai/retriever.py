from typing import Any

from app.ai.reranker import rerank_chunks

import re

from sqlalchemy import func, select

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embedding import create_question_embeddings

from app.ai.parent_resolver import resolve_parent_chunks

from app.schemas.question import RetrievalMode

from app.models.document import Document

from app.models.childchunks import ChildChunks

from app.models.parentchunks import ParentChunks



RetrievedChunks = dict[str, Any]


# Retrieve Vector Chunks: Vector search across db, ranks the relevant chunks.


async def retrieve_vector_chunks(
    db: AsyncSession,
    question: str,
    candidate_k: int,
    document_id: int | None = None,
    category: str | None = None,
) -> list[RetrievedChunks]:
    question_embeddings = create_question_embeddings(question)

    vector_score = (
        1 - ChildChunks.embeddings.cosine_distance(question_embeddings)
    ).label("vector_score")

    query = (
        select(
            ChildChunks.id.label("chunk_id"),
            ChildChunks.parent_id,
            ChildChunks.text,
            ChildChunks.child_index,
            ParentChunks.document_id,
            ParentChunks.page_number,
            ParentChunks.parent_index,
            Document.filename,
            vector_score
        ).join(ParentChunks, ParentChunks.id == ChildChunks.parent_id)
        .join(Document, Document.id == ParentChunks.document_id)
    )

    if category is not None:
        query = query.where(
            Document.category == category
        )

    if document_id is not None:
        query = query.where(
            ParentChunks.document_id == document_id
        )

    query = (
        query.order_by(
            ChildChunks.embeddings.cosine_distance(question_embeddings)
        ).limit(candidate_k)
    )

    result = await db.execute(query)

    return [
        {
            "chunk_id": row.chunk_id,
            "document_id": row.document_id,
            "parent_id": row.parent_id,
            "parent_index": row.parent_index,
            "child_index": row.child_index,
            "filename": row.filename,
            "text": row.text,
            "page_number": row.page_number,
            "vector_score": float(row.vector_score),
            "keyword_score": None,
            "fusion_score": None,
            "rerank_score": None,
        }

        for row in result.all()
    ]



# Retrieve Keyword Chunks: Keyword Search across the db, ranks relevant chunks.


async def retrieve_keyword_chunks(
    question: str,
    db: AsyncSession,
    candidate_k: int,
    document_id: int | None = None,
    category: str | None = None,
) -> list[RetrievedChunks]:
    cleaned = [
        term
        for term in re.findall(r"[A-Za-z0-9]+", question.lower())
    ]

    if not cleaned:
        return []

    tsquery_text = " OR ".join(cleaned)

    search_query = func.websearch_to_tsquery("english", tsquery_text)

    keyword_score = func.ts_rank_cd(
        ChildChunks.search_vector,
        search_query
    ).label("keyword_score")

    query = (
        select(
            ChildChunks.id.label("chunk_id"),
            ChildChunks.text,
            ChildChunks.child_index,
            ChildChunks.parent_id,
            ParentChunks.parent_index,
            ParentChunks.document_id,
            ParentChunks.page_number,
            Document.filename,
            keyword_score
        ).join(ParentChunks, ParentChunks.id == ChildChunks.parent_id)
        .join(Document, Document.id == ParentChunks.document_id)
        .where(
            ChildChunks.search_vector.op("@@")(search_query)
        )
    )

    if category is not None:
        query = query.where(Document.category == category)

    if document_id is not None:
        query = query.where(ParentChunks.document_id == document_id)

    query = (
        query.order_by(keyword_score.desc()).limit(candidate_k)
    )

    result = await db.execute(query)

    return [
        {
            "chunk_id": row.chunk_id,
            "document_id": row.document_id,
            "parent_id": row.parent_id,
            "parent_index": row.parent_index,
            "child_index": row.child_index,
            "filename": row.filename,
            "text": row.text,
            "page_number": row.page_number,
            "vector_score": None,
            "keyword_score": float(row.keyword_score),
            "fusion_score": None,
            "rerank_score": None,
        }

        for row in result.all()
    ]



# Fuse Rankings: RRF Fusion, Combining the scores of both keyword and vector results.


def fuse_rankings(
    vector_results: list[RetrievedChunks],
    keyword_results: list[RetrievedChunks],
    top_k: int,
    rrf_constant: int = 60,
) -> list[RetrievedChunks]:
    fused_results: dict[int, RetrievedChunks] = {}

    for rank, item in enumerate(vector_results, start=1):
        chunk_id = item["chunk_id"]

        fused_results[chunk_id] = item.copy()

        fused_results[chunk_id]["fusion_score"] = 1 /(rrf_constant + rank)

    for rank, item in enumerate(keyword_results, start=1):
        chunk_id = item["chunk_id"]

        rrf_score = (1/(rrf_constant + rank))

        if chunk_id in fused_results:

            fused_results[chunk_id]["keyword_score"] = item["keyword_score"]

            fused_results[chunk_id]["fusion_score"] += rrf_score

        else:

            fused_results[chunk_id] = item.copy()

            fused_results[chunk_id]["fusion_score"] = rrf_score

    ranked = sorted(
        fused_results.values(),
        key=lambda item: float(item["fusion_score"] or 0),
        reverse=True
    )

    return ranked[:top_k]



# Deduplicate Candidates: Filters repeated chunks.


def deduplicate_candidates(
    candidates: list[RetrievedChunks],
) -> list[RetrievedChunks]:

    unique_candidates: dict[int, RetrievedChunks] = {}

    for candidate in candidates:
        child_id = candidate["chunk_id"]

        if child_id not in unique_candidates:
            unique_candidates[child_id] = candidate

    return list(unique_candidates.values())



# Retrieve Muti Query Candidates: Multi query retrieval, gives a list of retrieved chunks.


async def retrieve_multi_query_candidates(
    queries: list[str],
    db: AsyncSession,
    candidate_k: int,
    document_id: int | None = None,
    category: str | None = None,
) -> list[RetrievedChunks]:

    all_candidates: list[RetrievedChunks] = []

    for query in queries:
        vector_results = await retrieve_vector_chunks(
            question=query,
            db=db,
            candidate_k=candidate_k,
            document_id=document_id,
            category=category
        )

        keyword_results = await retrieve_keyword_chunks(
            question=query,
            db=db,
            candidate_k=candidate_k,
            document_id=document_id,
            category=category
        )

        fused = fuse_rankings(
            vector_results=vector_results,
            keyword_results=keyword_results,
            top_k=candidate_k
        )

        all_candidates.extend(fused)

    return deduplicate_candidates(all_candidates)



# Retrieve Ranked Children: Main function combines retrieval with multi query and reranks them. Gives back relevant parents.


async def retrieve_ranked_children(
    question: str,
    db: AsyncSession,
    top_k: int,
    retrieval_mode: RetrievalMode = RetrievalMode.hybrid,
    document_id: int | None = None,
    category: str | None = None,
    queries: list[str] | None = None,
) -> list[RetrievedChunks]:
    candidate_k = max(top_k * 3, 10)

    if retrieval_mode == RetrievalMode.vector:

        result = await retrieve_vector_chunks(
            question=question,
            document_id=document_id,
            db=db,
            category=category,
            candidate_k=candidate_k,
        )

    elif retrieval_mode == RetrievalMode.keyword:

        result = await retrieve_keyword_chunks(
            question=question,
            document_id=document_id,
            category=category,
            candidate_k=candidate_k,
        )

    else:

        fused_results = await retrieve_multi_query_candidates(
            db=db,
            candidate_k=candidate_k,
            document_id=document_id,
            category=category,
            queries=queries or [question],
        )

        ranked_children = rerank_chunks(
            question=question,
            chunks=fused_results,
            top_k=top_k,
        )

        result = await resolve_parent_chunks(ranked_children=ranked_children, db=db)

    return result