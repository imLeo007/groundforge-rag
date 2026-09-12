from fastapi import FastAPI

from contextlib import asynccontextmanager

from app.ai.reranker import load_reranker

from app.routers.question import router as question_router

from app.routers.document import router as document_router


@asynccontextmanager
async def lifespan(app: FastAPI):

    load_reranker()

    yield

app = FastAPI(title="GroundForge", version="5.0.0", lifespan=lifespan)


app.include_router(document_router)

app.include_router(question_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "message": "GroundForge RAG is running."
    }