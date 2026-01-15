"""Core data models for DCA alerts."""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from .utils.colors import get_formatter


class IndexSymbol(Enum):
    """Supported market indices."""

    SP500 = "^GSPC"
    NASDAQ100 = "^NDX"
    RUSSELL2000 = "^RUT"

    @property
    def display_name(self) -> str:
        """Human-readable name for the index."""
        names = {
            IndexSymbol.SP500: "S&P 500",
            IndexSymbol.NASDAQ100: "NASDAQ 100",
            IndexSymbol.RUSSELL2000: "Russell 2000",
        }
        return names[self]


class Recommendation(Enum):
    """Buy recommendation status."""

    BUY = "BUY"
    HOLD = "HOLD"


@dataclass(frozen=True)
class IndexData:
    """Current market data for an index."""

    symbol: IndexSymbol
    current_price: Decimal
    fetched_at: datetime
    market_date: date


@dataclass(frozen=True)
class ATHRecord:
    """Persisted ATH record for an index."""

    symbol: IndexSymbol
    ath_value: Decimal
    ath_date: date
    updated_at: datetime


@dataclass(frozen=True)
class AnalysisResult:
    """Analysis output for a single index."""

    symbol: IndexSymbol
    current_price: Decimal
    ath_value: Decimal
    ath_date: date
    gap_percent: Decimal
    drop_tier: int
    recommendation: Recommendation
    is_new_ath: bool

    def format_recommendation(self) -> str:
        """Format recommendation for display with colors (for console)."""
        formatter = get_formatter()

        if self.is_new_ath:
            return formatter.new_ath("NEW ATH - HOLD")
        if self.recommendation == Recommendation.BUY:
            if self.drop_tier > 5:
                return formatter.buy_signal(f">>> BUY SIGNAL ({self.drop_tier}% tier) <<<")
            return formatter.buy_signal(">>> BUY SIGNAL <<<")
        return formatter.hold_signal("HOLD - below 5% threshold")

    def format_recommendation_plain(self) -> str:
        """Format recommendation for display without colors (for email)."""
        if self.is_new_ath:
            return "NEW ATH - HOLD"
        if self.recommendation == Recommendation.BUY:
            if self.drop_tier > 5:
                return f">>> BUY SIGNAL ({self.drop_tier}% tier) <<<"
            return ">>> BUY SIGNAL <<<"
        return "HOLD - below 5% threshold"


@dataclass(frozen=True)
class Report:
    """Complete report for all indices."""

    generated_at: datetime
    market_date: date
    results: tuple[AnalysisResult, ...]

    @property
    def has_buy_signals(self) -> bool:
        """Check if any index has a buy signal."""
        return any(r.recommendation == Recommendation.BUY for r in self.results)

    def to_text(self) -> str:
        """Render report as colorized text."""
        formatter = get_formatter()

        lines = [
            formatter.header(f"=== DCA Market Alert - {self.market_date.strftime('%Y-%m-%d')} ==="),
            "",
        ]

        for result in self.results:
            # Format index name
            index_line = formatter.index_name(f"{result.symbol.display_name} ({result.symbol.value})")

            # Format ATH value
            ath_line = f"  ATH:     {formatter.ath_value(f'${result.ath_value:,.2f}')} ({result.ath_date.strftime('%Y-%m-%d')})"

            # Format current price
            current_line = f"  Current: {formatter.current_price(f'${result.current_price:,.2f}')}"

            # Format gap with appropriate color
            gap_text = f"{result.gap_percent:+.2f}%"
            if result.gap_percent >= 0:
                gap_colored = formatter.gap_positive(gap_text)
            else:
                gap_colored = formatter.gap_negative(gap_text)
            gap_line = f"  Gap:     {gap_colored}"

            # Format recommendation (already colored in format_recommendation method)
            rec_line = f"  {result.format_recommendation()}"

            lines.extend([
                index_line,
                ath_line,
                current_line,
                gap_line,
                rec_line,
                "",
            ])

        # Format final action message
        if self.has_buy_signals:
            lines.append(formatter.action_required("ACTION REQUIRED: One or more indices have buy signals."))
        else:
            lines.append(formatter.no_action("No action required at this time."))

        return "\n".join(lines)

    def to_html(self) -> str:
        """Render report as HTML for email."""
        rows = []
        for result in self.results:
            rec_class = "buy" if result.recommendation == Recommendation.BUY else "hold"
            rows.append(f"""
            <tr>
                <td><strong>{result.symbol.display_name}</strong><br>
                    <small>{result.symbol.value}</small></td>
                <td>{result.ath_value:,.2f}<br>
                    <small>{result.ath_date.strftime('%Y-%m-%d')}</small></td>
                <td>{result.current_price:,.2f}</td>
                <td>{result.gap_percent:+.2f}%</td>
                <td class="{rec_class}">{result.format_recommendation_plain()}</td>
            </tr>
            """)

        action_msg = (
            '<p style="color: green; font-weight: bold;">'
            "ACTION REQUIRED: One or more indices have buy signals.</p>"
            if self.has_buy_signals
            else '<p style="color: gray;">No action required at this time.</p>'
        )

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background-color: #4a90d9; color: white; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                .buy {{ color: green; font-weight: bold; }}
                .hold {{ color: gray; }}
                h1 {{ color: #333; }}
            </style>
        </head>
        <body>
            <h1>DCA Market Alert - {self.market_date.strftime('%Y-%m-%d')}</h1>
            <table>
                <tr>
                    <th>Index</th>
                    <th>ATH</th>
                    <th>Current</th>
                    <th>Gap</th>
                    <th>Recommendation</th>
                </tr>
                {"".join(rows)}
            </table>
            {action_msg}
            <hr>
            <small>Generated at {self.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</small>
        </body>
        </html>
        """
