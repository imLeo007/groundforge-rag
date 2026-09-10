import json

import logging

from app.ai.llm import generate_utility_call

from app.models.message import Message



logger = logging.getLogger(__name__)



def format_conversation_history(messages: list[Message]) -> str:
    if not messages:
        return "No previous conversation"

    history: list[str] = []

    for message in messages:
        history.append(
            f"{message.role.upper()}: {message.content}"
        )

    return "\n\n".join(history)



async def prepare_queries(
    question: str,
    messages: list[Message],
    num_queries: int = 3,
) -> tuple[str, list[str]]:

    conversation_history = format_conversation_history(messages)

    prompt = f"""
You prepare questions for a document retrieval system.

Use the recent conversation only to understand what the current question refers to.

Your tasks:
1. Rewrite the current question as a clear standalone question.
2. Generate {num_queries} alternative search queries that express the same information need using different wording.

Rules:
- Preserve the user's original meaning.
- Resolve references such as "it", "they", "that", or "this".
- Do not answer the question.
- Do not add new information.
- Keep alternative queries short and clear.
- If the current question is already standalone, preserve its meaning.
- Return only valid JSON.

Return exactly this structure:

{{
    "standalone_question": "...",
    "alternative_queries": [
        "...",
        "...",
        "..."
    ]
}}

Recent conversation:
{conversation_history}

Current Question:
{question}
"""
    try:

        response = await generate_utility_call(prompt)

        data = json.loads(response)

        standalone_question = data.get("standalone_question", question)

        if (
            not isinstance(standalone_question, str)
            or not standalone_question.strip()
        ):
            standalone_question = question

        else:
            standalone_question = standalone_question.strip()

        alternative_queries = data.get("alternative_queries", [])

        queries = [standalone_question]

        if isinstance(alternative_queries, list):
            for query in alternative_queries:
                if (
                    isinstance(query, str)
                    and query.strip()
                    and query.strip() not in queries
                ):
                    queries.append(query.strip())

        return standalone_question, queries

    except Exception as error:
        logger.warning("Query preparation failed %s", error)

        return question, [question]