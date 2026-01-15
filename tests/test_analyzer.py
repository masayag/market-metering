"""Tests for drop analyzer."""

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from dca_alerts.market.analyzer import DropAnalyzer
from dca_alerts.models import ATHRecord, IndexData, IndexSymbol, Recommendation


class TestDropAnalyzer:
    """Tests for DropAnalyzer class."""

    def test_calculate_gap_percent_below_ath(self):
        """Test gap calculation when price is below ATH."""
        analyzer = DropAnalyzer(drop_increment=5)
        gap = analyzer.calculate_gap_percent(
            current=Decimal("5700"),
            ath=Decimal("6000"),
        )
        assert gap == Decimal("-5.00")

    def test_calculate_gap_percent_above_ath(self):
        """Test gap calculation when price is above ATH."""
        analyzer = DropAnalyzer(drop_increment=5)
        gap = analyzer.calculate_gap_percent(
            current=Decimal("6300"),
            ath=Decimal("6000"),
        )
        assert gap == Decimal("5.00")

    def test_calculate_gap_percent_at_ath(self):
        """Test gap calculation when price equals ATH."""
        analyzer = DropAnalyzer(drop_increment=5)
        gap = analyzer.calculate_gap_percent(
            current=Decimal("6000"),
            ath=Decimal("6000"),
        )
        assert gap == Decimal("0.00")

    def test_determine_drop_tier_no_drop(self):
        """Test tier for drops below threshold."""
        analyzer = DropAnalyzer(drop_increment=5)
        assert analyzer.determine_drop_tier(Decimal("-4.99")) == 0

    def test_determine_drop_tier_at_threshold(self):
        """Test tier at exact 5% threshold."""
        analyzer = DropAnalyzer(drop_increment=5)
        assert analyzer.determine_drop_tier(Decimal("-5.00")) == 5

    def test_determine_drop_tier_between_thresholds(self):
        """Test tier between thresholds floors down."""
        analyzer = DropAnalyzer(drop_increment=5)
        assert analyzer.determine_drop_tier(Decimal("-12.30")) == 10

    def test_determine_drop_tier_large_drop(self):
        """Test tier for large drops."""
        analyzer = DropAnalyzer(drop_increment=5)
        assert analyzer.determine_drop_tier(Decimal("-25.50")) == 25

    def test_determine_drop_tier_positive_gap(self):
        """Test tier returns 0 for positive gaps."""
        analyzer = DropAnalyzer(drop_increment=5)
        assert analyzer.determine_drop_tier(Decimal("5.00")) == 0

    def test_analyze_no_existing_ath(self):
        """Test analysis when no ATH record exists."""
        analyzer = DropAnalyzer(drop_increment=5)
        index_data = IndexData(
            symbol=IndexSymbol.SP500,
            current_price=Decimal("5700.00"),
            fetched_at=datetime(2025, 1, 15, 18, 0, 0, tzinfo=timezone.utc),
            market_date=date(2025, 1, 15),
        )

        result, new_ath = analyzer.analyze(index_data, None)

        assert result.is_new_ath is True
        assert result.recommendation == Recommendation.HOLD
        assert result.gap_percent == Decimal("0")
        assert new_ath is not None
        assert new_ath.ath_value == Decimal("5700.00")

    def test_analyze_new_ath(self):
        """Test analysis when current price exceeds ATH."""
        analyzer = DropAnalyzer(drop_increment=5)
        index_data = IndexData(
            symbol=IndexSymbol.SP500,
            current_price=Decimal("6100.00"),
            fetched_at=datetime(2025, 1, 15, 18, 0, 0, tzinfo=timezone.utc),
            market_date=date(2025, 1, 15),
        )
        ath_record = ATHRecord(
            symbol=IndexSymbol.SP500,
            ath_value=Decimal("6000.00"),
            ath_date=date(2025, 1, 10),
            updated_at=datetime(2025, 1, 10, 18, 0, 0, tzinfo=timezone.utc),
        )

        result, new_ath = analyzer.analyze(index_data, ath_record)

        assert result.is_new_ath is True
        assert result.recommendation == Recommendation.HOLD
        assert new_ath is not None
        assert new_ath.ath_value == Decimal("6100.00")

    def test_analyze_buy_signal(self):
        """Test analysis generates buy signal at 5% drop."""
        analyzer = DropAnalyzer(drop_increment=5)
        index_data = IndexData(
            symbol=IndexSymbol.SP500,
            current_price=Decimal("5700.00"),
            fetched_at=datetime(2025, 1, 15, 18, 0, 0, tzinfo=timezone.utc),
            market_date=date(2025, 1, 15),
        )
        ath_record = ATHRecord(
            symbol=IndexSymbol.SP500,
            ath_value=Decimal("6000.00"),
            ath_date=date(2025, 1, 10),
            updated_at=datetime(2025, 1, 10, 18, 0, 0, tzinfo=timezone.utc),
        )

        result, new_ath = analyzer.analyze(index_data, ath_record)

        assert result.is_new_ath is False
        assert result.recommendation == Recommendation.BUY
        assert result.drop_tier == 5
        assert result.gap_percent == Decimal("-5.00")
        assert new_ath is None

    def test_analyze_hold_signal(self):
        """Test analysis generates hold signal below threshold."""
        analyzer = DropAnalyzer(drop_increment=5)
        index_data = IndexData(
            symbol=IndexSymbol.SP500,
            current_price=Decimal("5850.00"),
            fetched_at=datetime(2025, 1, 15, 18, 0, 0, tzinfo=timezone.utc),
            market_date=date(2025, 1, 15),
        )
        ath_record = ATHRecord(
            symbol=IndexSymbol.SP500,
            ath_value=Decimal("6000.00"),
            ath_date=date(2025, 1, 10),
            updated_at=datetime(2025, 1, 10, 18, 0, 0, tzinfo=timezone.utc),
        )

        result, new_ath = analyzer.analyze(index_data, ath_record)

        assert result.recommendation == Recommendation.HOLD
        assert result.drop_tier == 0
        assert new_ath is None

    def test_custom_drop_increment(self):
        """Test analyzer with custom drop increment."""
        analyzer = DropAnalyzer(drop_increment=10)
        assert analyzer.determine_drop_tier(Decimal("-9.99")) == 0
        assert analyzer.determine_drop_tier(Decimal("-10.00")) == 10
        assert analyzer.determine_drop_tier(Decimal("-25.50")) == 20

    def test_invalid_drop_increment(self):
        """Test analyzer rejects invalid increment."""
        with pytest.raises(ValueError):
            DropAnalyzer(drop_increment=0)

        with pytest.raises(ValueError):
            DropAnalyzer(drop_increment=101)
