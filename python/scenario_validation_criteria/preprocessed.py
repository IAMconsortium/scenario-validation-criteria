"""Preprocess criteria definitions for use with IAMC nomenclature package."""
import pandas as pd

from nomenclature import countries

from . import load_criteria


def load_criteria_combined() -> pd.DataFrame:
    """Load and combine criteria thresholds with reference data.

    Processes raw criteria definitions through six steps:
    melting bound types, exploding comma-separated fields, expanding
    ``All Countries``, resolving reference-data multipliers, and applying
    range/min/max operators across multiple sources.

    Returns
    -------
    pd.DataFrame
        One row per (criterion, variable, region, year, level_of_concern,
        threshold_type) combination with columns ``value`` and ``unit``.

    """
    # Step 0: Load the raw criteria definitions.
    criteria_thrsh = load_criteria("criteria-thresholds")
    reference_data = load_criteria("reference-data")

    # Step 1: Melt threshold types (upper, lower) into column.
    criteria_step1 = (
        criteria_thrsh.melt(
            id_vars=[c for c in criteria_thrsh if c not in ["upper", "lower"]],
            value_vars=["upper", "lower"],
            var_name="threshold_type",
        )
        .dropna(subset="value")
    )

    # Step 2: Explode comma-separated values in variable, region, and year
    # columns.
    criteria_tmp = criteria_step1.copy()
    for col_name in ["variable", "region", "year"]:
        criteria_tmp[col_name] = criteria_tmp[col_name].str.split(",")
        criteria_tmp = criteria_tmp.explode(col_name)
        criteria_tmp[col_name] = criteria_tmp[col_name].str.strip()

    criteria_step2 = (
        criteria_tmp
        .reset_index(drop=True)
        .astype({"year": "Int64"})
    )

    # Step 3: Replace `All Countries` with country codes and explode.
    all_countries = [country.alpha_3 for country in countries]
    criteria_step3 = (
        criteria_step2
        .assign(region=lambda df: df["region"].map(
            lambda r: all_countries if r == "All Countries" else r
        ))
        .explode("region")
        .reset_index(drop=True)
    )

    # Step 4: Explode sources; preserve the original full expression for display.
    criteria_step4 = (
        pd.concat([
            # Extract operator and individual source names from reference_data.
            criteria_step3["reference_data"].str.extract(
                r"(?P<reference_multi_operator>[a-z]+)?"
                r"\(?(?P<reference_data>[^\)]+)\)?"
            ),
            # Carry the original expression alongside the rest of the data.
            criteria_step3.drop(columns="reference_data").assign(
                reference_data_expr=criteria_step3["reference_data"].values
            ),
        ], axis=1)
        # Insert value `range` if operator is empty.
        .fillna({"reference_multi_operator": "range"})
        # Split list of sources by comma and expand.
        .assign(reference_data=lambda df: df["reference_data"].str.split(","))
        .explode("reference_data")
        .assign(reference_data=lambda df: df["reference_data"].str.strip())
        # Reset index.
        .reset_index(drop=True)
    )

    # Step 5: Merge with references list and compute absolute values.
    # Keep value_rel (the threshold multiplier) and reference_value (the
    # dataset value) so they can be surfaced by load_criteria_combined.
    criteria_step5 = (
        criteria_step4
        # Merge with reference data.
        .merge(
            reference_data,
            on=["reference_data", "variable", "region", "year"],
        )
        # Assign new value and unit; retain relative and reference columns.
        .assign(
            value=lambda df: df.value_y + (df.value_x - 1.0) * df.value_y.abs(),
            unit=lambda df: df.unit_y.fillna(df.unit_x),
            value_rel=lambda df: df.value_x,
            reference_value=lambda df: df.value_y,
        )
        # Combine with data that does not use a reference.
        .pipe(
            lambda df: pd.concat([
                df,
                criteria_step4.loc[criteria_step4["reference_data"].isnull()],
            ])
        )
        # Drop intermediate merge columns.
        .drop(columns=["value_x", "value_y", "unit_x", "unit_y"])
        .reset_index(drop=True)
    )

    # Step 6: Apply operator for multiple sources.
    # Track which source won (idxmin/idxmax) so value_rel and reference_value
    # reflect the actual source used for the aggregated absolute value.
    def combine(group):
        assert group["unit"].nunique() == 1, \
            "Unit must be the same across combined references."
        assert group["reference_multi_operator"].nunique() == 1, \
            "Operation must be the same across combined references."
        threshold_type = group.name[-1]
        # Determine operator
        operator = group["reference_multi_operator"].iloc[0]
        if operator == "range":
            operator = "min-max"
        if "-" in operator:
            operator = (
                operator
                .split("-")[["lower", "upper"]
                .index(threshold_type)]
            )
        # Find the winning row (min or max of the absolute value).
        agg_value = getattr(group["value"], operator)()
        winning_row = group.loc[getattr(group["value"], f"idx{operator}")()]
        return pd.Series({
            "value": agg_value,
            "unit": group["unit"].iloc[0],
            "value_rel": winning_row["value_rel"],
            "reference_value": winning_row["reference_value"],
            "reference_data": winning_row["reference_data"],
            "reference_data_expr": winning_row["reference_data_expr"],
        })

    return (
        criteria_step5
        .groupby([
            "criterion", "region", "year",
            "variable", "level_of_concern",
            "threshold_type",
        ], dropna=False)
        [["reference_multi_operator", "unit", "value",
          "value_rel", "reference_value", "reference_data", "reference_data_expr"]]
        .apply(combine)
        .reset_index()
    )


def load_criteria_for_validator() -> list[dict]:
    """Load criteria definitions for use with IAMC nomenclature validator.

    Returns
    -------
    list[dict]
        Criteria definitions for use with IAMC nomenclature validator.

    """
    criteria_combined = load_criteria_combined()

    # Convert dataframe to list of nested dictionaries and return.
    return (
        criteria_combined
        .query("region=='World'")
        .rename(columns={
            "criterion": "name",
            "level_of_concern": "warning_level",
        })
        .assign(
            name=lambda df:
                df["name"]
                + ("|" + df["region"].astype(str))
                .where(df["region"].notna(), other="")
                + ("|" + df["year"].astype(str))
                .where(df["year"].notna(), other=""),
            threshold_type=lambda df: df["threshold_type"] + "_bound",
            warning_level=lambda df: df["warning_level"].map({
                "strong": "high",
                "medium": "medium",
            }),
        )
        .drop(columns="unit")
        .pivot(
            index=["name", "region", "year", "variable", "warning_level"],
            columns="threshold_type",
            values="value",
        )
        .reset_index()
        .groupby(["name", "region", "year", "variable"], dropna=False)
        [["warning_level", "upper_bound", "lower_bound"]]
        .apply(lambda df: list(df.apply(lambda row: row.to_dict(), axis=1)))
        .to_frame("validation")
        .reset_index()
        .apply(lambda row: row.dropna().to_dict(), axis=1)
        .tolist()
    )
