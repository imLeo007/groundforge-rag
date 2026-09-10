

# Recall at k: the ratio of retrieved items in relevant items.

def recall_at_k(
    relevant_items: set[tuple[int, int, int]],
    retrieved_items: list[tuple[int, int, int]],
    k: int,
) -> float:
    if k <= 0:
        raise ValueError("top_k must be greater than zero")

    if not relevant_items:
        return 0.0

    retrieved_top_k = retrieved_items[:k]

    retrieved_relevant = {
        item
        for item in retrieved_top_k
        if item in relevant_items
    }

    return len(retrieved_relevant) / len(relevant_items)


# Reciprocal Rank: How high the first item in retrieved items was ranked?.

def reciprocal_rank(
    relevant_items: set[tuple[int, int, int]],
    retrieved_items: list[tuple[int, int, int]],
) -> float:
    if not relevant_items:
        return 0.0

    for rank, item in enumerate(retrieved_items, start=1):
        if item in relevant_items:

            return 1.0 /rank

    return 0.0


# Mean for reciprocal ranks: avg.

def mean_reciprocal_ranks(
    reciprocal_ranks: list[float]
) -> float:
    if not reciprocal_ranks:
        return 0.0

    return sum(reciprocal_ranks) / len(reciprocal_ranks)