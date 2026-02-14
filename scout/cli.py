"""CLI command handler."""

import argparse
import logging
import sys
from pathlib import Path

from scout.config.settings import load_config
from scout.pipeline.runner import ScoutPipeline
from scout.utils.logger import setup_logger


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Startup Outreach Scout - Automated networking candidate discovery",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "command",
        choices=["run"],
        help="Command to execute",
    )

    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )

    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )

    args = parser.parse_args()

    # Setup logging
    logger = setup_logger(level=args.log_level)

    # Check if config file exists
    if not Path(args.config).exists():
        logger.error(f"Configuration file not found: {args.config}")
        logger.info("Please create a config.yaml file. See config.yaml template for reference.")
        return 1

    try:
        # Load configuration
        config = load_config(args.config)

        # Run pipeline
        if args.command == "run":
            pipeline = ScoutPipeline(config)
            pipeline.run()

        return 0

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
