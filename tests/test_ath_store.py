"""Tests for ATH store."""

import json
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from dca_alerts.models import ATHRecord, IndexSymbol
from dca_alerts.persistence.ath_store import ATHStore


class TestATHStore:
    """Tests for ATHStore class."""

    def test_get_nonexistent_file(self, ath_store_path: Path):
        """Test get returns None when file doesn't exist."""
        store = ATHStore(ath_store_path)
        result = store.get(IndexSymbol.SP500)
        assert result is None

    def test_get_all_empty(self, ath_store_path: Path):
        """Test get_all returns empty dict when file doesn't exist."""
        store = ATHStore(ath_store_path)
        result = store.get_all()
        assert result == {}

    def test_update_creates_file(self, ath_store_path: Path):
        """Test update creates file if it doesn't exist."""
        store = ATHStore(ath_store_path)
        record = ATHRecord(
            symbol=IndexSymbol.SP500,
            ath_value=Decimal("6000.00"),
            ath_date=date(2025, 1, 10),
            updated_at=datetime(2025, 1, 10, 18, 0, 0, tzinfo=timezone.utc),
        )

        store.update(record)

        assert ath_store_path.exists()
        with open(ath_store_path) as f:
            data = json.load(f)
        assert "^GSPC" in data

    def test_update_and_get(self, ath_store_path: Path):
        """Test round-trip update and get."""
        store = ATHStore(ath_store_path)
        record = ATHRecord(
            symbol=IndexSymbol.SP500,
            ath_value=Decimal("6000.00"),
            ath_date=date(2025, 1, 10),
            updated_at=datetime(2025, 1, 10, 18, 0, 0, tzinfo=timezone.utc),
        )

        store.update(record)
        retrieved = store.get(IndexSymbol.SP500)

        assert retrieved is not None
        assert retrieved.symbol == IndexSymbol.SP500
        assert retrieved.ath_value == Decimal("6000.00")
        assert retrieved.ath_date == date(2025, 1, 10)

    def test_update_multiple_symbols(self, ath_store_path: Path):
        """Test storing multiple symbols."""
        store = ATHStore(ath_store_path)

        sp500 = ATHRecord(
            symbol=IndexSymbol.SP500,
            ath_value=Decimal("6000.00"),
            ath_date=date(2025, 1, 10),
            updated_at=datetime(2025, 1, 10, 18, 0, 0, tzinfo=timezone.utc),
        )
        nasdaq = ATHRecord(
            symbol=IndexSymbol.NASDAQ100,
            ath_value=Decimal("18500.00"),
            ath_date=date(2025, 1, 8),
            updated_at=datetime(2025, 1, 8, 18, 0, 0, tzinfo=timezone.utc),
        )

        store.update(sp500)
        store.update(nasdaq)

        all_records = store.get_all()
        assert len(all_records) == 2
        assert IndexSymbol.SP500 in all_records
        assert IndexSymbol.NASDAQ100 in all_records

    def test_update_overwrites_existing(self, ath_store_path: Path):
        """Test update overwrites existing record."""
        store = ATHStore(ath_store_path)

        original = ATHRecord(
            symbol=IndexSymbol.SP500,
            ath_value=Decimal("6000.00"),
            ath_date=date(2025, 1, 10),
            updated_at=datetime(2025, 1, 10, 18, 0, 0, tzinfo=timezone.utc),
        )
        updated = ATHRecord(
            symbol=IndexSymbol.SP500,
            ath_value=Decimal("6200.00"),
            ath_date=date(2025, 1, 15),
            updated_at=datetime(2025, 1, 15, 18, 0, 0, tzinfo=timezone.utc),
        )

        store.update(original)
        store.update(updated)

        retrieved = store.get(IndexSymbol.SP500)
        assert retrieved is not None
        assert retrieved.ath_value == Decimal("6200.00")
        assert retrieved.ath_date == date(2025, 1, 15)

    def test_handles_invalid_json(self, ath_store_path: Path):
        """Test handles corrupted JSON gracefully."""
        ath_store_path.parent.mkdir(parents=True, exist_ok=True)
        ath_store_path.write_text("not valid json {{{")

        store = ATHStore(ath_store_path)
        result = store.get_all()

        assert result == {}

    def test_handles_invalid_record(self, ath_store_path: Path):
        """Test handles invalid record data gracefully."""
        ath_store_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "^GSPC": {"missing": "fields"},
        }
        ath_store_path.write_text(json.dumps(data))

        store = ATHStore(ath_store_path)
        result = store.get_all()

        assert result == {}

    def test_creates_parent_directories(self, tmp_path: Path):
        """Test update creates parent directories if needed."""
        nested_path = tmp_path / "nested" / "dirs" / "ath.json"
        store = ATHStore(nested_path)

        record = ATHRecord(
            symbol=IndexSymbol.SP500,
            ath_value=Decimal("6000.00"),
            ath_date=date(2025, 1, 10),
            updated_at=datetime(2025, 1, 10, 18, 0, 0, tzinfo=timezone.utc),
        )

        store.update(record)

        assert nested_path.exists()
