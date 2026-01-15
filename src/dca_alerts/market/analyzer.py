"""Drop analysis for buy signal detection."""

import logging
from datetime import datetime, timezone
from decimal import ROUND_DOWN, Decimal
from typing import Optional

from ..models import AnalysisResult, ATHRecord, IndexData, IndexSymbol, Recommendation

logger = logging.getLogger(__name__)


class DropAnalyzer:
    """Analyzes price drops from ATH."""

    def __init__(self, drop_increment: int = 5):
        """
        Initialize the analyzer.

        Args:
            drop_increment: Percentage increment for buy signals (default 5%)
        """
        if drop_increment <= 0 or drop_increment > 100:
            raise ValueError(f"drop_increment must be between 1 and 100, got {drop_increment}")
        self._increment = Decimal(drop_increment)

    def analyze(
        self,
        index_data: IndexData,
        ath_record: Optional[ATHRecord],
    ) -> tuple[AnalysisResult, Optional[ATHRecord]]:
        """
        Analyze current price against ATH.

        If no ATH record exists, current price becomes ATH.
        If current price > ATH, it becomes new ATH.

        Args:
            index_data: Current market data
            ath_record: Existing ATH record, or None if first run

        Returns:
            Tuple of (AnalysisResult, updated ATHRecord if new ATH else None)
        """
        current = index_data.current_price
        now = datetime.now(timezone.utc)

        if ath_record is None:
            logger.info(
                "No ATH record for %s, initializing with current price %.2f",
                index_data.symbol.display_name,
                current,
            )
            new_ath = ATHRecord(
                symbol=index_data.symbol,
                ath_value=current,
                ath_date=index_data.market_date,
                updated_at=now,
            )
            result = AnalysisResult(
                symbol=index_data.symbol,
                current_price=current,
                ath_value=current,
                ath_date=index_data.market_date,
                gap_percent=Decimal("0"),
                drop_tier=0,
                recommendation=Recommendation.HOLD,
                is_new_ath=True,
            )
            return result, new_ath

        ath_value = ath_record.ath_value
        ath_date = ath_record.ath_date

        if current > ath_value:
            logger.info(
                "New ATH for %s: %.2f (previous: %.2f)",
                index_data.symbol.display_name,
                current,
                ath_value,
            )
            new_ath = ATHRecord(
                symbol=index_data.symbol,
                ath_value=current,
                ath_date=index_data.market_date,
                updated_at=now,
            )
            result = AnalysisResult(
                symbol=index_data.symbol,
                current_price=current,
                ath_value=current,
                ath_date=index_data.market_date,
                gap_percent=Decimal("0"),
                drop_tier=0,
                recommendation=Recommendation.HOLD,
                is_new_ath=True,
            )
            return result, new_ath

        gap_percent = self.calculate_gap_percent(current, ath_value)
        drop_tier = self.determine_drop_tier(gap_percent)
        recommendation = Recommendation.BUY if drop_tier > 0 else Recommendation.HOLD

        logger.info(
            "%s: current=%.2f, ATH=%.2f, gap=%.2f%%, tier=%d%%, rec=%s",
            index_data.symbol.display_name,
            current,
            ath_value,
            gap_percent,
            drop_tier,
            recommendation.value,
        )

        result = AnalysisResult(
            symbol=index_data.symbol,
            current_price=current,
            ath_value=ath_value,
            ath_date=ath_date,
            gap_percent=gap_percent,
            drop_tier=drop_tier,
            recommendation=recommendation,
            is_new_ath=False,
        )
        return result, None

    def calculate_gap_percent(self, current: Decimal, ath: Decimal) -> Decimal:
        """
        Calculate percentage gap from ATH.

        Returns negative value when current is below ATH.

        Args:
            current: Current price
            ath: All-time high price

        Returns:
            Percentage gap (negative means below ATH)
        """
        if ath == 0:
            return Decimal("0")
        gap = ((current - ath) / ath) * 100
        return gap.quantize(Decimal("0.01"))

    def determine_drop_tier(self, gap_percent: Decimal) -> int:
        """
        Floor gap to nearest increment.

        Examples (5% increment):
            -4.9% -> 0 (HOLD)
            -5.0% -> 5 (BUY)
            -12.3% -> 10 (BUY)

        Args:
            gap_percent: Percentage gap from ATH (negative when below)

        Returns:
            Drop tier (0, 5, 10, 15, ...) or 0 if above threshold
        """
        if gap_percent >= 0:
            return 0

        drop = abs(gap_percent)
        tier = int((drop / self._increment).quantize(Decimal("1"), rounding=ROUND_DOWN))
        return tier * int(self._increment)
