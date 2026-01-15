"""Console notifier for terminal output."""

import logging
import sys

from ..models import Report

logger = logging.getLogger(__name__)


class ConsoleNotifier:
    """Prints report to stdout."""

    def send(self, report: Report) -> bool:
        """
        Print the report to stdout.

        Args:
            report: The report to print

        Returns:
            True if successful, False on write error
        """
        try:
            text = report.to_text()
            print(text, file=sys.stdout)
            sys.stdout.flush()
            logger.debug("Report printed to console")
            return True
        except OSError as e:
            logger.error("Failed to write to stdout: %s", e)
            return False
