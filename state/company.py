"""Data loader and company snapshot provider for NimbusDesk synthetic data."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from state.schemas import CompanySnapshot

DEFAULT_COMPANY_PATH = Path(__file__).resolve().parent.parent / "data" / "synthetic_company.json"
DEFAULT_SEEDED_DECISIONS_PATH = Path(__file__).resolve().parent.parent / "data" / "seeded_decisions.json"

_CACHED_SNAPSHOT: Optional[CompanySnapshot] = None


def load_company_snapshot(filepath: Optional[Path | str] = None, reload: bool = False) -> CompanySnapshot:
    """Load and validate the synthetic company snapshot."""
    global _CACHED_SNAPSHOT
    if _CACHED_SNAPSHOT is not None and not reload and filepath is None:
        return _CACHED_SNAPSHOT.model_copy(deep=True)

    path = Path(filepath) if filepath else DEFAULT_COMPANY_PATH
    if not path.exists():
        raise FileNotFoundError(f"Synthetic company data file not found at: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    snapshot = CompanySnapshot.model_validate(data)
    if filepath is None:
        _CACHED_SNAPSHOT = snapshot
    return snapshot.model_copy(deep=True)


def load_seeded_decisions(filepath: Optional[Path | str] = None) -> List[Dict[str, Any]]:
    """Load seeded past decisions for calibration."""
    path = Path(filepath) if filepath else DEFAULT_SEEDED_DECISIONS_PATH
    if not path.exists():
        raise FileNotFoundError(f"Seeded decisions file not found at: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
