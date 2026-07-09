"""Tests for criteria thresholds and metadata."""

import yaml
from nomenclature import countries

from utils import (
    expand_metadata_templates,
    load_csv_rows,
    parse_ref_data_col,
    parse_year_col,
    extract_citations,
    EXPECTED_THRESHOLD_COLS,
    METADATA_REQUIRED_KEYS,
    VALID_OPERATORS,
    format_type_prefix,
    is_float,
)

_COUNTRY_CODES = {c.alpha_3 for c in countries}
VALID_THRESHOLD_REGIONS = {"World", "All Countries"} | _COUNTRY_CODES


def _load_metadata(crit_dir):
    raw = yaml.safe_load((crit_dir / "descriptions.yaml").read_text())
    return expand_metadata_templates(raw)


# ---------------------------------------------------------------------------
# Column structure
# ---------------------------------------------------------------------------


def test_threshold_column_names(criteria_dirs):
    errors = []
    for name, path in criteria_dirs.items():
        rows = load_csv_rows(path / "thresholds.csv")
        if not rows:
            errors.append(f"{name}/thresholds.csv: file is empty")
            continue
        actual = set(rows[0].keys())
        extra = actual - EXPECTED_THRESHOLD_COLS
        missing = EXPECTED_THRESHOLD_COLS - actual
        if extra or missing:
            msg = f"{name}/thresholds.csv: column mismatch"
            if extra:
                msg += f" — unexpected: {sorted(extra)}"
            if missing:
                msg += f" — missing: {sorted(missing)}"
            errors.append(msg)
    assert not errors, "\n".join(errors)


# ---------------------------------------------------------------------------
# Criterion-name consistency between thresholds and metadata
# ---------------------------------------------------------------------------


def test_every_threshold_criterion_has_metadata(criteria_dirs):
    errors = []
    for name, path in criteria_dirs.items():
        threshold_ids = {
            row["criterion"] for row in load_csv_rows(path / "thresholds.csv")
        }
        metadata_ids = set(_load_metadata(path))
        missing = threshold_ids - metadata_ids
        if missing:
            errors.append(
                f"{name}: criteria in thresholds with no "
                f"metadata entry: {sorted(missing)}"
            )
    assert not errors, "\n".join(errors)


def test_every_metadata_criterion_has_threshold(criteria_dirs):
    errors = []
    for name, path in criteria_dirs.items():
        threshold_ids = {
            row["criterion"] for row in load_csv_rows(path / "thresholds.csv")
        }
        metadata_ids = set(_load_metadata(path))
        missing = metadata_ids - threshold_ids
        if missing:
            errors.append(
                f"{name}: criteria in metadata with no "
                f"threshold row: {sorted(missing)}"
            )
    assert not errors, "\n".join(errors)


# ---------------------------------------------------------------------------
# Metadata content
# ---------------------------------------------------------------------------


def test_metadata_required_keys(criteria_dirs):
    errors = []
    for name, path in criteria_dirs.items():
        for criterion, spec in _load_metadata(path).items():
            missing = METADATA_REQUIRED_KEYS - set(spec)
            if missing:
                errors.append(
                    f"{name}/{criterion}: missing metadata keys: "
                    f"{sorted(missing)}"
                )
    assert not errors, "\n".join(errors)


# ---------------------------------------------------------------------------
# Threshold row values
# ---------------------------------------------------------------------------


def test_threshold_required_string_columns_non_empty(criteria_dirs):
    errors = []
    for name, path in criteria_dirs.items():
        for i, row in enumerate(load_csv_rows(path / "thresholds.csv"), 1):
            for col in ("criterion", "variable", "unit"):
                if not row.get(col, "").strip():
                    errors.append(
                        f"{name}/thresholds.csv row {i}: '{col}' is empty"
                    )
    assert not errors, "\n".join(errors)


def test_threshold_region_values(criteria_dirs):
    errors = []
    for name, path in criteria_dirs.items():
        for i, row in enumerate(load_csv_rows(path / "thresholds.csv"), 1):
            for region in row.get("region", "").split(","):
                region = region.strip()
                if region and region not in VALID_THRESHOLD_REGIONS:
                    errors.append(
                        f"{name}/thresholds.csv row {i}: "
                        f"invalid region '{region}'"
                    )
    assert not errors, "\n".join(errors)


