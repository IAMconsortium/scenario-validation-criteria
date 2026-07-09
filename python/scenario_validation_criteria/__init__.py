"""Definitions of scenario validation criteria.

Use the `load_criteria` function to load definitions from raw definition files.
"""

from pathlib import Path

import pandas
import yaml


# Define path to data directory and check if it exists.
DATA_DIR: Path = Path(__file__).parent / "data"
if not DATA_DIR.is_dir():
    raise Exception("Could not find data directory.")


# Single criteria directory (no versioning).
CRITERIA_DIR: Path = DATA_DIR


# Component options that can be loaded.
COMPONENTS: set[str] = {
    "criteria-thresholds",
    "criteria-variables",
    "criteria-descriptions",
    "criteria-types",
    "reference-data",
    "reference-metadata",
    "sources",
}


# Column definitions of the thresholds CSVs.
THRESHOLD_COLS_DTYPES: dict[str, str] = {
    "criterion": "str",
    "variable": "str",
    "region": "str",
    "year": "str",
    "reference_data": "str",
    "unit": "str",
    "validation_outcome": "str",
    "upper": "float64",
    "lower": "float64",
}


def _format_prefix(prefix: str) -> str:
    """Convert dashes to spaces and capitalise every word."""
    return " ".join(word[:1].upper() + word[1:] for word in prefix.split("-"))


def _deformat_prefix(label: str) -> str:
    """Inverse of `_format_prefix`: lower-case and convert spaces to dashes.

    Idempotent for directory-form input (already lower-case, no spaces).
    """
    return label.lower().replace(" ", "-")


def _expand_metadata_templates(metadata: dict) -> dict:
    """Expand template metadata entries into individual entries.

    Template entries (those with a 'replacements' field) in a metadata dict
    are expanded into individual entries, applying all substitutions to
    both the criterion key and the text fields.

    A template entry looks like:
        "Criterion|{VarName}":
            justification_criterion: "... {text_sub} ..."
            replacements:
                VarName:
                    OptionA:
                        text_sub: value_a
                    OptionB:
                        text_sub: value_b
    """
    import itertools

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


# Load criteria definitions from a specific criteria file.
def _load_criteria_file(
    component: str,
    criteria_types: list[str],
    reference_subset: list[str],
    criteria_dir: Path,
):
    match component:
        # Load and combine all criteria definitions. Load threshold CSV files
        # into a dataframe or metadata YAML files into a dict.
        case "criteria-thresholds" | "criteria-descriptions":
            criteria_dirs = {
                criteria_dir.name: criteria_dir
                for criteria_dir in (criteria_dir / "criteria").glob("*")
                if criteria_dir.is_dir()
            }
            if criteria_types is not None:
                # Accept formatted labels (e.g. "Historical Vetting") by
                # converting them back to directory-name form.
                criteria_types = [
                    _deformat_prefix(ct) for ct in criteria_types
                ]
                criteria_dirs = {
                    k: v
                    for k, v in criteria_dirs.items()
                    if k in criteria_types
                }
                unknown = [r for r in criteria_types if r not in criteria_dirs]
                if unknown:
                    raise Exception(
                        f"Criteria type unknown: {', '.join(unknown)}"
                    )
                criteria_dirs = dict(
                    sorted(
                        criteria_dirs.items(),
                        key=lambda d: criteria_types.index(d[0]),
                    )
                )

            if component == "criteria-thresholds":
                return pandas.concat(
                    [
                        pandas.read_csv(
                            crit_dir / "thresholds.csv",
                            delimiter=",",
                            quotechar='"',
                            comment="#",
                            dtype=THRESHOLD_COLS_DTYPES,
                        ).assign(
                            criterion=lambda df, ct=criteria_type: (
                                f"{_format_prefix(ct)}|" + df["criterion"]
                            )
                        )
                        for criteria_type, crit_dir in criteria_dirs.items()
                    ],
                    ignore_index=True,
                )
            elif component == "criteria-descriptions":
                ret = {}
                for criteria_type, criteria_dir in criteria_dirs.items():
                    with (
                        criteria_dir / "descriptions.yaml"
                    ).open() as file_handle:
                        crit_defs = yaml.safe_load(file_handle)
                        crit_defs = _expand_metadata_templates(crit_defs)
                        prefix = _format_prefix(criteria_type)
                        ret |= {
                            f"{prefix}|" + crit_key: crit_specs
                            for crit_key, crit_specs in crit_defs.items()
                        }

                return ret

        # Load criteria variables.
        case "criteria-variables":
            criteria_thresholds = _load_criteria_file(
                component="criteria-thresholds",
                criteria_types=criteria_types,
                reference_subset=reference_subset,
                criteria_dir=CRITERIA_DIR,
            )
            return (
                criteria_thresholds["variable"]
                .str.split(",")
                .explode()
                .str.strip()
                .drop_duplicates()
                .sort_values()
                .tolist()
            )

        # Load criteria types from YAML files into a dict.
        case "criteria-types":
            with (criteria_dir / "criteria-types.yaml").open() as file_handle:
                return yaml.safe_load(file_handle)

        # Load and combine the reference data CSV files into a dataframe.
        case "reference-data" | "reference-metadata":
            # Get list of reference data to load.
            file_paths = (criteria_dir / "reference-data").glob("*.csv")
            reference_data = {
                file_path.stem: file_path for file_path in file_paths
            }
            if reference_subset is not None:
                reference_data = {
                    k: v
                    for k, v in reference_data.items()
                    if k in reference_subset
                }
                unknown = [
                    r for r in reference_subset if r not in reference_data
                ]
                if unknown:
                    raise Exception(
                        f"Reference datasets unknown: {', '.join(unknown)}"
                    )
            reference_data = dict(sorted(reference_data.items()))

            # Load data.
            if component == "reference-data":
                return pandas.concat(
                    [
                        pandas.read_csv(
                            ref_data_path,
                            delimiter=",",
                            quotechar='"',
                            comment="#",
                        ).assign(reference_data=ref_data)
                        for ref_data, ref_data_path in reference_data.items()
                    ],
                    ignore_index=True,
                )
            # Load metadata.
            elif component == "reference-metadata":
                ret = {}
                for ref_data, ref_data_path in reference_data.items():
                    with open(ref_data_path) as file_handle:
                        lines = []
                        for line in file_handle:
                            if line.startswith("#"):
                                lines.append(line[1:])
                            else:
                                continue
                        ret[ref_data] = yaml.safe_load("\n".join(lines)) or {}
                return ret
        case "sources":
            try:
                from pybtex.database.input import bibtex
            except ModuleNotFoundError:
                raise Exception(
                    f"Loading '{component}' requires pybtex to be installed."
                )
            with (criteria_dir / "sources.bib").open("r") as file_stream:
                return bibtex.Parser().parse_file(file_stream)
        case c:
            raise Exception(f"Unknown component: {c}")


