from app.schemas.question import QuestionResponse


def print_rag_report(
    response: QuestionResponse,
) -> None:
    print("\n" + "=" * 60)
    print("RAG V12 - CONVERSATION REPORT")
    print("=" * 60)

    print(
        f"\nConversation ID: "
        f"{response.conversation_id}"
    )

    print(
        f"Retrieval Mode: "
        f"{response.retrieval_mode.value}"
    )

    print("\n" + "-" * 60)
    print("QUESTION")
    print("-" * 60)

    print(
        f"Original: "
        f"{response.question}"
    )

    print(
        f"Rewritten: "
        f"{response.rewritten_question}"
    )

    print("\n" + "-" * 60)
    print("RETRIEVED CONTEXT")
    print("-" * 60)

    for pos, context in enumerate(
        response.used_contexts,
        start=1,
    ):
        print(
            f"\nSource {pos}"
        )

        print(
            f"Document: "
            f"{context.filename}"
        )

        print(
            f"Page: "
            f"{context.page_number}"
        )

        print(
            f"Matched Child: "
            f"{context.child_index}"
        )

        print(
            f"Rerank Score: "
            f"{context.rerank_score}"
        )

    print("\n" + "-" * 60)
    print("FINAL ANSWER")
    print("-" * 60)

    print(response.answer)

    print("\n" + "=" * 60)
    print("END OF REPORT")
    print("=" * 60 + "\n")