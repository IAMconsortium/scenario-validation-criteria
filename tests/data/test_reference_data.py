"""Tests for reference data CSV files."""

import yaml
from nomenclature import countries

from utils import (
    load_csv_rows,
    parse_ref_data_col,
    extract_citations,
    read_ref_data_header,
    parse_bib_keys,
    EXPECTED_REF_DATA_COLS,
)

_VALID_REGIONS = {"World"} | {c.alpha_3 for c in countries}


# ---------------------------------------------------------------------------
# Every reference dataset must be used somewhere in thresholds
# ---------------------------------------------------------------------------


def test_reference_datasets_are_used(reference_datasets, criteria_dirs):
    # Collect dataset names appearing in any threshold reference_data column.
    used: set[str] = set()
    for crit_dir in criteria_dirs.values():
        for row in load_csv_rows(crit_dir / "thresholds.csv"):
            ref_col = row.get("reference_data", "").strip()
            if not ref_col:
                continue
            try:
                _, datasets = parse_ref_data_col(ref_col)
                used.update(datasets)
            except ValueError:
                pass

    unused = set(reference_datasets) - used
    assert not unused, (
        f"reference datasets never referenced in any "
        f"thresholds file: {sorted(unused)}"
    )


# ---------------------------------------------------------------------------
# Header (YAML comment block)
# ---------------------------------------------------------------------------


def test_reference_data_header_has_required_keys(reference_datasets):
    errors = []
    for name, path in reference_datasets.items():
        header = read_ref_data_header(path)
        for key in ("source", "description"):
            if key not in header:
                errors.append(f"{name}.csv: missing '{key}' in header")
    assert not errors, "\n".join(errors)


# ---------------------------------------------------------------------------
# CSV columns
# ---------------------------------------------------------------------------


def test_reference_data_column_names_and_order(reference_datasets):
    errors = []
    for name, path in reference_datasets.items():
        rows = load_csv_rows(path)
        if not rows:
            errors.append(f"{name}.csv: file has no data rows")
            continue
        actual = list(rows[0].keys())
        if actual != EXPECTED_REF_DATA_COLS:
            errors.append(
                f"{name}.csv: columns are {actual}, "
                f"expected {EXPECTED_REF_DATA_COLS}"
            )
    assert not errors, "\n".join(errors)


# ---------------------------------------------------------------------------
# Region values
# ---------------------------------------------------------------------------


def test_reference_data_regions(reference_datasets):
    errors = []
    for name, path in reference_datasets.items():
        for i, row in enumerate(load_csv_rows(path), 1):
            region = row.get("region", "").strip()
            if region not in _VALID_REGIONS:
                errors.append(
                    f"{name}.csv row {i}: invalid region '{region}' "
                    f"(must be 'World', ISO 3166-1 alpha-3, or 'KOS')"
                )
    assert not errors, "\n".join(errors)


# ---------------------------------------------------------------------------
# Year values — integers divisible by 5
# ---------------------------------------------------------------------------


def test_reference_data_years(reference_datasets):
    errors = []
    for name, path in reference_datasets.items():
        for i, row in enumerate(load_csv_rows(path), 1):
            yr_str = row.get("year", "").strip()
            try:
                yr = int(yr_str)
            except ValueError:
                errors.append(
                    f"{name}.csv row {i}: year '{yr_str}' is not an integer"
                )
                continue
            if yr % 5 != 0:
                errors.append(
                    f"{name}.csv row {i}: year {yr} is not divisible by 5"
                )
    assert not errors, "\n".join(errors)


# ---------------------------------------------------------------------------
# Source and citation keys against the BibTeX file
# ---------------------------------------------------------------------------


def test_reference_data_source_is_valid_bib_key(reference_datasets, bib_keys):
    errors = []
    for name, path in reference_datasets.items():
        header = read_ref_data_header(path)
        source = header.get("source", "").strip()
        if source and source not in bib_keys:
            errors.append(
                f"{name}.csv: header 'source: {source}' "
                f"not found in sources.bib"
            )
    assert not errors, "\n".join(errors)


def test_reference_data_description_citations_are_valid(
    reference_datasets, bib_keys
):
    errors = []
    for name, path in reference_datasets.items():
        header = read_ref_data_header(path)
        description = str(header.get("description", ""))
        for key in extract_citations(description):
            if key not in bib_keys:
                errors.append(
                    f"{name}.csv: citation '{{{{cite:{key}}}}}' in header "
                    f"description not found in sources.bib"
                )
    assert not errors, "\n".join(errors)
