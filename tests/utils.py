"""Shared utility functions for the test suite."""
import csv
import re
import yaml
from pathlib import Path


CITATION_RE = re.compile(r"\{\{cite[p]?:([^}]+)\}\}")
BIB_KEY_RE = re.compile(r"@(?!comment)\w+\s*\{\s*([^,\s]+)", re.IGNORECASE)
# Matches: optional_operator(dataset, dataset, ...) or bare dataset names
REF_DATA_COL_RE = re.compile(r"^(?P<op>[a-z][a-z-]*)?\(?(?P<data>[^)]+)\)?$")

VALID_OPERATORS = {"range", "min", "max", "min-max"}
EXPECTED_THRESHOLD_COLS = {
    "criterion", "variable", "region", "year",
    "reference_data", "unit", "level_of_concern", "lower", "upper",
}
EXPECTED_REF_DATA_COLS = ["variable", "year", "region", "unit", "value"]
METADATA_REQUIRED_KEYS = {"justification_criterion", "justification_threshold"}
VALID_LEVEL_OF_CONCERN = {"medium", "strong"}


def format_type_prefix(prefix: str) -> str:
    """Convert a criteria-type directory name to its formatted label.

    Mirrors ``scenario_validation_criteria._format_prefix``: dashes become
    spaces and every word is capitalised (e.g. ``historical-vetting`` ->
    ``Historical Vetting``), matching the keys used in criteria-types.yaml.
    """
    return " ".join(word[:1].upper() + word[1:] for word in prefix.split("-"))


def load_csv_rows(path: Path) -> list[dict]:
    """Read a CSV, skipping lines starting with '#'."""
    with path.open() as f:
        return list(csv.DictReader(row for row in f if not row.startswith("#")))


def parse_bib_keys(bib_path: Path) -> set[str]:
    """Extract all non-@comment entry keys from a .bib file."""
    return {m.group(1) for m in BIB_KEY_RE.finditer(bib_path.read_text())}


def extract_citations(text: str) -> set[str]:
    """Return all citation keys referenced via {{cite:KEY}} or {{citep:KEY}}."""
    return set(CITATION_RE.findall(text))


def parse_ref_data_col(col: str) -> tuple[str, list[str]]:
    """
    Parse a reference_data column value.

    Returns (operator, [dataset_names]).
    Empty string returns ("range", []).
    Raises ValueError if the format is unrecognisable.
    """
    col = col.strip()
    if not col:
        return "range", []
    m = REF_DATA_COL_RE.match(col)
    if not m:
        raise ValueError(f"Cannot parse reference_data value: {col!r}")
    op = m.group("op") or "range"
    datasets = [d.strip() for d in m.group("data").split(",") if d.strip()]
    return op, datasets


def read_ref_data_header(path: Path) -> dict:
    """Parse the YAML comment header of a reference data CSV."""
    lines = path.read_text().splitlines()
    comment_lines = [line[1:] for line in lines if line.startswith("#")]
    return yaml.safe_load("\n".join(comment_lines)) or {}


def is_float(s: str) -> bool:
    try:
        float(s)
        return True
    except (ValueError, TypeError):
        return False
