"""Provider-agnostic LLM caller with structured Pydantic validation,

bounded retries, low temperature, and deterministic mock mode.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
from pathlib import Path
import random
import re
import types
import typing
from typing import Any, Callable, Dict, Optional, Type, TypeVar, get_args, get_origin
import httpx
from pydantic import BaseModel, ValidationError
from pydantic_core import PydanticUndefined

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class ConfigurationError(Exception):
    """Raised when LLM configuration or provider credentials are missing in real/record modes."""
    pass


def get_llm_mode() -> str:
    """Read the active LLM execution mode ('mock', 'real', 'record', 'replay')."""
    mode = os.getenv("LLM_MODE")
    if mode:
        return mode.strip().lower()
    legacy_mock = os.getenv("LLM_MOCK_MODE")
    if legacy_mock:
        return "mock" if legacy_mock.lower() in ("true", "1", "yes") else "real"
    return "mock"


def get_llm_provider() -> str:
    """Return the active provider ('gemini', 'openai', 'anthropic', 'replay', or 'mock')."""
    mode = get_llm_mode()
    provider = os.getenv("LLM_PROVIDER")
    if provider:
        return provider.strip().lower()
    if mode == "mock":
        return "mock"
    if mode == "replay":
        return "replay"
    # Real or record mode: determine from explicit API keys
    if os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"):
        return "gemini"
    if os.getenv("OPENAI_API_KEY"):
        return "openai"
    if os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic"
    raise ConfigurationError(
        "LLM_MODE is set to 'real' or 'record', but no API key was provided. "
        "Set LLM_PROVIDER to 'gemini', 'openai', or 'anthropic' and configure the corresponding API key."
    )


def get_llm_model() -> str:
    """Return the explicitly configured model identifier without fallback guessing."""
    mode = get_llm_mode()
    if mode == "mock":
        return os.getenv("GEMINI_MODEL") or os.getenv("OPENAI_MODEL") or os.getenv("ANTHROPIC_MODEL") or "mock-deterministic"
    if mode == "replay":
        return os.getenv("GEMINI_MODEL") or os.getenv("OPENAI_MODEL") or os.getenv("ANTHROPIC_MODEL") or "replay-cassette"

    provider = get_llm_provider()
    if provider == "gemini":
        model = os.getenv("GEMINI_MODEL")
        if not model:
            raise ConfigurationError("Set GEMINI_MODEL to a currently supported model ID from the provider's docs (e.g. gemini-2.0-flash)")
        return model
    elif provider == "openai":
        model = os.getenv("OPENAI_MODEL")
        if not model:
            raise ConfigurationError("Set OPENAI_MODEL to a currently supported model ID from the provider's docs (e.g. gpt-4o)")
        return model
    elif provider == "anthropic":
        model = os.getenv("ANTHROPIC_MODEL")
        if not model:
            raise ConfigurationError("Set ANTHROPIC_MODEL to a currently supported model ID from the provider's docs (e.g. claude-3-5-sonnet-20241022)")
        return model
    return "unknown"


def get_llm_badge() -> str:
    """Return a human-readable badge describing the active LLM mode and provider."""
    mode = get_llm_mode()
    if mode == "mock":
        return "LLM Mode: Mock (deterministic seed)"
    elif mode == "replay":
        return "LLM Mode: Replay (Deterministic Cassettes)"
    try:
        prov = get_llm_provider()
        model = get_llm_model()
        return f"LLM Mode: {mode.title()} ({prov.title()}: {model})"
    except Exception:
        return f"LLM Mode: {mode.title()}"


def compute_cassette_hash(prompt: str, model_name: str, provider: str, model: str) -> str:
    """Compute stable SHA-256 hash by stripping volatile timestamps and UUIDs."""
    normalized = re.sub(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?", "[TIMESTAMP]", prompt)
    normalized = re.sub(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b", "[UUID]", normalized)
    normalized = re.sub(r"Decision id:\s*[^\s\n\.,]+", "Decision id: [ID]", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    key = f"{normalized}:{model_name}:{provider}:{model}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:24]


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
    cassette_file: Optional[str] = None,
) -> T:
    """Execute a structured LLM call validated against a Pydantic model.

    Modes:
    - mock: returns canned or registered mock response (default).
    - real: calls LLM API; raises ConfigurationError if keys are missing.
    - record: calls LLM API and saves output to cassette file.
    - replay: reads canned response from cassette file without making API calls.
    """
    mode = get_llm_mode()
    if mock_mode is not None:
        mode = "mock" if mock_mode else "real"

    # Replay mode: read cassette file
    if mode == "replay":
        provider = os.getenv("LLM_PROVIDER", "gemini")
        model = os.getenv("GEMINI_MODEL") or os.getenv("OPENAI_MODEL") or os.getenv("ANTHROPIC_MODEL") or "default"
        if not cassette_file:
            prompt_hash = compute_cassette_hash(prompt, response_model.__name__, provider, model)
            cassette_file = f"tests/cassettes/{prompt_hash}.json"
        c_path = Path(cassette_file)
        if not c_path.exists():
            raise FileNotFoundError(f"Cassette file not found for replay: {c_path}")
        with open(c_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return response_model.model_validate(data)

    # Mock mode
    if mode == "mock":
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
            return _generate_default_mock(response_model, prompt)
        except Exception as e:
            logger.warning(f"Default mock generation failed for {response_model.__name__}: {e}")
            raise RuntimeError(f"No mock handler or mock_response provided for {response_model.__name__}")

    # Real or Record mode: require valid provider and model
    provider = get_llm_provider()
    model = get_llm_model()

    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    if provider == "gemini" and not gemini_key:
        raise ConfigurationError("LLM_PROVIDER is 'gemini' but GEMINI_API_KEY is not set.")
    elif provider == "openai" and not openai_key:
        raise ConfigurationError("LLM_PROVIDER is 'openai' but OPENAI_API_KEY is not set.")
    elif provider == "anthropic" and not anthropic_key:
        raise ConfigurationError("LLM_PROVIDER is 'anthropic' but ANTHROPIC_API_KEY is not set.")

    json_schema = json.dumps(response_model.model_json_schema(), indent=2)
    augmented_prompt = f"{prompt}\n\nStrict output requirement: Return ONLY a valid JSON object matching this JSON Schema:\n{json_schema}"

    last_error: Optional[Exception] = None

    for attempt in range(1, max_retries + 1):
        try:
            raw_response_text = ""
            if provider == "gemini" and gemini_key:
                raw_response_text = await _call_gemini(
                    api_key=gemini_key,
                    system_prompt=system_prompt,
                    prompt=augmented_prompt,
                    temperature=temperature,
                    model=model,
                )
            elif provider == "openai" and openai_key:
                raw_response_text = await _call_openai(
                    api_key=openai_key,
                    system_prompt=system_prompt,
                    prompt=augmented_prompt,
                    temperature=temperature,
                    model=model,
                )
            elif provider == "anthropic" and anthropic_key:
                raw_response_text = await _call_anthropic(
                    api_key=anthropic_key,
                    system_prompt=system_prompt,
                    prompt=augmented_prompt,
                    temperature=temperature,
                    model=model,
                )

            cleaned = clean_json_markdown(raw_response_text)
            parsed_data = json.loads(cleaned)
            validated = response_model.model_validate(parsed_data)

            # If in record mode, write cassette to disk
            if mode == "record":
                if not cassette_file:
                    prompt_hash = compute_cassette_hash(prompt, response_model.__name__, provider, model)
                    cassette_file = f"tests/cassettes/{prompt_hash}.json"
                c_path = Path(cassette_file)
                c_path.parent.mkdir(parents=True, exist_ok=True)
                with open(c_path, "w", encoding="utf-8") as f:
                    json.dump(parsed_data, f, indent=2)

            return validated

        except (ValidationError, json.JSONDecodeError, httpx.HTTPError) as err:
            last_error = err
            logger.warning(f"Attempt {attempt}/{max_retries} failed for {response_model.__name__}: {err}")
            if attempt < max_retries:
                delay = 0.5 * (2 ** (attempt - 1)) + random.uniform(0.1, 0.4)
                if isinstance(err, httpx.HTTPStatusError):
                    if err.response.status_code in (429, 500, 502, 503, 504):
                        retry_after = err.response.headers.get("Retry-After")
                        if retry_after:
                            try:
                                delay = max(delay, float(retry_after) + random.uniform(0.1, 0.5))
                            except ValueError:
                                pass
                await asyncio.sleep(delay)
            else:
                break

    raise RuntimeError(f"Failed to obtain valid {response_model.__name__} after {max_retries} attempts: {last_error}")


async def _call_gemini(api_key: str, system_prompt: str, prompt: str, temperature: float, model: Optional[str] = None) -> str:
    target_model = model or os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{target_model}:generateContent"
    headers = {
        "x-goog-api-key": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "response_mime_type": "application/json",
        },
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        candidates = data.get("candidates", [])
        if not candidates:
            raise ValueError("No candidates returned from Gemini API")
        return candidates[0]["content"]["parts"][0]["text"]


async def _call_openai(api_key: str, system_prompt: str, prompt: str, temperature: float, model: Optional[str] = None) -> str:
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    target_model = model or os.getenv("OPENAI_MODEL", "gpt-4o")
    payload = {
        "model": target_model,
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


async def _call_anthropic(api_key: str, system_prompt: str, prompt: str, temperature: float, model: Optional[str] = None) -> str:
    url = "https://api.anthropic.com/v1/messages"
    target_model = model or os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": target_model,
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
