"""
System configuration for the Agentic AI Architect system.

All settings can be overridden via environment variables (prefixed with AAA_).
Sensitive values (API keys, credentials) must NEVER be committed to source code.
Use a .env file or environment variables instead.

Usage::

    from config.settings import get_settings
    settings = get_settings()
    print(settings.data_dir)
"""

import os
from dataclasses import dataclass, field
from pathlib import Path


# ---------------------------------------------------------------------------
# Default values
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).parent.parent


def _env(key: str, default: str = "") -> str:
    """Read an environment variable with AAA_ prefix, falling back to the bare key."""
    return os.environ.get(f"AAA_{key}", os.environ.get(key, default))


def _env_int(key: str, default: int) -> int:
    return int(_env(key, str(default)))


def _env_float(key: str, default: float) -> float:
    return float(_env(key, str(default)))


def _env_bool(key: str, default: bool) -> bool:  # noqa: FBT001
    val = _env(key, str(default)).lower()
    return val in ("1", "true", "yes", "on")


# ---------------------------------------------------------------------------
# Settings dataclasses
# ---------------------------------------------------------------------------

@dataclass
class CrawlerSettings:
    """Settings for the CrawlerAgent."""
    user_agent: str = field(
        default_factory=lambda: _env("CRAWLER_USER_AGENT",
            "AgenticAIArchitect/1.0 (https://github.com/BraPil/Agentic-AI-Architect)")
    )
    request_timeout: int = field(default_factory=lambda: _env_int("CRAWLER_TIMEOUT", 15))
    rate_limit_seconds: float = field(default_factory=lambda: _env_float("CRAWLER_RATE_LIMIT", 1.0))
    max_content_length: int = field(default_factory=lambda: _env_int("CRAWLER_MAX_CONTENT", 50_000))
    respect_robots_txt: bool = field(default_factory=lambda: _env_bool("CRAWLER_ROBOTS_TXT", True))


@dataclass
class LLMSettings:
    """LLM provider settings."""
    openai_api_key: str = field(default_factory=lambda: _env("OPENAI_API_KEY", ""))
    anthropic_api_key: str = field(default_factory=lambda: _env("ANTHROPIC_API_KEY", ""))
    firecrawl_api_key: str = field(default_factory=lambda: _env("FIRECRAWL_API_KEY", ""))
    default_model: str = field(default_factory=lambda: _env("DEFAULT_LLM_MODEL", "claude-3-5-haiku-20241022"))
    fast_model: str = field(default_factory=lambda: _env("FAST_LLM_MODEL", "claude-3-haiku-20240307"))
    embedding_model: str = field(default_factory=lambda: _env("EMBEDDING_MODEL", "text-embedding-3-small"))
    max_tokens: int = field(default_factory=lambda: _env_int("LLM_MAX_TOKENS", 4096))
    temperature: float = field(default_factory=lambda: _env_float("LLM_TEMPERATURE", 0.1))


@dataclass
class StorageSettings:
    """Storage path settings."""
    data_dir: Path = field(default_factory=lambda: Path(_env("DATA_DIR", str(_PROJECT_ROOT / "data"))))
    knowledge_db: str = field(default_factory=lambda: _env("KNOWLEDGE_DB", "data/knowledge_base.db"))
    vector_store_dir: str = field(default_factory=lambda: _env("VECTOR_STORE_DIR", "data/vector_store"))
    output_dir: str = field(default_factory=lambda: _env("OUTPUT_DIR", "data/output"))

    def ensure_dirs(self) -> None:
        """Create all configured directories if they don't exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        Path(self.knowledge_db).parent.mkdir(parents=True, exist_ok=True)
        Path(self.vector_store_dir).mkdir(parents=True, exist_ok=True)
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)


@dataclass
class TrendSettings:
    """Trend tracking thresholds."""
    new_trend_threshold: float = field(default_factory=lambda: _env_float("TREND_NEW_THRESHOLD", 7.0))
    decline_threshold: float = field(default_factory=lambda: _env_float("TREND_DECLINE_THRESHOLD", 5.0))
    breakthrough_delta: float = field(default_factory=lambda: _env_float("TREND_BREAKTHROUGH_DELTA", 2.0))


@dataclass
class ToolSettings:
    """Tool discovery thresholds."""
    new_tool_star_threshold: int = field(default_factory=lambda: _env_int("TOOL_STAR_THRESHOLD", 100))
    breakthrough_score_threshold: float = field(
        default_factory=lambda: _env_float("TOOL_BREAKTHROUGH_SCORE", 8.5)
    )


@dataclass
class OrchestratorSettings:
    """Orchestrator cycle settings."""
    max_cycle_errors: int = field(default_factory=lambda: _env_int("MAX_CYCLE_ERRORS", 3))
    cycle_interval_hours: float = field(default_factory=lambda: _env_float("CYCLE_INTERVAL_HOURS", 24.0))
    log_level: str = field(default_factory=lambda: _env("LOG_LEVEL", "INFO"))


@dataclass
class Settings:
    """Root settings object. Access via :func:`get_settings`."""
    crawler: CrawlerSettings = field(default_factory=CrawlerSettings)
    llm: LLMSettings = field(default_factory=LLMSettings)
    storage: StorageSettings = field(default_factory=StorageSettings)
    trends: TrendSettings = field(default_factory=TrendSettings)
    tools: ToolSettings = field(default_factory=ToolSettings)
    orchestrator: OrchestratorSettings = field(default_factory=OrchestratorSettings)

    def to_agent_configs(self) -> dict[str, dict]:
        """Produce per-agent config dicts suitable for agent constructors."""
        return {
            "crawler_config": {
                "user_agent": self.crawler.user_agent,
                "request_timeout": self.crawler.request_timeout,
                "rate_limit_seconds": self.crawler.rate_limit_seconds,
                "max_content_length": self.crawler.max_content_length,
                "respect_robots_txt": self.crawler.respect_robots_txt,
            },
            "trend_config": {
                "new_trend_threshold": self.trends.new_trend_threshold,
                "decline_threshold": self.trends.decline_threshold,
                "breakthrough_delta": self.trends.breakthrough_delta,
            },
            "tool_config": {
                "new_tool_star_threshold": self.tools.new_tool_star_threshold,
                "breakthrough_score_threshold": self.tools.breakthrough_score_threshold,
            },
            "doc_config": {
                "output_dir": self.storage.output_dir,
            },
        }


# ---------------------------------------------------------------------------
# Singleton accessor
# ---------------------------------------------------------------------------

_settings: Settings | None = None


def get_settings() -> Settings:
    """Return the global Settings singleton, loading from environment on first call."""
    global _settings  # noqa: PLW0603
    if _settings is None:
        _settings = Settings()
        _settings.storage.ensure_dirs()
    return _settings
