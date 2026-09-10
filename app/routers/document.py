from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status, Form

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

from app.services.pdf_service import save_pdf

from app.services.document import get_all_documents, get_document_by_id, get_document_stats, delete_document, create_document

from app.tasks.document import process_document

from app.schemas.document import DocumentDeleteResponse, DocumentDetailResponse, DocumentResponse, DocumentUploadResponse


router = APIRouter(prefix="/document", tags=["Document"])


SessionDB = Annotated[AsyncSession, Depends(get_db)]


UPLOAD_DIR = "uploads"


# endpoints


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    db: SessionDB,
    file: Annotated[UploadFile, File(...)],
    category: Annotated[str, Form(...)]
) -> DocumentUploadResponse:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="file must have filename")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="file must be a pdf")

    try:
        file_path = save_pdf(file=file, upload_dir=UPLOAD_DIR)

        document = await create_document(
            db=db,
            filename=file.filename,
            category=category
        )

        task = process_document.delay(
            document_id=document.id,
            file_path=file_path,
        )

        return DocumentUploadResponse(
            message="Document queued for processing.",
            filename=file.filename,
            category=category,
            task_id=task.id,
            document_id=document.id,
            status=str(document.status)
        )

    finally:
        await file.close()



@router.get("", response_model=list[DocumentResponse])
async def list_documents(db: SessionDB) -> list[DocumentResponse]:
    documents = await get_all_documents(db=db)

    return [
        DocumentResponse.model_validate(document)
        for document in documents
    ]



@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document(db: SessionDB, document_id: int) -> DocumentDetailResponse:
    document = await get_document_by_id(db=db, document_id=document_id)

    (total_parent_chunks, total_child_chunks) = await get_document_stats(db=db, document_id=document_id)

    return DocumentDetailResponse(
        id=document.id,
        filename=document.filename,
        status=document.status,
        category=document.category,
        created_at=document.created_at,
        total_child_chunks=total_child_chunks,
        total_parent_chunks=total_parent_chunks,
    )



@router.delete("/{document_id}", response_model=DocumentDeleteResponse)
async def remove_document(db: SessionDB, document_id: int) -> DocumentDeleteResponse:
    result = await delete_document(db=db, document_id=document_id)

    return DocumentDeleteResponse(**result)