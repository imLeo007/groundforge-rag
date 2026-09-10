from celery import Celery

from celery.signals import worker_process_init

from pathlib import Path

from app.services.pdf_service import warm_docling

from app.core.config import settings


celery_app = Celery(
    "rag_worker,",
    broker=settings.redis_broker,
    backend=settings.redis_backend,
    include=["app.tasks.document"]
)


@worker_process_init.connect
def initialize_docling(**kwargs) -> None:

    warm_pdf = (
        Path(__file__).resolve().parent.parent
        / "assets"
        / "sample.pdf"
    )

    warm_docling(str(warm_pdf))