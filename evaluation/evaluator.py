import json

from pathlib import Path

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.question import RetrievalMode, QuestionRequest

from app.schemas.document import RetrievedContextResponse

from app.routers.question import answer_question

import types

import sys


dummy_module = types.ModuleType("langchain_community.chat_models.vertexai")

dummy_module.ChatVertexAI = None

sys.modules["langchain_community.chat_models.vertexai"] = dummy_module


from ragas import SingleTurnSample, EvaluationDataset, evaluate

from openai import OpenAI

from ragas.llms import llm_factory

from ragas.metrics import Faithfulness, LLMContextPrecisionWithReference, LLMContextRecall

from app.core.config import settings

from evaluation.metrics import mean_reciprocal_ranks, recall_at_k, reciprocal_rank



EvaluationItem = dict[str, Any]


client = OpenAI(
    api_key=settings.ai_credits_api_key,
    base_url="https://aicredits.in/v1",
)


evaluator_llm = llm_factory(
    model=settings.ai_credits_model,
    provider="openai",
    client=client,
    temperature=0.0,
)


def load_dataset(
    path: str = "evaluation/dataset.json",
) -> list[EvaluationItem]:
    dataset_path = Path(path)

    if not dataset_path.exists():
        raise FileNotFoundError(f"dataset not found {path}")

    with dataset_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def build_relevant_children(
    item: EvaluationItem,
) -> set[tuple[int, int, int]]:
    return {
        (
            child["page_number"],
            child["parent_index"],
            child["child_index"]
        )for child in item["relevant_children"]
    }


def build_retrieved_children(
    contexts: list[RetrievedContextResponse],
) -> list[tuple[int, int, int]]:
    return [
        (
            context.page_number,
            context.parent_index,
            context.child_index,
        )for context in contexts
    ]


# Evaluate Retrieval: Runs the retrieval from pipeline itself and evaluates the questions.

async def evaluate_retrieval(
    db: AsyncSession,
    top_k: int = 5,
    retrieval_mode: RetrievalMode = RetrievalMode.hybrid,
) -> EvaluationItem:
    dataset = load_dataset()

    question_results: list[EvaluationItem] = []
    reciprocal_ranks: list[float] = []
    recall_scores: list[float] = []
    samples: list[SingleTurnSample] = []

    for item in dataset:
        request = QuestionRequest(
            question=item["question"],
            top_k=top_k,
            retrieval_mode=retrieval_mode,
        )

        response = await answer_question(request=request, db=db)

        sample = SingleTurnSample(
            user_input=response.question,
            retrieved_contexts=[
                context.parent_text
                for context in response.used_contexts
            ],
            response=response.answer,
            reference=item["reference_answer"],
        )

        samples.append(sample)

        relevant_children = build_relevant_children(item)

        retrieved_children = build_retrieved_children(response.used_contexts)

        recall = recall_at_k(
            relevant_items=relevant_children,
            retrieved_items=retrieved_children,
            k=top_k,
        )

        rr = reciprocal_rank(
            relevant_items=relevant_children,
            retrieved_items=retrieved_children,
        )

        recall_scores.append(recall)
        reciprocal_ranks.append(rr)

        question_results.append(
            {
                "id": item["id"],
                "question": item["question"],
                "answer": response.answer,
                "used_contexts": [
                    context.parent_text
                    for context in response.used_contexts
                ],
                "relevant_children": list(relevant_children),
                "retrieved_children": retrieved_children,
                "recall_at_k": recall,
                "reciprocal_rank": rr
            }
        )

    average_recall = (
        sum(recall_scores) / len(recall_scores)
        if recall_scores
        else 0.0
    )

    mrr = mean_reciprocal_ranks(reciprocal_ranks)

    faithfulness = Faithfulness(llm=evaluator_llm)

    context_precision = LLMContextPrecisionWithReference(llm=evaluator_llm)

    context_recall = LLMContextRecall(llm=evaluator_llm)

    eval_dataset = EvaluationDataset(samples=samples)

    result = evaluate(
        dataset=eval_dataset,
        metrics=[
            faithfulness,
            context_precision,
            context_recall,
        ]
    )

    ragas_df = result.to_pandas()

    for question_result, (_, row) in zip(question_results, ragas_df.iterrows()):
        question_result["ragas"] = {
            "faithfulness": float(row["faithfulness"]),
            "context_precision": float(row["llm_context_precision_with_reference"]),
            "context_recall": float(row["context_recall"])
        }

    scores = {
        "average_faithfulness": float(ragas_df["faithfulness"].mean()),
        "average_context_precision": float(ragas_df["llm_context_precision_with_reference"].mean()),
        "average_context_recall": float(ragas_df["context_recall"].mean())
    }

    return {
        "questions_evaluated": len(dataset),
        "retrieval_mode": retrieval_mode.value,
        "top_k": top_k,

        "average_recall_at_k": average_recall,
        "mean_reciprocal_rank": mrr,

        "results": question_results,
        "ragas_evaluation": scores
    }