"""LLM client abstractions for partial prompt bias experiments."""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Sequence

try:
    from openai import AsyncAzureOpenAI, AsyncOpenAI
except ImportError:  # pragma: no cover - optional dependency
    AsyncOpenAI = None  # type: ignore[misc]
    AsyncAzureOpenAI = None  # type: ignore[misc]


class LLMClient(ABC):
    """Abstract interface for querying an LLM for a single label selection."""

    @abstractmethod
    async def choose_label(
        self,
        partial_prompt: str,
        labels: Sequence[str],
        temperature: float,
        max_tokens: int,
        model: str,
    ) -> int:
        """Return the index of the chosen label."""


class OpenAIClient(LLMClient):
    """Concrete LLM client that uses OpenAI's async Chat Completions API."""

    def __init__(self, api_key: str | None = None) -> None:
        if AsyncOpenAI is None:
            raise RuntimeError(
                "openai package not installed. Add it to requirements.txt."
            )
        key = api_key or os.environ.get("OPENAI_API_KEY")
        if key is None:
            raise RuntimeError("OPENAI_API_KEY is required for OpenAIClient.")
        self.client = AsyncOpenAI(api_key=key)

    async def choose_label(
        self,
        partial_prompt: str,
        labels: Sequence[str],
        temperature: float,
        max_tokens: int,
        model: str,
    ) -> int:
        if not labels:
            raise ValueError("labels must be non-empty.")

        system_prompt = (
            "You are a classifier. Respond with exactly one label from the provided "
            "list, with no additional explanation."
        )
        user_prompt = (
            f"{partial_prompt}\n\nValid labels: {', '.join(labels)}\n"
            "Answer with exactly one of these labels."
        )

        response = await self.client.chat.completions.create(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

        message = response.choices[0].message.content or ""
        text = message.strip()

        # Match exact label or prefix match; fall back to first matching substring.
        for idx, label in enumerate(labels):
            if text == label or text.startswith(label):
                return idx

        for idx, label in enumerate(labels):
            if label in text:
                return idx

        return 0  # Fallback with implicit logging responsibility to caller.


class AzureOpenAIClient(LLMClient):
    """LLM client that targets Azure OpenAI deployments."""

    def __init__(
        self,
        *,
        endpoint: str | None = None,
        api_version: str | None = None,
        deployment: str | None = None,
        api_key: str | None = None,
    ) -> None:
        if AsyncAzureOpenAI is None:
            raise RuntimeError(
                "openai package not installed. Add it to requirements.txt."
            )
        endpoint = endpoint or os.environ.get("AZURE_OPENAI_ENDPOINT")
        api_version = api_version or os.environ.get("AZURE_OPENAI_API_VERSION")
        deployment = deployment or os.environ.get("AZURE_OPENAI_DEPLOYMENT")
        api_key = api_key or os.environ.get("AZURE_OPENAI_KEY") or os.environ.get(
            "OPENAI_API_KEY"
        )

        missing = [
            name
            for name, value in [
                ("AZURE_OPENAI_ENDPOINT", endpoint),
                ("AZURE_OPENAI_API_VERSION", api_version),
                ("AZURE_OPENAI_DEPLOYMENT", deployment),
                ("AZURE_OPENAI_KEY/OPENAI_API_KEY", api_key),
            ]
            if value is None
        ]
        if missing:
            raise RuntimeError(
                "Missing Azure OpenAI configuration values: " + ", ".join(missing)
            )

        self.deployment = deployment  # type: ignore[assignment]
        self.client = AsyncAzureOpenAI(
            azure_endpoint=endpoint,
            api_version=api_version,
            api_key=api_key,
        )

    async def choose_label(
        self,
        partial_prompt: str,
        labels: Sequence[str],
        temperature: float,
        max_tokens: int,
        model: str,
    ) -> int:
        if not labels:
            raise ValueError("labels must be non-empty.")

        system_prompt = (
            "You are a classifier. Respond with exactly one label from the provided "
            "list, with no additional explanation."
        )
        user_prompt = (
            f"{partial_prompt}\n\nValid labels: {', '.join(labels)}\n"
            "Answer with exactly one of these labels."
        )

        response = await self.client.chat.completions.create(
            model=self.deployment or model,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

        message = response.choices[0].message.content or ""
        text = message.strip()

        for idx, label in enumerate(labels):
            if text == label or text.startswith(label):
                return idx

        for idx, label in enumerate(labels):
            if label in text:
                return idx

        return 0

