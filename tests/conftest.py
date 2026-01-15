"""Shared test fixtures."""

from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from dca_alerts.models import AnalysisResult, ATHRecord, IndexData, IndexSymbol, Recommendation


@pytest.fixture
def sample_index_data() -> IndexData:
    """Sample market data for S&P 500."""
    return IndexData(
        symbol=IndexSymbol.SP500,
        current_price=Decimal("5700.00"),
        fetched_at=datetime(2025, 1, 15, 18, 0, 0, tzinfo=timezone.utc),
        market_date=date(2025, 1, 15),
    )


@pytest.fixture
def sample_ath_record() -> ATHRecord:
    """Sample ATH record for S&P 500."""
    return ATHRecord(
        symbol=IndexSymbol.SP500,
        ath_value=Decimal("6000.00"),
        ath_date=date(2025, 1, 10),
        updated_at=datetime(2025, 1, 10, 18, 0, 0, tzinfo=timezone.utc),
    )


@pytest.fixture
def sample_analysis_result() -> AnalysisResult:
    """Sample analysis result with buy signal."""
    return AnalysisResult(
        symbol=IndexSymbol.SP500,
        current_price=Decimal("5700.00"),
        ath_value=Decimal("6000.00"),
        ath_date=date(2025, 1, 10),
        gap_percent=Decimal("-5.00"),
        drop_tier=5,
        recommendation=Recommendation.BUY,
        is_new_ath=False,
    )


@pytest.fixture
def ath_store_path(tmp_path: Path) -> Path:
    """Temporary path for ATH storage."""
    return tmp_path / "ath_records.json"
