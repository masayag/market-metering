"""Colored logging utilities."""

import logging
from typing import Optional

from .colors import ANSIColors, ColorFormatter


class ColoredLogFormatter(logging.Formatter):
    """Log formatter that adds colors to log levels."""

    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
        force_color: Optional[bool] = None,
    ) -> None:
        """
        Initialize colored log formatter.

        Args:
            fmt: Log format string
            datefmt: Date format string
            force_color: Override color detection
        """
        super().__init__(fmt, datefmt)
        self.color_formatter = ColorFormatter(force_color)

        # Define colors for each log level
        self.level_colors = {
            logging.CRITICAL: (ANSIColors.BRIGHT_RED, ANSIColors.BOLD),
            logging.ERROR: (ANSIColors.RED, ANSIColors.BOLD),
            logging.WARNING: (ANSIColors.YELLOW,),
            logging.INFO: (ANSIColors.BLUE,),
            logging.DEBUG: (ANSIColors.BRIGHT_BLACK,),
        }

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        # Get the original formatted message
        message = super().format(record)

        # Apply color to log level if supported
        if record.levelno in self.level_colors:
            colors = self.level_colors[record.levelno]

            # Find and color the log level part
            level_name = record.levelname
            if level_name in message:
                colored_level = self.color_formatter.format(level_name, *colors)
                message = message.replace(level_name, colored_level, 1)

        return message


def setup_colored_logging(
    level: str = "INFO",
    force_color: Optional[bool] = None,
) -> None:
    """
    Setup colored logging for the application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        force_color: Override color detection
    """
    # Create colored formatter
    formatter = ColoredLogFormatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
        force_color=force_color,
    )

    # Get root logger and clear existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    # Create console handler with colored formatter
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        handlers=[console_handler],
    )