# Load all criteria definitions.
def load_criteria(
    components: str | list[str] | tuple[str] | None = None,
    load_all: bool = False,
    criteria_types: str | list[str] | None = None,
    reference_subset: str | list[str] | tuple[str] | None = None,
):
    """Load and return the criteria definitions contained in the package.

    Parameters
    ----------
    components : str | list[str] | tuple[str], optional
        A string or list/vector of strings. The return type changes depending
        on whether a list/vector or a single string is provided.
    load_all : bool, optional
        Alternatively to providing the names of individual components, the
        loading of all components can be instructed with the key-word argument
        `load_all=True`.
    criteria_types : str | list[str] | tuple[str], optional
        When loading the components `thresholds` and `descriptions`, by default
        all criteria types are loaded. Alternatively, a single string or a
        list or tuple of strings can be provided as argument `criteria_types`
        to load only a subset of criteria of corresponding type(s).
    reference_subset : str | list[str] | tuple[str], optional
        When loading the component `reference-data`, by default all sources
        are loaded. Alternatively, a single string or a list or tuple of
        strings can be provided as argument `reference_subset` to load only
        a subset of sources.

    Returns
    -------
    pd.DataFrame | dict[str, str] | dict[str, pd.DataFrame | dict[str, str]]
        Returns the loaded data. This data can be a dataframe or a nested
        list. If multiple data components are requested, then the components
        are returned inside a keyworded list.

    """
    if components is None and not load_all:
        raise Exception(
            "At least one component must be provided as function argument."
        )
    if components is not None and load_all:
        raise Exception(
            "Component name(s) and `load_all` cannot be provided as arguments "
            "at the same time."
        )
    if load_all:
        components = list(COMPONENTS)
    if criteria_types is not None:
        if isinstance(criteria_types, str):
            criteria_types = [criteria_types]
        elif not isinstance(criteria_types, tuple):
            criteria_types = list(criteria_types)
    if reference_subset is not None:
        if isinstance(reference_subset, str):
            reference_subset = [reference_subset]
        elif isinstance(reference_subset, tuple):
            reference_subset = list(reference_subset)
    if isinstance(components, str):
        return _load_criteria_file(
            component=components,
            criteria_types=criteria_types,
            reference_subset=reference_subset,
            criteria_dir=CRITERIA_DIR,
        )
    elif isinstance(components, list) and all(
        isinstance(c, str) for c in components
    ):
        return {
            component: _load_criteria_file(
                component=component,
                criteria_types=criteria_types,
                reference_subset=reference_subset,
                criteria_dir=CRITERIA_DIR,
            )
            for component in components
        }
    else:
        raise Exception(
            "Argument `components` must be string or list of strings."
        )


__all__ = [
    "load_criteria",
]
