from sqlalchemy.orm import Mapped, mapped_column, relationship

from sqlalchemy import String, Integer, DateTime, func

from typing import TYPE_CHECKING

from datetime import datetime

from app.core.database import Base


if TYPE_CHECKING:
    from app.models.parentchunks import ParentChunks


class Document(Base):

    __tablename__ = "document"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    filename: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    category: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String,
        nullable=False,
        server_default="queued",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    parent_chunks: Mapped[list["ParentChunks"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )