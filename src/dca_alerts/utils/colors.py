"""ANSI color utilities for terminal output."""

import os
import sys
from typing import Optional


class ANSIColors:
    """ANSI color codes for terminal output."""

    # Reset
    RESET = "\033[0m"

    # Regular colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Bright colors
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    # Styles
    BOLD = "\033[1m"
    DIM = "\033[2m"
    UNDERLINE = "\033[4m"


class ColorFormatter:
    """Handles colored text formatting with terminal support detection."""

    def __init__(self, force_color: Optional[bool] = None) -> None:
        """
        Initialize color formatter.

        Args:
            force_color: Override color detection. None = auto-detect,
                        True = always use colors, False = never use colors
        """
        self._force_color = force_color
        self._color_support = self._detect_color_support()

    def _detect_color_support(self) -> bool:
        """Detect if the terminal supports ANSI colors."""
        if self._force_color is not None:
            return self._force_color

        # Check if output is redirected (not a tty)
        if not sys.stdout.isatty():
            return False

        # Check environment variables
        term = os.getenv("TERM", "").lower()
        colorterm = os.getenv("COLORTERM", "").lower()

        # Common terminals that support color
        if any(t in term for t in ["color", "ansi", "xterm", "screen", "tmux"]):
            return True

        if colorterm in ["truecolor", "24bit"]:
            return True

        # Check for explicit color support
        if os.getenv("FORCE_COLOR") or os.getenv("CLICOLOR_FORCE"):
            return True

        # Disable if explicitly set
        if os.getenv("NO_COLOR") or os.getenv("CLICOLOR") == "0":
            return False

        # Default to True for most modern terminals
        return True

    def format(self, text: str, *colors: str) -> str:
        """
        Apply color formatting to text.

        Args:
            text: Text to format
            *colors: ANSI color/style codes to apply

        Returns:
            Formatted text with colors if supported, plain text otherwise
        """
        if not self._color_support or not colors:
            return text

        prefix = "".join(colors)
        return f"{prefix}{text}{ANSIColors.RESET}"

    def header(self, text: str) -> str:
        """Format text as a header."""
        return self.format(text, ANSIColors.BRIGHT_CYAN, ANSIColors.BOLD)

    def index_name(self, text: str) -> str:
        """Format text as an index name."""
        return self.format(text, ANSIColors.BRIGHT_WHITE, ANSIColors.BOLD)

    def ath_value(self, text: str) -> str:
        """Format text as ATH value."""
        return self.format(text, ANSIColors.BLUE)

    def current_price(self, text: str) -> str:
        """Format text as current price."""
        return self.format(text, ANSIColors.WHITE)

    def gap_positive(self, text: str) -> str:
        """Format positive gap percentage."""
        return self.format(text, ANSIColors.GREEN)

    def gap_negative(self, text: str) -> str:
        """Format negative gap percentage."""
        return self.format(text, ANSIColors.RED)

    def buy_signal(self, text: str) -> str:
        """Format BUY signal."""
        return self.format(text, ANSIColors.BRIGHT_GREEN, ANSIColors.BOLD)

    def hold_signal(self, text: str) -> str:
        """Format HOLD signal."""
        return self.format(text, ANSIColors.YELLOW)

    def new_ath(self, text: str) -> str:
        """Format NEW ATH signal."""
        return self.format(text, ANSIColors.BRIGHT_MAGENTA, ANSIColors.BOLD)

    def action_required(self, text: str) -> str:
        """Format action required message."""
        return self.format(text, ANSIColors.BRIGHT_RED, ANSIColors.BOLD)

    def no_action(self, text: str) -> str:
        """Format no action message."""
        return self.format(text, ANSIColors.GREEN)


# Global formatter instance
_formatter: Optional[ColorFormatter] = None


def get_formatter() -> ColorFormatter:
    """Get the global color formatter instance."""
    global _formatter
    if _formatter is None:
        _formatter = ColorFormatter()
    return _formatter


def set_color_mode(force_color: Optional[bool] = None) -> None:
    """
    Configure global color mode.

    Args:
        force_color: None = auto-detect, True = force on, False = force off
    """
    global _formatter
    _formatter = ColorFormatter(force_color)