"""Shared pytest fixtures."""

import yaml
import pytest
from pathlib import Path

from utils import load_csv_rows, parse_bib_keys


EXTDATA = Path(__file__).parent.parent / "inst" / "extdata"


@pytest.fixture
def bib_keys():
    """Set of all non-@comment entry keys in sources.bib."""
    return parse_bib_keys(EXTDATA / "sources.bib")


@pytest.fixture
def criteria_types_dict():
    """Return the parsed criteria-types.yaml."""
    return yaml.safe_load((EXTDATA / "criteria-types.yaml").read_text())


@pytest.fixture
def criteria_dirs():
    """Return a mapping of criteria type name to directory path."""
    root = EXTDATA / "criteria"
    return {d.name: d for d in sorted(root.iterdir()) if d.is_dir()}


@pytest.fixture
def reference_datasets():
    """Return a mapping of dataset stem to CSV path for reference data."""
    ref_dir = EXTDATA / "reference-data"
    return {p.stem: p for p in sorted(ref_dir.glob("*.csv"))}


@pytest.fixture
def all_threshold_rows(criteria_dirs):
    """Return all threshold rows across criteria types, with '_type' set."""
    rows = []
    for crit_type, crit_dir in criteria_dirs.items():
        for row in load_csv_rows(crit_dir / "thresholds.csv"):
            row["_type"] = crit_type
            rows.append(row)
    return rows
