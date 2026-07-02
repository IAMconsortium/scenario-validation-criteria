"""Tests for data directory structure."""


REQUIRED_FILES = {"criteria-types.yaml", "sources.bib"}
REQUIRED_DIRS = {"criteria", "reference-data"}


def test_required_files_present(criteria_types_dict, bib_keys):
    from pathlib import Path
    EXTDATA = Path(__file__).parent.parent / "inst" / "extdata"
    present = {p.name for p in EXTDATA.iterdir()}
    missing = REQUIRED_FILES - present
    assert not missing, (
        f"missing required files: {sorted(missing)}"
    )


def test_required_directories_present():
    from pathlib import Path
    EXTDATA = Path(__file__).parent.parent / "inst" / "extdata"
    present = {p.name for p in EXTDATA.iterdir() if p.is_dir()}
    missing = REQUIRED_DIRS - present
    assert not missing, (
        f"missing required directories: {sorted(missing)}"
    )


def test_criteria_dirs_match_types(criteria_types_dict, criteria_dirs):
    defined = set(criteria_types_dict)
    present = set(criteria_dirs)
    errors = []
    if extra := present - defined:
        errors.append(f"directories not listed in criteria-types.yaml: {sorted(extra)}")
    if missing := defined - present:
        errors.append(f"types in criteria-types.yaml with no directory: {sorted(missing)}")
    assert not errors, "; ".join(errors)


def test_each_criteria_type_has_required_files(criteria_dirs):
    errors = []
    for name, path in criteria_dirs.items():
        for fname in ("descriptions.yaml", "thresholds.csv"):
            if not (path / fname).exists():
                errors.append(f"{name}/{fname}")
    assert not errors, (
        f"missing files:\n" + "\n".join(f"  {e}" for e in errors)
    )
