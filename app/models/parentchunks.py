from sqlalchemy import Integer, ForeignKey, Text, func, DateTime, UniqueConstraint

from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import TYPE_CHECKING

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.childchunks import ChildChunks


class ParentChunks(Base):

    __tablename__ = "parent_chunks"

    __table_args__ = (
        UniqueConstraint(
            "document_id",
            "page_number",
            "parent_index",
            name="uq_parent_chunk_pos"
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    document_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("document.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    heading: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    parent_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    page_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    child_chunks: Mapped[list["ChildChunks"]] = relationship(
        back_populates="parent_chunks",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    document: Mapped["Document"] = relationship(
        back_populates="parent_chunks"
    )