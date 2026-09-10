from typing import Annotated

from fastapi import APIRouter, Depends

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm import generate_answer

from app.ai.prompt import build_rag_prompt

from app.core.database import get_db

from app.ai.retriever import retrieve_ranked_children

from app.schemas.document import RetrievedContextResponse

from app.schemas.question import QuestionRequest, QuestionResponse

from app.services.document import get_document_by_id

from app.ai.query_prepare import prepare_queries

from app.services.conversation_service import create_conversation, get_recent_message, save_message

from app.utils.report import print_rag_report

from app.ai.parent_resolver import RetrievedContexts


router = APIRouter(prefix="/question", tags=["Question"])


SessionDB = Annotated[AsyncSession, Depends(get_db)]


# endpoints


def build_context(retrieved_chunks: RetrievedContexts) -> str:
    context_parts: list[str] = []

    for pos, chunk in enumerate(retrieved_chunks, start=1):
        context_parts.append(
            f"""
source {pos}
Filename: {chunk["filename"]}
Page: {chunk["page_number"]}
Chunk: {chunk["parent_index"]}

context:
{chunk["parent_text"]}
""".strip()
        )

    return "\n\n--\n\n".join(context_parts)



async def answer_question(request: QuestionRequest, db: AsyncSession, document_id: int | None = None) -> QuestionResponse:

    if request.conversation_id is None:
        conversation = await create_conversation(db)

        conversation_id = conversation.id

        recent_messages = []

    else:
        conversation_id = request.conversation_id

        recent_messages = await get_recent_message(
            db=db,
            conversation_id=conversation_id
        )

    standalone_question, queries = await prepare_queries(
        question=request.question,
        messages=recent_messages,
    )

    await save_message(
        db=db,
        conversation_id=conversation_id,
        role="user",
        content=request.question,
    )

    retrieved_contexts = await retrieve_ranked_children(
        question=standalone_question,
        category=request.category,
        db=db,
        top_k=request.top_k,
        retrieval_mode=request.retrieval_mode,
        document_id=document_id,
        queries=queries,
    )

    context = build_context(retrieved_contexts)

    prompt = build_rag_prompt(question=request.question, context=context)

    answer = await generate_answer(prompt)

    await save_message(
        db=db,
        conversation_id=conversation_id,
        role="assistant",
        content=answer,
    )

    used_contexts = [
        RetrievedContextResponse.model_validate(context)
        for context in retrieved_contexts
    ]

    response = QuestionResponse(
        question=request.question,
        rewritten_question=standalone_question,
        conversation_id=conversation_id,
        answer=answer,
        retrieval_mode=request.retrieval_mode,
        used_contexts=used_contexts
    )

    print_rag_report(response)

    return response



@router.post("/ask", response_model=QuestionResponse)
async def ask_all_documents(request: QuestionRequest, db: SessionDB) -> QuestionResponse:
    return await answer_question(
        request=request,
        db=db
    )



@router.post("/ask/{document_id}", response_model=QuestionResponse)
async def ask_one_document(document_id: int, request: QuestionRequest, db: SessionDB) -> QuestionResponse:
    await get_document_by_id(
        db=db,
        document_id=document_id
    )

    return await answer_question(
        request=request,
        db=db,
        document_id=document_id,
    )