"""OpenAI LLM provider implementation."""

import json
from typing import Any, Dict, Optional

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False

from openai import AsyncOpenAI

from ..core.logger import get_logger
from .base import LLMProvider, LLMResponse, StructuredOutput

logger = get_logger(__name__)


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider implementation."""

    # Pricing per 1M tokens (as of 2024)
    PRICING = {
        "gpt-4-turbo-preview": {"input": 10.0, "output": 30.0},
        "gpt-4": {"input": 30.0, "output": 60.0},
        "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
        "gpt-3.5-turbo-16k": {"input": 3.0, "output": 4.0},
    }

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-5-mini",
        temperature: float = 0.3,
        max_tokens: int = 9000,
        organization: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key
            model: Model name
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            organization: Optional organization ID
            **kwargs: Additional parameters
        """
        super().__init__(api_key, model, temperature, max_tokens, **kwargs)

        # Only set organization if explicitly provided
        client_kwargs = {"api_key": api_key}
        if organization:
            client_kwargs["organization"] = organization
            
        self.client = AsyncOpenAI(**client_kwargs)

        # Initialize tokenizer (optional)
        self.encoding = None
        if TIKTOKEN_AVAILABLE:
            try:
                self.encoding = tiktoken.encoding_for_model(model)
            except KeyError:
                # Fallback to cl100k_base for newer models
                try:
                    self.encoding = tiktoken.get_encoding("cl100k_base")
                except Exception:
                    pass

    async def generate_completion(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Generate text completion using OpenAI.

        Args:
            prompt: Input prompt
            temperature: Override default temperature
            max_tokens: Override default max tokens
            **kwargs: Additional parameters

        Returns:
            LLM response
        """
        temp = temperature if temperature is not None else self.temperature
        tokens = max_tokens if max_tokens is not None else self.max_tokens

        try:
            logger.debug(
                "openai_request",
                model=self.model,
                temperature=temp,
                max_tokens=tokens,
            )

            # O1 models (o1-mini, o1-preview, gpt-5-mini) only support temperature=1
            request_params = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": tokens,
            }
            
            # Only add temperature for models that support it
            if not self.model.startswith("o1") and not self.model.startswith("gpt-5"):
                request_params["temperature"] = temp
            
            request_params.update(kwargs)
            
            response = await self.client.chat.completions.create(**request_params)

            content = response.choices[0].message.content or ""
            tokens_used = response.usage.total_tokens if response.usage else 0
            cost = self.estimate_cost(
                response.usage.prompt_tokens if response.usage else 0,
                response.usage.completion_tokens if response.usage else 0,
            )

            logger.debug(
                "openai_response",
                tokens_used=tokens_used,
                cost=cost,
                finish_reason=response.choices[0].finish_reason,
            )

            return LLMResponse(
                content=content,
                tokens_used=tokens_used,
                cost=cost,
                model=self.model,
                finish_reason=response.choices[0].finish_reason or "stop",
            )

        except Exception as e:
            logger.error("openai_error", error=str(e), exc_info=True)
            raise

    async def generate_structured_output(
        self,
        prompt: str,
        schema: Dict[str, Any],
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> StructuredOutput:
        """
        Generate structured output using OpenAI function calling.

        Args:
            prompt: Input prompt
            schema: JSON schema for output
            temperature: Override default temperature
            **kwargs: Additional parameters

        Returns:
            Structured output
        """
        temp = temperature if temperature is not None else self.temperature

        # Build function definition from schema
        function_def = {
            "name": "extract_data",
            "description": "Extract structured data from document",
            "parameters": schema,
        }

        try:
            # O1 models (o1-mini, o1-preview, gpt-5-mini) only support temperature=1
            request_params = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "functions": [function_def],
                "function_call": {"name": "extract_data"},
            }
            
            # Only add temperature for models that support it
            if not self.model.startswith("o1") and not self.model.startswith("gpt-5"):
                request_params["temperature"] = temp
            
            request_params.update(kwargs)
            
            response = await self.client.chat.completions.create(**request_params)

            # Extract function call arguments
            function_call = response.choices[0].message.function_call
            if not function_call:
                raise ValueError("No function call in response")

            data = json.loads(function_call.arguments)

            tokens_used = response.usage.total_tokens if response.usage else 0
            cost = self.estimate_cost(
                response.usage.prompt_tokens if response.usage else 0,
                response.usage.completion_tokens if response.usage else 0,
            )

            return StructuredOutput(
                data=data,
                tokens_used=tokens_used,
                cost=cost,
            )

        except Exception as e:
            logger.error("openai_structured_error", error=str(e), exc_info=True)
            raise

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text using tiktoken or fallback estimation.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens
        """
        if self.encoding is not None:
            try:
                return len(self.encoding.encode(text))
            except Exception:
                pass
        
        # Fallback: rough estimate (~4 chars per token)
        return len(text) // 4

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Estimate cost based on token usage.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Estimated cost in USD
        """
        # Get pricing for model (with fallback)
        pricing = self.PRICING.get(
            self.model, {"input": 10.0, "output": 30.0}  # Default to GPT-4 Turbo pricing
        )

        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost