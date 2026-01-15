"""Configuration loading and validation."""

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

from .models import IndexSymbol

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when configuration is invalid or incomplete."""


@dataclass(frozen=True)
class EmailConfig:
    """Email/SMTP configuration."""

    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    sender_email: str
    recipient_email: str
    use_tls: bool = True


@dataclass(frozen=True)
class AppConfig:
    """Application configuration."""

    indices: tuple[IndexSymbol, ...]
    ath_storage_path: Path
    drop_increment: int
    fetch_timeout_seconds: int
    email: Optional[EmailConfig]
    log_level: str


def _get_env(key: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    """Get environment variable with optional default and required validation."""
    value = os.environ.get(key, default)
    if required and not value:
        raise ConfigurationError(f"Required environment variable {key} is not set")
    return value


def _get_env_int(key: str, default: int) -> int:
    """Get integer environment variable."""
    value = os.environ.get(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError as e:
        raise ConfigurationError(f"Environment variable {key} must be an integer: {value}") from e


def _get_env_bool(key: str, default: bool) -> bool:
    """Get boolean environment variable."""
    value = os.environ.get(key)
    if value is None:
        return default
    return value.lower() in ("true", "1", "yes", "on")


def _load_yaml_config(config_path: Optional[Path]) -> dict:
    """Load YAML configuration file if it exists."""
    if config_path is None:
        return {}

    if not config_path.exists():
        logger.debug("Config file not found at %s, using defaults", config_path)
        return {}

    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
            return config if config else {}
    except yaml.YAMLError as e:
        raise ConfigurationError(f"Invalid YAML in config file {config_path}: {e}") from e


def _parse_indices(yaml_config: dict) -> tuple[IndexSymbol, ...]:
    """Parse indices from YAML config or return defaults."""
    yaml_indices = yaml_config.get("indices", [])

    if yaml_indices:
        indices = []
        for item in yaml_indices:
            symbol_str = item.get("symbol") if isinstance(item, dict) else item
            for idx in IndexSymbol:
                if idx.value == symbol_str:
                    indices.append(idx)
                    break
            else:
                logger.warning("Unknown index symbol: %s, skipping", symbol_str)
        if indices:
            return tuple(indices)

    return tuple(IndexSymbol)


def _build_email_config(yaml_config: dict) -> Optional[EmailConfig]:
    """Build email configuration from env vars and YAML."""
    yaml_email = yaml_config.get("email", {})

    smtp_user = _get_env("DCA_SMTP_USER")
    smtp_password = _get_env("DCA_SMTP_PASSWORD")
    sender_email = _get_env("DCA_SENDER_EMAIL")
    recipient_email = _get_env("DCA_RECIPIENT_EMAIL")

    if not all([smtp_user, smtp_password, sender_email, recipient_email]):
        logger.info("Email configuration incomplete, email notifications disabled")
        return None

    return EmailConfig(
        smtp_host=_get_env("DCA_SMTP_HOST") or yaml_email.get("smtp_host", "smtp.gmail.com"),
        smtp_port=_get_env_int("DCA_SMTP_PORT", yaml_email.get("smtp_port", 587)),
        smtp_user=smtp_user,
        smtp_password=smtp_password,
        sender_email=sender_email,
        recipient_email=recipient_email,
        use_tls=_get_env_bool("DCA_SMTP_USE_TLS", yaml_email.get("use_tls", True)),
    )


def load_config(config_path: Optional[Path] = None) -> AppConfig:
    """
    Load configuration from environment variables and optional YAML file.

    Environment variables take precedence over YAML configuration.

    Args:
        config_path: Optional path to YAML configuration file

    Returns:
        Validated AppConfig instance

    Raises:
        ConfigurationError: If required configuration is missing or invalid
    """
    yaml_config = _load_yaml_config(config_path)
    yaml_storage = yaml_config.get("storage", {})
    yaml_analysis = yaml_config.get("analysis", {})
    yaml_market = yaml_config.get("market", {})
    yaml_logging = yaml_config.get("logging", {})

    ath_path_str = _get_env("DCA_ATH_STORAGE_PATH") or yaml_storage.get(
        "ath_path", "./data/ath_records.json"
    )
    ath_storage_path = Path(ath_path_str)

    drop_increment = _get_env_int(
        "DCA_DROP_INCREMENT", yaml_analysis.get("drop_increment", 5)
    )
    if drop_increment <= 0 or drop_increment > 100:
        raise ConfigurationError(
            f"drop_increment must be between 1 and 100, got {drop_increment}"
        )

    fetch_timeout = _get_env_int(
        "DCA_FETCH_TIMEOUT_SECONDS", yaml_market.get("fetch_timeout_seconds", 30)
    )

    log_level = _get_env("DCA_LOG_LEVEL") or yaml_logging.get("level", "INFO")

    return AppConfig(
        indices=_parse_indices(yaml_config),
        ath_storage_path=ath_storage_path,
        drop_increment=drop_increment,
        fetch_timeout_seconds=fetch_timeout,
        email=_build_email_config(yaml_config),
        log_level=log_level,
    )


def configure_logging(level: str, force_color: Optional[bool] = None) -> None:
    """Configure colored logging for the application."""
    from .utils.logging import setup_colored_logging

    setup_colored_logging(level, force_color)
