from litellm import acompletion

import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

MAIN_LLM_MODELS = [settings.gemini_model]

UTILITY_LLM_MODELS = [settings.groq_model, settings.openrouter_model]



def get_api_key_for_model(model: str) -> str | None:

    if "gemini" in model.lower():
        return settings.gemini_api_key

    if "groq" in model.lower():
        return settings.groq_api_key

    if "openrouter" in model.lower():
        return settings.openrouter_api_key
    
    return None



async def execute_llm_call(
    prompt: str,
    models: list[str],
    temperature: float = 0.1,
    max_tokens: int | None = None,
    reasoning_effort: str | None = None,
) -> str:

    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty")

    kwargs = {
        "temperature": temperature,
    }

    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens

    if reasoning_effort is not None:
        kwargs["reasoning_effort"] = reasoning_effort

    last_error: Exception | None = None

    for model in models:
        try:
            api_key = get_api_key_for_model(model)

            response = await acompletion(
                model=model,
                api_key=api_key,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                **kwargs,
            )

            answer = response.choices[0].message.content

            if not answer or not answer.strip():
                raise RuntimeError(f"{model} returned an empty response")

            return answer.strip()

        except Exception as error:
            last_error = error

            logger.warning("LLM model %s failed: %s", model, error)

    raise RuntimeError("All configured LLM models failed") from last_error



async def generate_answer(prompt: str) -> str:

    return await execute_llm_call(prompt, MAIN_LLM_MODELS, temperature=0.1, max_tokens=500, reasoning_effort="minimal")



async def generate_utility_call(prompt: str) -> str:

    return await execute_llm_call(prompt, UTILITY_LLM_MODELS, temperature=0.0, max_tokens=300)