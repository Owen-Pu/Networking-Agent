"""Configuration loading and management."""

import os
import logging
from pathlib import Path
from typing import Optional
import yaml
from dotenv import load_dotenv

from scout.models.config import ScoutConfig

logger = logging.getLogger(__name__)


def load_config(config_path: str = "config.yaml") -> ScoutConfig:
    """
    Load and validate configuration from YAML file.

    Args:
        config_path: Path to YAML configuration file

    Returns:
        Validated ScoutConfig instance

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config is invalid
    """
    # Load environment variables from .env
    load_dotenv()

    # Check if config file exists
    if not Path(config_path).exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    # Load YAML config
    try:
        with open(config_path, "r") as f:
            config_dict = yaml.safe_load(f)
    except Exception as e:
        raise ValueError(f"Failed to parse YAML config: {e}")

    # Validate with Pydantic
    try:
        config = ScoutConfig(**config_dict)
        logger.info(f"Successfully loaded config from {config_path}")
        logger.info(f"  - {len(config.rss_feeds)} RSS feeds")
        logger.info(f"  - {len(config.keywords.include)} include keywords")
        logger.info(f"  - {len(config.keywords.exclude)} exclude keywords")
        logger.info(f"  - Output format: {config.output_format}")
        return config
    except Exception as e:
        raise ValueError(f"Invalid configuration: {e}")


def get_database_path() -> str:
    """Get path to SQLite database."""
    db_dir = Path("data")
    db_dir.mkdir(exist_ok=True)
    return str(db_dir / "scout.db")


def get_output_path(filename: str = "output.csv") -> str:
    """Get path for output file."""
    output_dir = Path("data/output")
    output_dir.mkdir(parents=True, exist_ok=True)
    return str(output_dir / filename)
