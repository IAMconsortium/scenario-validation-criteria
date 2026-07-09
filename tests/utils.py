"""Shared utility functions for the test suite."""

import csv
import itertools
import re
import yaml
from pathlib import Path


CITATION_RE = re.compile(r"\{\{cite[p]?:([^}]+)\}\}")
BIB_KEY_RE = re.compile(r"@(?!comment)\w+\s*\{\s*([^,\s]+)", re.IGNORECASE)
# Matches: optional_operator(dataset, dataset, ...) or bare dataset names
REF_DATA_COL_RE = re.compile(r"^(?P<op>[a-z][a-z-]*)?\(?(?P<data>[^)]+)\)?$")
# Matches a cumulative year range: cumulative[YYYY-YYYY]
CUMULATIVE_YEAR_RE = re.compile(r"^cumulative\[(?P<start>\d+)-(?P<end>\d+)\]$")

VALID_OPERATORS = {"range", "min", "max", "min-max"}
EXPECTED_THRESHOLD_COLS = {
    "criterion",
    "variable",
    "region",
    "year",
    "reference_data",
    "unit",
    "validation_outcome",
    "lower",
    "upper",
}
EXPECTED_REF_DATA_COLS = ["variable", "year", "region", "unit", "value"]
METADATA_REQUIRED_KEYS = {"justification_criterion", "justification_threshold"}


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
        return list(
            csv.DictReader(row for row in f if not row.startswith("#"))
        )


def parse_bib_keys(bib_path: Path) -> set[str]:
    """Extract all non-@comment entry keys from a .bib file."""
    return {m.group(1) for m in BIB_KEY_RE.finditer(bib_path.read_text())}


def extract_citations(text: str) -> set[str]:
    """Return all citation keys from {{cite:KEY}} or {{citep:KEY}}."""
    return set(CITATION_RE.findall(text))


def parse_ref_data_col(col: str) -> tuple[str, list[str]]:
    """Parse a reference_data column value.

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


def parse_year_col(col: str) -> list:
    """Parse a threshold ``year`` column value into its entries.

    The value is a comma-separated list of entries, where each entry is
    either a plain integer year (e.g. ``2030``) or a cumulative range of the
    form ``cumulative[YYYY-YYYY]``. A cumulative entry denotes that the
    threshold applies to the cumulative sum over the inclusive year range,
    rather than to each individual year.

    Returns a list with one item per non-empty comma-separated field, in
    order: a plain year is returned as an ``int``, a cumulative range as a
    ``(start, end)`` tuple of ints. An empty value returns an empty list.

    Raises
    ------
    ValueError
        If an entry is neither a plain integer nor a well-formed
        ``cumulative[YYYY-YYYY]`` range, if a cumulative range is inverted
        (start > end), or if cumulative and plain-year entries are mixed
        within the same value. Mixing is forbidden because the two carry
        incompatible dimensions (``[X]`` vs. ``[X]/[time]``).

    """
    entries: list = []
    kinds: set[str] = set()
    for raw in col.split(","):
        field = raw.strip()
        if not field:
            continue
        match = CUMULATIVE_YEAR_RE.match(field)
        if match:
            start, end = int(match["start"]), int(match["end"])
            if start > end:
                raise ValueError(
                    f"inverted cumulative range '{field}' (start > end)"
                )
            entries.append((start, end))
            kinds.add("cumulative")
        else:
            try:
                entries.append(int(field))
            except ValueError:
                raise ValueError(
                    f"year '{field}' is neither an integer nor a "
                    f"cumulative[YYYY-YYYY] range"
                )
            kinds.add("plain")
    if len(kinds) > 1:
        raise ValueError(
            "cumulative and plain-year entries cannot be mixed in one row"
        )
    return entries


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


def expand_metadata_templates(metadata: dict) -> dict:
    """Expand template metadata entries into individual entries.

    Standalone copy of ``scenario_validation_criteria._expand_metadata_``
    ``templates`` so the raw-data tests can validate ``descriptions.yaml``
    without importing the Python package. The package's own expansion logic
    is exercised separately by the package-functionality tests.

    Template entries (those with a 'replacements' field) are expanded into
    individual entries, applying all substitutions to both the criterion key
    and the text fields.
    """
    result = {}
    for key, spec in metadata.items():
        if "replacements" not in spec:
            result[key] = spec
            continue
        replacements = spec["replacements"]
        base_spec = {k: v for k, v in spec.items() if k != "replacements"}
        var_names = list(replacements.keys())
        option_lists = [list(replacements[v].items()) for v in var_names]
        for combo in itertools.product(*option_lists):
            subs: dict[str, str] = {}
            for var_name, (option_key, text_subs) in zip(var_names, combo):
                subs[var_name] = option_key
                subs.update(text_subs or {})
            new_key = key
            for sub_var, sub_val in subs.items():
                if sub_val is None:
                    # Tilde (~) entry: strip the placeholder and its
                    # adjacent pipe.
                    new_key = (
                        new_key.replace(f"|{{{sub_var}}}", "")
                        .replace(f"{{{sub_var}}}|", "")
                        .replace(f"{{{sub_var}}}", "")
                    )
                else:
                    new_key = new_key.replace(f"{{{sub_var}}}", sub_val)
            new_spec = {}
            for field_k, field_v in base_spec.items():
                if isinstance(field_v, str):
                    for sub_var, sub_val in subs.items():
                        if sub_val is not None:
                            field_v = field_v.replace(
                                f"{{{sub_var}}}", sub_val
                            )
                new_spec[field_k] = field_v
            result[new_key] = new_spec
    return result
