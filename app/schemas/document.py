from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    category: str
    created_at: datetime

class DocumentDetailResponse(DocumentResponse):
    status: str
    total_parent_chunks: int
    total_child_chunks: int

class DocumentUploadResponse(BaseModel):
    message: str
    document_id: int
    filename: str
    category: str
    task_id: str
    status: str

class DocumentDeleteResponse(BaseModel):
    message: str
    document_id: int

class RetrievedContextResponse(BaseModel):
    document_id: int
    filename: str
    page_number: int
    parent_index: int
    child_index: int
    parent_text: str
    rerank_score: float | None = None