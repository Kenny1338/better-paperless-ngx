"""Configuration management for Better Paperless."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load .env file at module import
load_dotenv()


class PaperlessConfig(BaseSettings):
    """Paperless-ngx connection configuration."""

    model_config = SettingsConfigDict(env_prefix="PAPERLESS_")

    api_url: str = "http://localhost:8000"
    api_token: str = ""
    verify_ssl: bool = True
    timeout: int = 30
    max_retries: int = 3


class OpenAIConfig(BaseSettings):
    """OpenAI LLM configuration."""

    model_config = SettingsConfigDict(env_prefix="OPENAI_")

    api_key: str = ""
    model: str = "gpt-5-mini"
    temperature: float = 0.3
    max_tokens: int = 9000
    organization: str = ""


class AnthropicConfig(BaseSettings):
    """Anthropic LLM configuration."""

    model_config = SettingsConfigDict(env_prefix="ANTHROPIC_")

    api_key: str = ""
    model: str = "claude-3-sonnet-20240229"
    temperature: float = 0.3
    max_tokens: int = 2000


class OllamaConfig(BaseSettings):
    """Ollama local LLM configuration."""

    model_config = SettingsConfigDict(env_prefix="OLLAMA_")

    base_url: str = "http://localhost:11434"
    model: str = "llama2"
    temperature: float = 0.3
    max_tokens: int = 2000


class RedisConfig(BaseSettings):
    """Redis cache configuration."""

    model_config = SettingsConfigDict(env_prefix="REDIS_")

    url: str = "redis://localhost:6379/0"
    password: str = ""


@dataclass
class ProcessingOptions:
    """Configuration options for document processing."""

    # Feature flags
    enable_title_generation: bool = True
    enable_tagging: bool = True
    enable_metadata_extraction: bool = True
    enable_categorization: bool = True
    enable_summarization: bool = False

    # LLM settings
    llm_provider: str = "openai"
    llm_model: str = "gpt-4"
    llm_temperature: float = 0.3
    llm_max_tokens: int = 2000

    # Tagging settings
    use_rule_based_tagging: bool = True
    use_llm_tagging: bool = True
    tag_confidence_threshold: float = 0.7
    max_tags_per_document: int = 10

    # Processing settings
    skip_if_title_exists: bool = True
    skip_if_tags_exist: bool = False
    overwrite_existing: bool = False
    processed_tag: str = "bp-processed"
    skip_if_processed_tag: bool = True

    # Summary settings
    summary_max_length: int = 500
    summary_style: str = "concise"  # concise, detailed, bullet_points

    # Error handling
    retry_attempts: int = 3
    retry_delay: float = 1.0
    continue_on_error: bool = True


class Config:
    """Main configuration manager for Better Paperless."""

    def __init__(self, config_path: Optional[Path] = None) -> None:
        """
        Initialize configuration.

        Args:
            config_path: Path to YAML configuration file
        """
        self.config_path = config_path or Path("config/config.yaml")
        self._config: Dict[str, Any] = {}
        self._load_config()

        # Initialize sub-configurations
        self.paperless = PaperlessConfig()
        self.openai = OpenAIConfig()
        self.anthropic = AnthropicConfig()
        self.ollama = OllamaConfig()
        self.redis = RedisConfig()

    def _load_config(self) -> None:
        """Load configuration from YAML file."""
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f) or {}
        else:
            self._config = self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "paperless": {
                "url": "http://localhost:8000",
                "verify_ssl": True,
                "timeout": 30,
                "max_retries": 3,
            },
            "llm": {
                "primary_provider": "openai",
                "fallback_provider": None,
            },
            "processing": {
                "features": {
                    "title_generation": True,
                    "tagging": True,
                    "metadata_extraction": True,
                    "categorization": True,
                    "summarization": False,
                },
                "rules": {
                    "skip_if_title_exists": True,
                    "skip_if_tagged": False,
                    "overwrite_existing_metadata": False,
                },
                "batch": {
                    "enabled": True,
                    "batch_size": 10,
                    "max_concurrent_processes": 5,
                },
            },
            "tagging": {
                "rule_based": {"enabled": True},
                "llm_based": {
                    "enabled": True,
                    "confidence_threshold": 0.7,
                    "max_tags_per_document": 10,
                },
                "tag_creation": {"auto_create_tags": True, "default_color": "#3498db"},
            },
            "metadata": {
                "date_extraction": {"enabled": True},
                "correspondent_extraction": {
                    "enabled": True,
                    "auto_create_correspondents": True,
                },
            },
            "summarization": {
                "enabled": False,
                "max_length": 500,
                "style": "concise",
            },
            "watcher": {
                "enabled": False,
                "mode": "webhook",
                "polling": {"interval_seconds": 60},
                "webhook": {"host": "0.0.0.0", "port": 8080, "path": "/webhook/paperless"},
            },
            "cache": {"enabled": True, "backend": "memory", "ttl_seconds": 3600},
            "logging": {"level": "INFO", "format": "json", "output": "file"},
            "monitoring": {"enabled": True, "metrics_port": 9090},
        }

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-separated key.

        Args:
            key: Dot-separated configuration key (e.g., 'llm.primary_provider')
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value by dot-separated key.

        Args:
            key: Dot-separated configuration key
            value: Value to set
        """
        keys = key.split(".")
        config = self._config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def get_processing_options(self) -> ProcessingOptions:
        """
        Get processing options from configuration.

        Returns:
            ProcessingOptions instance
        """
        proc_config = self.get("processing", {})
        features = proc_config.get("features", {})
        rules = proc_config.get("rules", {})
        tagging_config = self.get("tagging", {})
        summary_config = self.get("summarization", {})
        llm_config = self.get("llm", {})

        return ProcessingOptions(
            enable_title_generation=features.get("title_generation", True),
            enable_tagging=features.get("tagging", True),
            enable_metadata_extraction=features.get("metadata_extraction", True),
            enable_categorization=features.get("categorization", True),
            enable_summarization=features.get("summarization", False),
            llm_provider=llm_config.get("primary_provider", "openai"),
            skip_if_title_exists=rules.get("skip_if_title_exists", True),
            skip_if_tags_exist=rules.get("skip_if_tagged", False),
            overwrite_existing=rules.get("overwrite_existing_metadata", False),
            processed_tag=rules.get("processed_tag", "bp-processed"),
            skip_if_processed_tag=rules.get("skip_if_processed_tag", True),
            use_rule_based_tagging=tagging_config.get("rule_based", {}).get("enabled", True),
            use_llm_tagging=tagging_config.get("llm_based", {}).get("enabled", True),
            tag_confidence_threshold=tagging_config.get("llm_based", {}).get(
                "confidence_threshold", 0.7
            ),
            max_tags_per_document=tagging_config.get("llm_based", {}).get(
                "max_tags_per_document", 10
            ),
            summary_max_length=summary_config.get("max_length", 500),
            summary_style=summary_config.get("style", "concise"),
        )

    def save(self, path: Optional[Path] = None) -> None:
        """
        Save configuration to YAML file.

        Args:
            path: Path to save configuration (default: self.config_path)
        """
        save_path = path or self.config_path
        save_path.parent.mkdir(parents=True, exist_ok=True)

        with open(save_path, "w", encoding="utf-8") as f:
            yaml.dump(self._config, f, default_flow_style=False, sort_keys=False)

    @property
    def llm_provider(self) -> str:
        """Get the primary LLM provider."""
        return self.get("llm.primary_provider", "openai")

    @property
    def cache_enabled(self) -> bool:
        """Check if caching is enabled."""
        return self.get("cache.enabled", True)

    @property
    def watcher_enabled(self) -> bool:
        """Check if document watcher is enabled."""
        return self.get("watcher.enabled", False)

    @property
    def monitoring_enabled(self) -> bool:
        """Check if monitoring is enabled."""
        return self.get("monitoring.enabled", True)