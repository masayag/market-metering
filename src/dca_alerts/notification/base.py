"""Base notifier protocol."""

from typing import Protocol

from ..models import Report


class Notifier(Protocol):
    """Protocol for sending reports."""

    def send(self, report: Report) -> bool:
        """
        Send the report.

        Args:
            report: The report to send

        Returns:
            True if successful, False otherwise

        Note:
            Implementations should log failures, not raise exceptions.
        """
        ...
