"""Tests for data models."""

from datetime import date, datetime, timezone
from decimal import Decimal

from dca_alerts.models import AnalysisResult, IndexSymbol, Recommendation, Report


class TestIndexSymbol:
    """Tests for IndexSymbol enum."""

    def test_display_names(self):
        """Test display names are correct."""
        assert IndexSymbol.SP500.display_name == "S&P 500"
        assert IndexSymbol.NASDAQ100.display_name == "NASDAQ 100"
        assert IndexSymbol.RUSSELL2000.display_name == "Russell 2000"

    def test_values(self):
        """Test symbol values are correct."""
        assert IndexSymbol.SP500.value == "^GSPC"
        assert IndexSymbol.NASDAQ100.value == "^NDX"
        assert IndexSymbol.RUSSELL2000.value == "^RUT"


class TestAnalysisResult:
    """Tests for AnalysisResult class."""

    def test_format_recommendation_buy(self):
        """Test formatting buy recommendation."""
        result = AnalysisResult(
            symbol=IndexSymbol.SP500,
            current_price=Decimal("5700.00"),
            ath_value=Decimal("6000.00"),
            ath_date=date(2025, 1, 10),
            gap_percent=Decimal("-5.00"),
            drop_tier=5,
            recommendation=Recommendation.BUY,
            is_new_ath=False,
        )
        assert result.format_recommendation() == ">>> BUY SIGNAL <<<"

    def test_format_recommendation_buy_higher_tier(self):
        """Test formatting buy recommendation at higher tier."""
        result = AnalysisResult(
            symbol=IndexSymbol.SP500,
            current_price=Decimal("5400.00"),
            ath_value=Decimal("6000.00"),
            ath_date=date(2025, 1, 10),
            gap_percent=Decimal("-10.00"),
            drop_tier=10,
            recommendation=Recommendation.BUY,
            is_new_ath=False,
        )
        assert result.format_recommendation() == ">>> BUY SIGNAL (10% tier) <<<"

    def test_format_recommendation_hold(self):
        """Test formatting hold recommendation."""
        result = AnalysisResult(
            symbol=IndexSymbol.SP500,
            current_price=Decimal("5850.00"),
            ath_value=Decimal("6000.00"),
            ath_date=date(2025, 1, 10),
            gap_percent=Decimal("-2.50"),
            drop_tier=0,
            recommendation=Recommendation.HOLD,
            is_new_ath=False,
        )
        assert result.format_recommendation() == "HOLD - below 5% threshold"

    def test_format_recommendation_new_ath(self):
        """Test formatting new ATH."""
        result = AnalysisResult(
            symbol=IndexSymbol.SP500,
            current_price=Decimal("6100.00"),
            ath_value=Decimal("6100.00"),
            ath_date=date(2025, 1, 15),
            gap_percent=Decimal("0"),
            drop_tier=0,
            recommendation=Recommendation.HOLD,
            is_new_ath=True,
        )
        assert result.format_recommendation() == "NEW ATH - HOLD"


class TestReport:
    """Tests for Report class."""

    def test_has_buy_signals_true(self):
        """Test has_buy_signals returns True when buy signal exists."""
        results = (
            AnalysisResult(
                symbol=IndexSymbol.SP500,
                current_price=Decimal("5700.00"),
                ath_value=Decimal("6000.00"),
                ath_date=date(2025, 1, 10),
                gap_percent=Decimal("-5.00"),
                drop_tier=5,
                recommendation=Recommendation.BUY,
                is_new_ath=False,
            ),
        )
        report = Report(
            generated_at=datetime(2025, 1, 15, 18, 0, 0, tzinfo=timezone.utc),
            market_date=date(2025, 1, 15),
            results=results,
        )
        assert report.has_buy_signals is True

    def test_has_buy_signals_false(self):
        """Test has_buy_signals returns False when no buy signals."""
        results = (
            AnalysisResult(
                symbol=IndexSymbol.SP500,
                current_price=Decimal("5850.00"),
                ath_value=Decimal("6000.00"),
                ath_date=date(2025, 1, 10),
                gap_percent=Decimal("-2.50"),
                drop_tier=0,
                recommendation=Recommendation.HOLD,
                is_new_ath=False,
            ),
        )
        report = Report(
            generated_at=datetime(2025, 1, 15, 18, 0, 0, tzinfo=timezone.utc),
            market_date=date(2025, 1, 15),
            results=results,
        )
        assert report.has_buy_signals is False

    def test_to_text_contains_required_info(self):
        """Test text report contains required information."""
        results = (
            AnalysisResult(
                symbol=IndexSymbol.SP500,
                current_price=Decimal("5700.00"),
                ath_value=Decimal("6000.00"),
                ath_date=date(2025, 1, 10),
                gap_percent=Decimal("-5.00"),
                drop_tier=5,
                recommendation=Recommendation.BUY,
                is_new_ath=False,
            ),
        )
        report = Report(
            generated_at=datetime(2025, 1, 15, 18, 0, 0, tzinfo=timezone.utc),
            market_date=date(2025, 1, 15),
            results=results,
        )
        text = report.to_text()

        assert "S&P 500" in text
        assert "6,000.00" in text
        assert "5,700.00" in text
        assert "-5.00%" in text
        assert "BUY SIGNAL" in text
        assert "2025-01-15" in text

    def test_to_html_is_valid(self):
        """Test HTML report is valid HTML."""
        results = (
            AnalysisResult(
                symbol=IndexSymbol.SP500,
                current_price=Decimal("5700.00"),
                ath_value=Decimal("6000.00"),
                ath_date=date(2025, 1, 10),
                gap_percent=Decimal("-5.00"),
                drop_tier=5,
                recommendation=Recommendation.BUY,
                is_new_ath=False,
            ),
        )
        report = Report(
            generated_at=datetime(2025, 1, 15, 18, 0, 0, tzinfo=timezone.utc),
            market_date=date(2025, 1, 15),
            results=results,
        )
        html = report.to_html()

        assert "<!DOCTYPE html>" in html
        assert "<html>" in html
        assert "</html>" in html
        assert "S&amp;P 500" in html or "S&P 500" in html
