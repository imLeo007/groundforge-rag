from typing import Any


def print_evaluation_report(
    evaluation: dict[str, Any],
) -> None:
    print("\n" + "=" * 60)
    print("RAG V15 - EVALUATION REPORT")
    print("=" * 60)

    # --------------------------------
    # General information
    # --------------------------------

    print(
        f"\nQuestions evaluated: "
        f"{evaluation['questions_evaluated']}"
    )

    print(
        f"Retrieval mode: "
        f"{evaluation['retrieval_mode']}"
    )

    print(
        f"Top K: "
        f"{evaluation['top_k']}"
    )

    # --------------------------------
    # Retrieval evaluation
    # --------------------------------

    print("\n" + "-" * 60)
    print("RETRIEVAL EVALUATION")
    print("-" * 60)

    print(
        f"Average Recall@{evaluation['top_k']}: "
        f"{evaluation['average_recall_at_k']:.3f}"
    )

    print(
        f"Mean Reciprocal Rank: "
        f"{evaluation['mean_reciprocal_rank']:.3f}"
    )

    # --------------------------------
    # Context compression evaluation
    # --------------------------------

    print("\n" + "-" * 60)
    print("RAGAS EVALUATION EVALUATION")
    print("-" * 60)

    print(
        f"Average Faithuflness Ratio:"
        f"{evaluation["ragas_evaluation"]["average_faithfulness"]:.3f}"
    )

    print(
        f"Average Context Precision Ratio:"
        f"{evaluation["ragas_evaluation"]["average_context_precision"]:.3f}"
    )

    print(
        f"Average Context Recall Ratio"
        f"{evaluation["ragas_evaluation"]["average_context_recall"]:.3f}"
    )

    # --------------------------------
    # Per-question results
    # --------------------------------

    print("\n" + "-" * 60)
    print("PER-QUESTION RESULTS")
    print("-" * 60)

    for result in evaluation["results"]:
        recall = result["recall_at_k"]
        rr = result["reciprocal_rank"]

        retrieval_status = (
            "PASS"
            if recall > 0
            else "FAIL"
        )

        print(
            f"\n[{result['id']}] "
            f"{retrieval_status}"
        )

        print(
            f"Question: "
            f"{result['question']}"
        )

        print(
            f"Faithfullness:"
            f"{result["ragas"]["faithfulness"]:.3f}"
        )

        print(
            f"Context Precision:"
            f"{result["ragas"]["context_precision"]:.3f}"
        )

        print(
            f"Context Recall:"
            f"{result["ragas"]["context_recall"]:.3f}"
        )

        # Retrieval metrics

        print(
            f"Recall@{evaluation['top_k']}: "
            f"{recall:.3f}"
        )

        print(
            f"Reciprocal Rank: "
            f"{rr:.3f}"
        )

        # Retrieved chunks

        print(
            f"Expected Children: "
            f"{result['relevant_children']}"
        )

        print(
            f"Retrieved Children: "
            f"{result['retrieved_children']}"
        )

        print("\n" + "." * 60)

    # --------------------------------
    # End
    # --------------------------------

    print("\n" + "=" * 60)
    print("END OF REPORT")
    print("=" * 60 + "\n")