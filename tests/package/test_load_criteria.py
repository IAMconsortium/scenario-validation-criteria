"""Tests for the Python package API (``scenario_validation_criteria``).

Unlike the raw-data tests, these load the installed package and exercise
its public ``load_criteria`` entry point and internal helpers against the
data bundled into the package.
"""

import pandas
import pytest

import scenario_validation_criteria as svc
from scenario_validation_criteria import (
    COMPONENTS,
    load_criteria,
    _deformat_prefix,
    _expand_metadata_templates,
    _format_prefix,
)


# ---------------------------------------------------------------------------
# Prefix formatting helpers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "directory, label",
    [
        ("historical-vetting", "Historical Vetting"),
        ("feasibility-concern", "Feasibility Concern"),
        ("sustainability-concern", "Sustainability Concern"),
    ],
)
def test_format_prefix(directory, label):
    assert _format_prefix(directory) == label


@pytest.mark.parametrize(
    "label", ["Historical Vetting", "Feasibility Concern"]
)
def test_deformat_prefix_inverts_format(label):
    assert _format_prefix(_deformat_prefix(label)) == label


def test_deformat_prefix_idempotent_on_directory_form():
    assert _deformat_prefix("historical-vetting") == "historical-vetting"


# ---------------------------------------------------------------------------
# Metadata template expansion
# ---------------------------------------------------------------------------


def test_expand_metadata_templates_without_replacements_is_identity():
    metadata = {"Criterion A": {"justification_criterion": "text"}}
    assert _expand_metadata_templates(metadata) == metadata


def test_expand_metadata_templates_substitutes_key_and_fields():
    metadata = {
        "Emissions|{Species}": {
            "justification_criterion": "concern about {gas}",
            "replacements": {
                "Species": {
                    "CO2": {"gas": "carbon dioxide"},
                    "CH4": {"gas": "methane"},
                }
            },
        }
    }
    result = _expand_metadata_templates(metadata)
    assert set(result) == {"Emissions|CO2", "Emissions|CH4"}
    assert result["Emissions|CO2"]["justification_criterion"] == (
        "concern about carbon dioxide"
    )
    assert "replacements" not in result["Emissions|CO2"]


def test_expand_metadata_templates_tilde_strips_placeholder():
    # A YAML "~" option key parses to None, which strips the placeholder
    # (and its adjacent pipe) from the criterion key.
    metadata = {
        "Emissions|{Species}": {
            "justification_criterion": "text",
            "replacements": {"Species": {None: None}},
        }
    }
    result = _expand_metadata_templates(metadata)
    assert set(result) == {"Emissions"}


# ---------------------------------------------------------------------------
# load_criteria: argument validation
# ---------------------------------------------------------------------------


def test_load_criteria_requires_component_or_load_all():
    with pytest.raises(Exception):
        load_criteria()


def test_load_criteria_rejects_components_and_load_all_together():
    with pytest.raises(Exception):
        load_criteria(components="criteria-types", load_all=True)


def test_load_criteria_unknown_component_raises():
    with pytest.raises(Exception):
        load_criteria(components="not-a-component")


# ---------------------------------------------------------------------------
# load_criteria: individual components
# ---------------------------------------------------------------------------


def test_load_criteria_types_returns_dict():
    types = load_criteria("criteria-types")
    assert isinstance(types, dict)
    assert "Historical Vetting" in types


def test_load_criteria_thresholds_is_dataframe_with_expected_columns():
    df = load_criteria("criteria-thresholds")
    assert isinstance(df, pandas.DataFrame)
    assert not df.empty
    assert set(svc.THRESHOLD_COLS_DTYPES).issubset(df.columns)
    # Every criterion is prefixed with its formatted criteria type.
    assert df["criterion"].str.contains(r"\|").all()


def test_load_criteria_descriptions_expands_and_prefixes_keys():
    descriptions = load_criteria("criteria-descriptions")
    assert isinstance(descriptions, dict)
    assert descriptions
    # Keys are prefixed "<Type>|<criterion>" and templates are expanded.
    assert all("|" in key for key in descriptions)
    assert all("replacements" not in spec for spec in descriptions.values())


def test_load_criteria_variables_is_sorted_unique_list():
    variables = load_criteria("criteria-variables")
    assert isinstance(variables, list)
    assert all(isinstance(v, str) for v in variables)
    assert variables == sorted(variables)
    assert len(variables) == len(set(variables))


def test_load_reference_data_is_dataframe_with_reference_column():
    df = load_criteria("reference-data")
    assert isinstance(df, pandas.DataFrame)
    assert not df.empty
    assert "reference_data" in df.columns


def test_load_reference_metadata_returns_headers():
    metadata = load_criteria("reference-metadata")
    assert isinstance(metadata, dict)
    assert metadata
    for header in metadata.values():
        assert isinstance(header, dict)


def test_load_sources_returns_bibtex_database():
    sources = load_criteria("sources")
    # pybtex BibliographyData exposes an 'entries' mapping.
    assert hasattr(sources, "entries")
    assert len(sources.entries) > 0


# ---------------------------------------------------------------------------
# load_criteria: multiple components and load_all
# ---------------------------------------------------------------------------


def test_load_criteria_list_returns_keyed_dict():
    result = load_criteria(["criteria-types", "criteria-variables"])
    assert set(result) == {"criteria-types", "criteria-variables"}


def test_load_all_returns_every_component():
    result = load_criteria(load_all=True)
    assert set(result) == COMPONENTS


# ---------------------------------------------------------------------------
# load_criteria: subset filtering
# ---------------------------------------------------------------------------


def test_criteria_types_subset_filters_thresholds():
    df = load_criteria(
        "criteria-thresholds", criteria_types="Historical Vetting"
    )
    prefixes = {c.split("|", 1)[0] for c in df["criterion"]}
    assert prefixes == {"Historical Vetting"}


def test_unknown_criteria_type_raises():
    with pytest.raises(Exception):
        load_criteria("criteria-thresholds", criteria_types="Nonexistent")


def test_reference_subset_filters_reference_data():
    all_data = load_criteria("reference-data")
    one = all_data["reference_data"].iloc[0]
    subset = load_criteria("reference-data", reference_subset=one)
    assert set(subset["reference_data"].unique()) == {one}


def test_unknown_reference_subset_raises():
    with pytest.raises(Exception):
        load_criteria("reference-data", reference_subset="nonexistent-dataset")
