from app.core.celery_app import celery_app

import asyncio

from app.ai.chunker import chunk_document

from app.ai.embedding import create_embeddings

import os

from app.core.database import AsyncSessionLocal

from app.services.document import get_document_by_id, save_document_chunks

from app.services.pdf_service import extract_document



@celery_app.task(bind=True, max_retries=3)
def process_document(self, document_id: int, file_path: str,) -> None:

    asyncio.run(
        process_document_async(file_path=file_path, document_id=document_id)
    )

    clean_file(file_path=file_path)



async def process_document_async(
    document_id: int,
    file_path: str,
) -> None:

    async with AsyncSessionLocal() as db:

        document = await get_document_by_id(
            db=db,
            document_id=document_id,
        )

        document.status = "processing"
        await db.commit()
        await db.refresh(document)

        docling_doc = extract_document(file_path=file_path)

        parent_chunks, child_chunks = chunk_document(document=docling_doc)

        child_texts = [
            child["text"]
            for child in child_chunks
        ]

        child_embeddings = create_embeddings(child_texts)

        await save_document_chunks(
            document=document,
            parent_chunks=parent_chunks,
            child_chunks=child_chunks,
            child_embeddings=child_embeddings,
            db=db,
        )



def clean_file(file_path: str) -> None:
    if os.path.exists(file_path):
        os.remove(file_path)