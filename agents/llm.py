"""Provider-agnostic LLM caller with structured Pydantic validation,

bounded retries, low temperature, and deterministic mock mode.
"""

from __future__ import annotations

import json
import logging
import os
import re
import types
import typing
from typing import Any, Callable, Dict, Optional, Type, TypeVar, get_args, get_origin
import httpx
from pydantic import BaseModel, ValidationError
from pydantic_core import PydanticUndefined

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

# Registry for canned mock handlers: model_class -> handler callable or canned instance
_MOCK_REGISTRY: Dict[Type[Any], Callable[[str, str], Any]] = {}


def register_mock_generator(model_cls: Type[T], generator: Callable[[str, str], T]) -> None:
    """Register a custom mock response generator for a specific Pydantic model."""
    _MOCK_REGISTRY[model_cls] = generator


def clean_json_markdown(text: str) -> str:
    """Strip markdown code fences (```json ... ```) if present."""
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        return match.group(1).strip()
    return text


async def llm_call(
    prompt: str,
    response_model: Type[T],
    system_prompt: str = "You are an analytical AI reasoning engine. Provide your output strictly in JSON conforming to the requested schema.",
    temperature: float = 0.0,
    max_retries: int = 3,
    mock_mode: Optional[bool] = None,
    mock_response: Optional[T] = None,
) -> T:
    """Execute a structured LLM call validated against a Pydantic model.

    Features:
    - Provider agnostic: checks Gemini, OpenAI, Anthropic, or defaults to Mock mode.
    - Low temperature for analytical consistency.
    - Bounded retries on schema or JSON parse failure.
    - Deterministic mock mode for test suites and offline resilience.
    """
    if mock_mode is None:
        mock_mode = os.getenv("LLM_MOCK_MODE", "true").lower() in ("true", "1", "yes")

    # If mock mode or explicit mock response requested
    if mock_mode:
        if mock_response is not None:
            return mock_response

        # Check registered generators
        if response_model in _MOCK_REGISTRY:
            generated = _MOCK_REGISTRY[response_model](prompt, system_prompt)
            if isinstance(generated, response_model):
                return generated
            return response_model.model_validate(generated)

        # Attempt default mock instantiation
        try:
            # Try to instantiate model with defaults or sample fields
            return _generate_default_mock(response_model, prompt)
        except Exception as e:
            logger.warning(f"Default mock generation failed for {response_model.__name__}: {e}")
            raise RuntimeError(f"No mock handler or mock_response provided for {response_model.__name__}")

    # Real LLM Call path
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    json_schema = json.dumps(response_model.model_json_schema(), indent=2)
    augmented_prompt = f"{prompt}\n\nStrict output requirement: Return ONLY a valid JSON object matching this JSON Schema:\n{json_schema}"

    last_error: Optional[Exception] = None

    for attempt in range(1, max_retries + 1):
        try:
            raw_response_text = ""
            if gemini_key:
                raw_response_text = await _call_gemini(
                    api_key=gemini_key,
                    system_prompt=system_prompt,
                    prompt=augmented_prompt,
                    temperature=temperature,
                )
            elif openai_key:
                raw_response_text = await _call_openai(
                    api_key=openai_key,
                    system_prompt=system_prompt,
                    prompt=augmented_prompt,
                    temperature=temperature,
                )
            elif anthropic_key:
                raw_response_text = await _call_anthropic(
                    api_key=anthropic_key,
                    system_prompt=system_prompt,
                    prompt=augmented_prompt,
                    temperature=temperature,
                )
            else:
                # Fallback to mock mode if no API key found
                logger.info("No API keys found in environment. Falling back to mock mode.")
                return await llm_call(
                    prompt=prompt,
                    response_model=response_model,
                    system_prompt=system_prompt,
                    mock_mode=True,
                    mock_response=mock_response,
                )

            cleaned = clean_json_markdown(raw_response_text)
            parsed_data = json.loads(cleaned)
            return response_model.model_validate(parsed_data)

        except (ValidationError, json.JSONDecodeError, httpx.HTTPError) as err:
            last_error = err
            logger.warning(f"Attempt {attempt}/{max_retries} failed for {response_model.__name__}: {err}")
            if attempt == max_retries:
                # If retries exhausted and mock fallback is acceptable, or raise
                break

    raise RuntimeError(f"Failed to obtain valid {response_model.__name__} after {max_retries} attempts: {last_error}")


async def _call_gemini(api_key: str, system_prompt: str, prompt: str, temperature: float) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "response_mime_type": "application/json",
        },
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        candidates = data.get("candidates", [])
        if not candidates:
            raise ValueError("No candidates returned from Gemini API")
        return candidates[0]["content"]["parts"][0]["text"]


async def _call_openai(api_key: str, system_prompt: str, prompt: str, temperature: float) -> str:
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
        "response_format": {"type": "json_object"},
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


async def _call_anthropic(api_key: str, system_prompt: str, prompt: str, temperature: float) -> str:
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-20241022"),
        "max_tokens": 4096,
        "temperature": temperature,
        "system": system_prompt,
        "messages": [{"role": "user", "content": prompt}],
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data["content"][0]["text"]


def _generate_default_mock(model_cls: Type[T], prompt: str) -> T:
    """Construct a synthetic valid instance of model_cls when no specific mock is registered."""
    fields = model_cls.model_fields
    values: Dict[str, Any] = {}
    for name, field in fields.items():
        if field.default is not PydanticUndefined and field.default is not None:
            values[name] = field.default
        elif field.default_factory is not None:
            values[name] = field.default_factory()
        else:
            annotation = field.annotation
            origin = get_origin(annotation)
            args = get_args(annotation)

            # Handle Optional / Union
            if origin is typing.Union or (hasattr(types, "UnionType") and origin is types.UnionType):
                # Filter out NoneType
                non_none = [a for a in args if a is not type(None)]
                if non_none:
                    annotation = non_none[0]
                    origin = get_origin(annotation)
                    args = get_args(annotation)

            # Handle Literal
            if origin is typing.Literal and args:
                values[name] = args[0]
            # Handle primitive types
            elif annotation is str:
                values[name] = f"mock_{name}"
            elif annotation is int:
                values[name] = 1
            elif annotation is float:
                values[name] = 0.5
            elif annotation is bool:
                values[name] = True
            elif origin in (list, typing.List):
                values[name] = []
            elif origin in (dict, typing.Dict):
                values[name] = {}
            elif isinstance(annotation, type) and issubclass(annotation, BaseModel):
                values[name] = _generate_default_mock(annotation, prompt)
            else:
                values[name] = None
    return model_cls.model_validate(values)
