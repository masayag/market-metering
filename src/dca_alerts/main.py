"""Main entry point and orchestrator for DCA alerts."""

import argparse
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .config import AppConfig, ConfigurationError, configure_logging, load_config
from .market.analyzer import DropAnalyzer
from .market.fetcher import MarketDataError, YFinanceFetcher
from .models import AnalysisResult, Report
from .notification.console_notifier import ConsoleNotifier
from .notification.email_notifier import EmailNotifier
from .persistence.ath_store import ATHStore
from .utils.colors import set_color_mode

logger = logging.getLogger(__name__)

# Exit codes
EXIT_SUCCESS = 0
EXIT_PARTIAL = 1
EXIT_FAILURE = 2


def run(config: AppConfig) -> int:
    """
    Execute the DCA alert check.

    Args:
        config: Application configuration

    Returns:
        Exit code (0=success, 1=partial, 2=failure)
    """
    logger.info("Starting DCA alerts check")
    logger.info("Monitoring indices: %s", ", ".join(i.display_name for i in config.indices))

    fetcher = YFinanceFetcher(timeout_seconds=config.fetch_timeout_seconds)
    analyzer = DropAnalyzer(drop_increment=config.drop_increment)
    store = ATHStore(config.ath_storage_path)

    index_data_list = fetcher.fetch_all(list(config.indices))

    if not index_data_list:
        logger.error("Failed to fetch any market data")
        return EXIT_FAILURE

    ath_records = store.get_all()

    # Fetch historical ATH for any missing records
    for index_data in index_data_list:
        if index_data.symbol not in ath_records:
            logger.info(
                "No ATH record for %s, fetching historical ATH...",
                index_data.symbol.display_name,
            )
            try:
                historical_ath = fetcher.fetch_ath(index_data.symbol)
                store.update(historical_ath)
                ath_records[index_data.symbol] = historical_ath
            except MarketDataError as e:
                logger.warning(
                    "Failed to fetch historical ATH for %s: %s. Using current price.",
                    index_data.symbol.display_name,
                    e,
                )

    results: list[AnalysisResult] = []
    for index_data in index_data_list:
        ath_record = ath_records.get(index_data.symbol)
        result, new_ath = analyzer.analyze(index_data, ath_record)
        results.append(result)

        if new_ath:
            store.update(new_ath)

    market_date = index_data_list[0].market_date
    report = Report(
        generated_at=datetime.now(timezone.utc),
        market_date=market_date,
        results=tuple(results),
    )

    console = ConsoleNotifier()
    console_success = console.send(report)

    email_success = True
    if config.email:
        email_notifier = EmailNotifier(config.email)
        email_success = email_notifier.send(report)
    else:
        logger.info("Email notifications disabled (no SMTP configuration)")

    if report.has_buy_signals:
        logger.info("Buy signals detected for %d index(es)", sum(
            1 for r in results if r.recommendation.value == "BUY"
        ))
    else:
        logger.info("No buy signals - all indices within threshold")

    if console_success and email_success:
        return EXIT_SUCCESS
    if console_success or email_success:
        return EXIT_PARTIAL
    return EXIT_FAILURE


def main(args: Optional[list[str]] = None) -> int:
    """
    Main entry point.

    Args:
        args: Command line arguments (defaults to sys.argv)

    Returns:
        Exit code
    """
    parser = argparse.ArgumentParser(
        description="DCA Market Drop Alert Service",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exit codes:
  0  Success - all indices fetched, all notifications sent
  1  Partial - some indices failed OR email failed
  2  Failure - no market data retrieved OR critical error

Examples:
  %(prog)s                      # Run with defaults
  %(prog)s -c config/config.yaml  # Use custom config file
  %(prog)s --no-color            # Run without colored output
        """,
    )
    parser.add_argument(
        "-c", "--config",
        type=Path,
        help="Path to YAML configuration file",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging (DEBUG level)",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output",
    )

    parsed = parser.parse_args(args)

    try:
        config = load_config(parsed.config)
    except ConfigurationError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        return EXIT_FAILURE

    # Configure color settings
    force_color = False if parsed.no_color else None
    set_color_mode(force_color=force_color)

    log_level = "DEBUG" if parsed.verbose else config.log_level
    configure_logging(log_level, force_color)

    try:
        return run(config)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return EXIT_FAILURE
    except Exception as e:
        logger.exception("Unexpected error: %s", e)
        return EXIT_FAILURE


if __name__ == "__main__":
    sys.exit(main())
