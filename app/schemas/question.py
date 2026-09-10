from enum import Enum

from pydantic import BaseModel, Field

from app.schemas.document import RetrievedContextResponse


class RetrievalMode(str, Enum):
    vector = "vector"
    keyword = "keyword"
    hybrid = "hybrid"

class QuestionRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    category: str | None = None
    top_k: int = Field(default=5, ge=1, le=20)
    retrieval_mode: RetrievalMode = RetrievalMode.hybrid
    conversation_id: int | None = None

class QuestionResponse(BaseModel):
    question: str
    rewritten_question: str
    conversation_id: int
    answer: str
    retrieval_mode: RetrievalMode
    used_contexts: list[RetrievedContextResponse]