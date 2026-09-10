import asyncio

from app.core.database import AsyncSessionLocal

from app.schemas.question import RetrievalMode

from evaluation.evaluator import evaluate_retrieval

from evaluation.report import print_evaluation_report


async def main() -> None:
    async with AsyncSessionLocal() as db:

        print("\nMULTI-QUERY V15")

        multi_query = await evaluate_retrieval(
            db=db,
            top_k=5,
            retrieval_mode=RetrievalMode.hybrid,
        )

        print_evaluation_report(multi_query)


if __name__ == "__main__":
    asyncio.run(main())