"""Tests for the BibTeX sources file."""

import yaml

from scenario_validation_criteria import _expand_metadata_templates
from utils import extract_citations, read_ref_data_header, load_csv_rows


def _load_metadata(crit_dir):
    raw = yaml.safe_load((crit_dir / "descriptions.yaml").read_text())
    return _expand_metadata_templates(raw)


# ---------------------------------------------------------------------------
# Citations in metadata YAML must resolve to valid BibTeX keys
# ---------------------------------------------------------------------------


def test_metadata_citations_are_valid(criteria_dirs, bib_keys):
    errors = []
    for name, path in criteria_dirs.items():
        metadata = _load_metadata(path)
        for criterion, spec in metadata.items():
            for field, text in spec.items():
                for key in extract_citations(str(text)):
                    if key not in bib_keys:
                        errors.append(
                            f"{name}/{criterion}/{field}: "
                            f"citation key '{key}' not in sources.bib"
                        )
    assert not errors, "\n".join(errors)


# ---------------------------------------------------------------------------
# Every BibTeX entry must be cited at least once
# ---------------------------------------------------------------------------


def test_all_bib_entries_are_cited(
    criteria_dirs, reference_datasets, bib_keys
):
    all_cited: set[str] = set()

    # Citations from metadata YAML ({{cite:KEY}} / {{citep:KEY}})
    for path in criteria_dirs.values():
        metadata = _load_metadata(path)
        for spec in metadata.values():
            for text in spec.values():
                all_cited |= extract_citations(str(text))

    # 'source:' values from reference data headers count as citations
    for path in reference_datasets.values():
        header = read_ref_data_header(path)
        if source := header.get("source", "").strip():
            all_cited.add(source)
        # Also handle any explicit {{cite:...}} in descriptions
        all_cited |= extract_citations(str(header.get("description", "")))

    uncited = bib_keys - all_cited
    assert not uncited, f"sources.bib: entries never cited: {sorted(uncited)}"
