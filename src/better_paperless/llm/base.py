"""Abstract base class for LLM providers."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from pydantic import BaseModel


class LLMResponse(BaseModel):
    """Standardized LLM response."""

    content: str
    tokens_used: int
    cost: float
    model: str
    finish_reason: str = "stop"

    class Config:
        """Pydantic config."""

        from_attributes = True


class StructuredOutput(BaseModel):
    """Structured output from LLM."""

    data: Dict[str, Any]
    confidence: float = 1.0
    tokens_used: int
    cost: float

    class Config:
        """Pydantic config."""

        from_attributes = True


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(
        self,
        api_key: str,
        model: str,
        temperature: float = 0.3,
        max_tokens: int = 2000,
        **kwargs: Any,
    ) -> None:
        """
        Initialize LLM provider.

        Args:
            api_key: API key for the provider
            model: Model name to use
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens in response
            **kwargs: Additional provider-specific arguments
        """
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.extra_params = kwargs

    @abstractmethod
    async def generate_completion(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Generate text completion.

        Args:
            prompt: Input prompt
            temperature: Override default temperature
            max_tokens: Override default max tokens
            **kwargs: Additional generation parameters

        Returns:
            LLM response
        """
        pass

    @abstractmethod
    async def generate_structured_output(
        self,
        prompt: str,
        schema: Dict[str, Any],
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> StructuredOutput:
        """
        Generate structured output matching schema.

        Args:
            prompt: Input prompt
            schema: JSON schema for output
            temperature: Override default temperature
            **kwargs: Additional generation parameters

        Returns:
            Structured output
        """
        pass

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens
        """
        pass

    @abstractmethod
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Estimate cost for token usage.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Estimated cost in USD
        """
        pass

    async def generate_with_retry(
        self,
        prompt: str,
        max_retries: int = 3,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Generate completion with automatic retry.

        Args:
            prompt: Input prompt
            max_retries: Maximum number of retries
            **kwargs: Additional generation parameters

        Returns:
            LLM response
        """
        last_error = None

        for attempt in range(max_retries):
            try:
                return await self.generate_completion(prompt, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    # Wait before retry (exponential backoff)
                    import asyncio

                    await asyncio.sleep(2**attempt)

        raise last_error or Exception("Failed after retries")