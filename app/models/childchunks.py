from datetime import datetime

from sqlalchemy import Integer, Text, DateTime, ForeignKey, func, UniqueConstraint, Computed

from sqlalchemy.orm import Mapped, mapped_column, relationship

from sqlalchemy.dialects.postgresql import TSVECTOR

from pgvector.sqlalchemy import Vector

from app.core.config import settings

from app.core.database import Base

from typing import Any, TYPE_CHECKING


if TYPE_CHECKING:
    from app.models.parentchunks import ParentChunks


class ChildChunks(Base):

    __tablename__ = "child_chunks"

    __table_args__ = (
        UniqueConstraint(
            "parent_id",
            "child_index",
            name="uq_child_chunks_pos",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    parent_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "parent_chunks.id",
            ondelete="CASCADE"
        ),
        nullable=False,
    )

    text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    child_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    embeddings: Mapped[Any] = mapped_column(
        Vector(settings.embedding_dimension),
        nullable=False,
    )

    search_vector: Mapped[Any] = mapped_column(
        TSVECTOR,
        Computed(
            "to_tsvector('english', coalesce(text, ''))",
            persisted=True,
        ),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    parent_chunks: Mapped["ParentChunks"] = relationship(
        back_populates="child_chunks"
    )