def test_threshold_validation_outcome(criteria_dirs, criteria_types_dict):
    errors = []
    for name, path in criteria_dirs.items():
        # Allowed outcomes for this criteria type are declared in
        # criteria-types.yaml. "ok" is the implicit default and never appears
        # in the threshold files, so it is excluded from the accepted values.
        type_label = format_type_prefix(name)
        outcomes = criteria_types_dict[type_label]["validation_outcomes"]
        valid = set(outcomes) - {"ok"}
        for i, row in enumerate(load_csv_rows(path / "thresholds.csv"), 1):
            outcome = row.get("validation_outcome", "").strip()
            if outcome not in valid:
                errors.append(
                    f"{name}/thresholds.csv row {i}: "
                    f"invalid validation_outcome '{outcome}' "
                    f"(expected one of {sorted(valid)})"
                )
    assert not errors, "\n".join(errors)


def test_threshold_year_values(criteria_dirs):
    """Year entries must be integers or cumulative[YYYY-YYYY] ranges.

    Entries are comma-separated; cumulative and plain-year entries may not
    be mixed within a single row (see ``parse_year_col``).
    """
    errors = []
    for name, path in criteria_dirs.items():
        for i, row in enumerate(load_csv_rows(path / "thresholds.csv"), 1):
            try:
                parse_year_col(row.get("year", ""))
            except ValueError as exc:
                errors.append(f"{name}/thresholds.csv row {i}: {exc}")
    assert not errors, "\n".join(errors)


def test_threshold_lower_or_upper_set(criteria_dirs):
    errors = []
    for name, path in criteria_dirs.items():
        for i, row in enumerate(load_csv_rows(path / "thresholds.csv"), 1):
            lower = row.get("lower", "").strip()
            upper = row.get("upper", "").strip()
            if not (is_float(lower) or is_float(upper)):
                errors.append(
                    f"{name}/thresholds.csv row {i}: "
                    f"neither 'lower' ({lower!r}) nor 'upper' ({upper!r}) "
                    f"is a valid number"
                )
    assert not errors, "\n".join(errors)


# ---------------------------------------------------------------------------
# reference_data column
# ---------------------------------------------------------------------------


def test_threshold_reference_data_format(criteria_dirs):
    errors = []
    for name, path in criteria_dirs.items():
        for i, row in enumerate(load_csv_rows(path / "thresholds.csv"), 1):
            ref_col = row.get("reference_data", "").strip()
            if not ref_col:
                continue
            try:
                op, _ = parse_ref_data_col(ref_col)
            except ValueError as exc:
                errors.append(f"{name}/thresholds.csv row {i}: {exc}")
                continue
            if op not in VALID_OPERATORS:
                errors.append(
                    f"{name}/thresholds.csv row {i}: "
                    f"unknown operator '{op}' in '{ref_col}' "
                    f"(valid: {sorted(VALID_OPERATORS)})"
                )
    assert not errors, "\n".join(errors)


def test_threshold_reference_datasets_exist(criteria_dirs, reference_datasets):
    errors = []
    for name, path in criteria_dirs.items():
        for i, row in enumerate(load_csv_rows(path / "thresholds.csv"), 1):
            ref_col = row.get("reference_data", "").strip()
            if not ref_col:
                continue
            try:
                _, datasets = parse_ref_data_col(ref_col)
            except ValueError:
                continue  # already caught by format test
            for ds in datasets:
                if ds not in reference_datasets:
                    errors.append(
                        f"{name}/thresholds.csv row {i}: "
                        f"unknown reference dataset '{ds}'"
                    )
    assert not errors, "\n".join(errors)


def test_threshold_variables_present_in_reference_data(
    criteria_dirs, reference_datasets
):
    # Cache variable sets per dataset to avoid re-reading.
    ref_vars: dict[str, set[str]] = {}
    for ds_name, ds_path in reference_datasets.items():
        ref_vars[ds_name] = {row["variable"] for row in load_csv_rows(ds_path)}

    errors = []
    for name, path in criteria_dirs.items():
        for i, row in enumerate(load_csv_rows(path / "thresholds.csv"), 1):
            ref_col = row.get("reference_data", "").strip()
            if not ref_col:
                continue
            try:
                _, datasets = parse_ref_data_col(ref_col)
            except ValueError:
                continue
            threshold_vars = {
                v.strip() for v in row.get("variable", "").split(",")
            }
            for ds in datasets:
                if ds not in ref_vars:
                    continue  # caught by existence test
                if not threshold_vars & ref_vars[ds]:
                    errors.append(
                        f"{name}/thresholds.csv row {i}: "
                        f"none of {sorted(threshold_vars)} found in "
                        f"'{ds}' variable column"
                    )
    assert not errors, "\n".join(errors)
