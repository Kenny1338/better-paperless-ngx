"""Factory for creating LLM provider instances."""

from typing import Optional

from ..core.config import Config
from ..core.logger import get_logger
from .base import LLMProvider
from .openai_provider import OpenAIProvider

logger = get_logger(__name__)


class LLMFactory:
    """Factory for creating LLM provider instances."""

    @staticmethod
    def create_provider(
        provider_name: str,
        config: Config,
        model_override: Optional[str] = None,
    ) -> LLMProvider:
        """
        Create LLM provider instance.

        Args:
            provider_name: Name of provider (openai, anthropic, ollama)
            config: Application configuration
            model_override: Optional model name override

        Returns:
            LLM provider instance

        Raises:
            ValueError: If provider is not supported
        """
        provider_name = provider_name.lower()

        if provider_name == "openai":
            return LLMFactory._create_openai_provider(config, model_override)
        elif provider_name == "anthropic":
            return LLMFactory._create_anthropic_provider(config, model_override)
        elif provider_name == "ollama":
            return LLMFactory._create_ollama_provider(config, model_override)
        else:
            raise ValueError(
                f"Unsupported LLM provider: {provider_name}. "
                "Supported providers: openai, anthropic, ollama"
            )

    @staticmethod
    def _create_openai_provider(
        config: Config, model_override: Optional[str] = None
    ) -> OpenAIProvider:
        """Create OpenAI provider."""
        model = model_override or config.openai.model

        logger.info("creating_llm_provider", provider="openai", model=model)

        return OpenAIProvider(
            api_key=config.openai.api_key,
            model=model,
            temperature=config.openai.temperature,
            max_tokens=config.openai.max_tokens,
            organization=config.openai.organization,
        )

    @staticmethod
    def _create_anthropic_provider(
        config: Config, model_override: Optional[str] = None
    ) -> LLMProvider:
        """Create Anthropic provider."""
        # Import here to avoid dependency if not using Anthropic
        try:
            from .anthropic_provider import AnthropicProvider

            model = model_override or config.anthropic.model

            logger.info("creating_llm_provider", provider="anthropic", model=model)

            return AnthropicProvider(
                api_key=config.anthropic.api_key,
                model=model,
                temperature=config.anthropic.temperature,
                max_tokens=config.anthropic.max_tokens,
            )
        except ImportError:
            raise ImportError(
                "Anthropic provider requires 'anthropic' package. "
                "Install with: pip install anthropic"
            )

    @staticmethod
    def _create_ollama_provider(
        config: Config, model_override: Optional[str] = None
    ) -> LLMProvider:
        """Create Ollama provider."""
        # Import here to avoid dependency if not using Ollama
        try:
            from .ollama_provider import OllamaProvider

            model = model_override or config.ollama.model

            logger.info("creating_llm_provider", provider="ollama", model=model)

            return OllamaProvider(
                api_key="",  # Ollama doesn't need API key
                model=model,
                temperature=config.ollama.temperature,
                max_tokens=config.ollama.max_tokens,
                base_url=config.ollama.base_url,
            )
        except ImportError:
            raise ImportError(
                "Ollama provider requires 'ollama' package. " "Install with: pip install ollama"
            )

    @staticmethod
    def create_from_config(config: Config) -> LLMProvider:
        """
        Create LLM provider from configuration.

        Args:
            config: Application configuration

        Returns:
            LLM provider instance
        """
        provider_name = config.llm_provider
        return LLMFactory.create_provider(provider_name, config)