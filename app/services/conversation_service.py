from sqlalchemy import select

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation

from app.models.message import Message


async def create_conversation(
    db: AsyncSession,
) -> Conversation:
    conversation = Conversation()

    db.add(conversation)

    await db.commit()

    await db.refresh(conversation)

    return conversation


async def save_message(
    db: AsyncSession,
    conversation_id: int,
    role: str,
    content: str
) -> Message:
    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
    )

    db.add(message)

    await db.commit()

    await db.refresh(message)

    return message


async def get_recent_message(
    db: AsyncSession,
    conversation_id: int,
    limit: int = 6,
) -> list[Message]:
    query = (
        select(Message).where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc(), Message.id.desc())
        .limit(limit)
    )

    result = await db.execute(query)

    messages = list(result.scalars().all())

    messages.reverse()

    return messages