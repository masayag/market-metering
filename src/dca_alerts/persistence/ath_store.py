"""ATH persistence to local JSON file."""

import json
import logging
import tempfile
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Optional

from ..models import ATHRecord, IndexSymbol

logger = logging.getLogger(__name__)


class ATHStoreError(Exception):
    """Raised when ATH storage operations fail."""


class ATHStore:
    """Persists ATH records to local JSON file."""

    def __init__(self, storage_path: Path):
        """
        Initialize the ATH store.

        Args:
            storage_path: Path to JSON file for ATH storage
        """
        self._path = storage_path

    def get(self, symbol: IndexSymbol) -> Optional[ATHRecord]:
        """
        Retrieve ATH record for symbol.

        Args:
            symbol: Index symbol to look up

        Returns:
            ATHRecord if exists, None otherwise
        """
        records = self.get_all()
        return records.get(symbol)

    def get_all(self) -> dict[IndexSymbol, ATHRecord]:
        """
        Retrieve all ATH records.

        Returns:
            Dictionary mapping symbols to ATH records
        """
        data = self._load()
        records = {}

        for symbol_value, record_data in data.items():
            for idx in IndexSymbol:
                if idx.value == symbol_value:
                    try:
                        records[idx] = ATHRecord(
                            symbol=idx,
                            ath_value=Decimal(record_data["ath_value"]),
                            ath_date=date.fromisoformat(record_data["ath_date"]),
                            updated_at=datetime.fromisoformat(record_data["updated_at"]),
                        )
                    except (KeyError, ValueError) as e:
                        logger.warning(
                            "Invalid ATH record for %s, skipping: %s", symbol_value, e
                        )
                    break

        return records

    def update(self, record: ATHRecord) -> None:
        """
        Upsert ATH record.

        Uses atomic write with temp file + rename for crash safety.

        Args:
            record: ATH record to save
        """
        data = self._load()
        data[record.symbol.value] = {
            "ath_value": str(record.ath_value),
            "ath_date": record.ath_date.isoformat(),
            "updated_at": record.updated_at.isoformat(),
        }
        self._save(data)
        logger.info(
            "Updated ATH for %s: %.2f on %s",
            record.symbol.display_name,
            record.ath_value,
            record.ath_date,
        )

    def _load(self) -> dict:
        """
        Load JSON file.

        Returns:
            Dictionary from JSON, or empty dict if file doesn't exist
        """
        if not self._path.exists():
            logger.debug("ATH file not found at %s, starting fresh", self._path)
            return {}

        try:
            with open(self._path) as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except json.JSONDecodeError as e:
            logger.warning("Invalid JSON in ATH file %s: %s", self._path, e)
            return {}
        except OSError as e:
            logger.error("Failed to read ATH file %s: %s", self._path, e)
            return {}

    def _save(self, data: dict) -> None:
        """
        Atomic save to JSON file.

        Writes to temp file then renames for crash safety.

        Args:
            data: Dictionary to save as JSON
        """
        self._path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                dir=self._path.parent,
                prefix=".ath_",
                suffix=".tmp",
                delete=False,
            ) as f:
                json.dump(data, f, indent=2)
                temp_path = Path(f.name)

            temp_path.replace(self._path)
        except OSError as e:
            logger.error("Failed to save ATH file: %s", e)
            if temp_path.exists():
                temp_path.unlink()
            raise ATHStoreError(f"Failed to save ATH file: {e}") from e
