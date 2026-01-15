"""Market data fetching using yfinance."""

import logging
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Protocol

import yfinance as yf

from ..models import ATHRecord, IndexData, IndexSymbol

logger = logging.getLogger(__name__)


class MarketDataError(Exception):
    """Raised when market data cannot be retrieved."""


class MarketDataFetcher(Protocol):
    """Protocol for fetching market data."""

    def fetch(self, symbol: IndexSymbol) -> IndexData:
        """Fetch current price for the given index."""
        ...

    def fetch_all(self, symbols: list[IndexSymbol]) -> list[IndexData]:
        """Fetch current prices for all given indices."""
        ...


class YFinanceFetcher:
    """yfinance implementation of MarketDataFetcher."""

    def __init__(self, timeout_seconds: int = 30):
        self._timeout = timeout_seconds

    def fetch(self, symbol: IndexSymbol) -> IndexData:
        """
        Fetch current price for the given index.

        Args:
            symbol: The index symbol to fetch

        Returns:
            IndexData with current price information

        Raises:
            MarketDataError: If data cannot be retrieved
        """
        try:
            ticker = yf.Ticker(symbol.value)
            hist = ticker.history(period="1d")

            if hist.empty:
                raise MarketDataError(
                    f"No data returned for {symbol.value}. "
                    "Market may be closed or symbol invalid."
                )

            latest = hist.iloc[-1]
            price = Decimal(str(latest["Close"]))
            market_date = hist.index[-1].date()

            return IndexData(
                symbol=symbol,
                current_price=price,
                fetched_at=datetime.now(timezone.utc),
                market_date=market_date,
            )

        except MarketDataError:
            raise
        except Exception as e:
            logger.exception("Failed to fetch data for %s", symbol.value)
            raise MarketDataError(f"Failed to fetch {symbol.value}: {e}") from e

    def fetch_all(self, symbols: list[IndexSymbol]) -> list[IndexData]:
        """
        Fetch current prices for all given indices.

        Returns partial results on individual failures.

        Args:
            symbols: List of index symbols to fetch

        Returns:
            List of IndexData for successfully fetched symbols
        """
        results = []
        for symbol in symbols:
            try:
                data = self.fetch(symbol)
                results.append(data)
                logger.info(
                    "Fetched %s: %.2f (date: %s)",
                    symbol.display_name,
                    data.current_price,
                    data.market_date,
                )
            except MarketDataError as e:
                logger.error("Failed to fetch %s: %s", symbol.display_name, e)
        return results

    def fetch_ath(self, symbol: IndexSymbol, period: str = "max") -> ATHRecord:
        """
        Fetch the all-time high for an index from historical data.

        Args:
            symbol: The index symbol to fetch
            period: Historical period to search (default "max" for all available data)

        Returns:
            ATHRecord with the historical ATH

        Raises:
            MarketDataError: If data cannot be retrieved
        """
        try:
            ticker = yf.Ticker(symbol.value)
            hist = ticker.history(period=period)

            if hist.empty:
                raise MarketDataError(
                    f"No historical data returned for {symbol.value}."
                )

            ath_idx = hist["High"].idxmax()
            ath_value = Decimal(str(hist.loc[ath_idx, "High"]))
            ath_date = ath_idx.date()

            logger.info(
                "Fetched historical ATH for %s: %.2f on %s",
                symbol.display_name,
                ath_value,
                ath_date,
            )

            return ATHRecord(
                symbol=symbol,
                ath_value=ath_value,
                ath_date=ath_date,
                updated_at=datetime.now(timezone.utc),
            )

        except MarketDataError:
            raise
        except Exception as e:
            logger.exception("Failed to fetch ATH for %s", symbol.value)
            raise MarketDataError(f"Failed to fetch ATH for {symbol.value}: {e}") from e
