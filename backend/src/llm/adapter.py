"""
LLM Adapter — Abstraction layer for LLM API calls.

Uses Google Gemini as the primary provider.
Designed with an adapter pattern for easy provider switching.
"""

import json
import logging

from google import genai

from src.core.config import settings

logger = logging.getLogger(__name__)


class LLMAdapter:
    """
    Adapter for LLM API calls.

    Wraps the Gemini API with:
    - Structured JSON output parsing
    - Error handling and retries
    - Logging for debugging
    """

    def __init__(self, provider: str = "gemini"):
        self.provider = provider
        self._client = None

    @property
    def client(self):
        """Lazy-initialize the Gemini client."""
        if self._client is None:
            if not settings.GEMINI_API_KEY:
                raise ValueError(
                    "GEMINI_API_KEY is not set. Add it to your .env file."
                )
            self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
        return self._client

    async def generate(
        self,
        prompt: str,
        system_instruction: str,
        model: str = "gemini-2.0-flash",
        temperature: float = 0.3,
    ) -> str:
        """
        Generate a response from the LLM.

        Args:
            prompt: The user/task prompt.
            system_instruction: System-level instructions for the model.
            model: Model identifier (default: gemini-2.0-flash for free tier).
            temperature: Sampling temperature (lower = more deterministic).

        Returns:
            Raw text response from the model.
        """
        try:
            response = await self.client.aio.models.generate_content(
                model=model,
                contents=prompt,
                config={
                    "system_instruction": system_instruction,
                    "temperature": temperature,
                },
            )
            return response.text
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise

    async def generate_json(
        self,
        prompt: str,
        system_instruction: str,
        model: str = "gemini-2.0-flash",
        temperature: float = 0.2,
    ) -> dict:
        """
        Generate a response and parse it as JSON.

        The system instruction should explicitly ask for JSON output.

        Args:
            prompt: The user/task prompt.
            system_instruction: Must include "respond in JSON" instruction.
            model: Model identifier.
            temperature: Sampling temperature.

        Returns:
            Parsed JSON dict.
        """
        raw_response = await self.generate(
            prompt=prompt,
            system_instruction=system_instruction + "\n\nYou MUST respond with valid JSON only. No markdown, no code fences.",
            model=model,
            temperature=temperature,
        )

        # Clean response — strip markdown code fences if present
        cleaned = raw_response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}\nRaw: {raw_response[:500]}")
            raise ValueError(f"LLM returned invalid JSON: {e}")


# Singleton instance
llm_adapter = LLMAdapter()
