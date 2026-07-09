This page gives a criterion-by-criterion overview of all validation criteria,
combining the scientific justifications with the computed threshold values.

```python exec="true" session="summary" showcode="false"
import re
import pandas as pd
from sigfig import round as sf_round
from itables import to_html_datatable
from scenario_validation_criteria import load_criteria
from scenario_validation_criteria.preprocessed import load_criteria_combined
from scenario_validation_criteria.formatting import format_sources, insert_citations

criteria_combined = load_criteria_combined().query("region == 'World'")
criteria_types, criteria_meta, sources = load_criteria(
    ["criteria-types", "criteria-descriptions", "sources"],
).values()
sources_formatted = format_sources(sources)


def _fmt(text):
    return insert_citations(text, sources_formatted, "").replace("\n", "<br>")


def _fmt_num(v):
    if pd.isna(v):
        return v
    if v == 0:
        return 0.0
    if abs(v) >= 100:
        return round(v, 0)
    return float(sf_round(str(v), sigfigs=3))


def _pivot(df):
    """Pivot lower/upper bounds into columns, including relative and reference values."""
    d = df.drop(columns="criterion").copy()
    d["year"] = d["year"].astype("object").where(d["year"].notna(), other="")
    has_ref = d["value_rel"].notna().any()

    # Pivot absolute values, relative multipliers, and reference values together.
    pivoted = (
        d.pivot_table(
            index=["variable", "region", "year", "validation_outcome", "unit"],
            columns="threshold_type",
            values=["value", "value_rel", "reference_value"],
            aggfunc="first",
        )
    )
    name_map = {
        ("value", "lower"): "Lower (abs)", ("value", "upper"): "Upper (abs)",
        ("value_rel", "lower"): "Lower (rel)", ("value_rel", "upper"): "Upper (rel)",
        ("reference_value", "lower"): "Lower (ref)", ("reference_value", "upper"): "Upper (ref)",
    }
    pivoted.columns = [name_map.get(c, "_".join(c)) for c in pivoted.columns]
    pivoted = pivoted.reset_index()

    if has_ref:
        # reference_data_expr is the same for both threshold types; attach once.
        ref_expr = (
            d.groupby(["variable", "year", "validation_outcome"], dropna=False)
            ["reference_data_expr"].first().reset_index()
        )
        pivoted = pivoted.merge(ref_expr, on=["variable", "year", "validation_outcome"], how="left")

        for col in ["Lower (rel)", "Upper (rel)"]:
            pivoted[col] = pivoted[col].apply(
                lambda v: f"{(v - 1) * 100:+.0f}%" if pd.notna(v) else v
            )
        for col in ["Lower (ref)", "Upper (ref)"]:
            pivoted[col] = pivoted[col].apply(
                _fmt_num
            )
        pivoted["reference_data_expr"] = pivoted["reference_data_expr"].apply(
            lambda v: re.sub(r"^range\((.+)\)$", r"Most permissive value of: \1", v)
            if pd.notna(v) else v
        )

    for col in ["Lower (abs)", "Upper (abs)"]:
        if col in pivoted.columns:
            pivoted[col] = pivoted[col].apply(
                _fmt_num
            )

    col_order = [
        "variable", "region", "year", "unit", "validation_outcome",
        "Lower (abs)",
        *(["Lower (rel)", "Lower (ref)"] if has_ref else []),
        "Upper (abs)",
        *(["Upper (rel)", "Upper (ref)"] if has_ref else []),
        *(["reference_data_expr"] if has_ref else []),
    ]
    result = pivoted[[c for c in col_order if c in pivoted.columns]]
    result = result.rename(columns={"reference_data_expr": "reference_data"})
    return result.rename(columns=lambda c: c.replace("_", " ").capitalize())


# Ordered list of criteria within the combined df (preserves CSV row order)
ordered_criteria = list(dict.fromkeys(criteria_combined["criterion"]))

for crit_type in criteria_types:
    type_criteria = [c for c in ordered_criteria if c.startswith(f"{crit_type}|")]
    if not type_criteria:
        continue

    print(f"## {crit_type}\n")

    type_spec = criteria_types[crit_type]
    print(f"{_fmt(type_spec['description'])}\n")
    print("**Possible validation outcomes:**\n")
    for outcome, outcome_desc in type_spec["validation_outcomes"].items():
        print(f"* `{outcome}` — {outcome_desc}")
    print("")

    for criterion in type_criteria:
        criterion_name = criterion.split("|", 1)[1]
        print(f"### {criterion_name}\n")

        meta = criteria_meta.get(criterion, {})
        if jc := meta.get("justification_criterion"):
            print(f"**Why this criterion?** {_fmt(jc)}\n")
        if jt := meta.get("justification_threshold"):
            print(f"**Why this threshold?** {_fmt(jt)}\n")

        df = _pivot(criteria_combined[criteria_combined["criterion"] == criterion].copy())
        table_html = to_html_datatable(df, connected=True, style="width:100%")
        print(f"<div>\n{table_html}\n</div>\n")

        if note := meta.get("note"):
            print(f"!!! note\n\n    {_fmt(note).replace("\n", "\n    ")}\n")

print("---\n\n## Sources\n")

df_srcs = pd.DataFrame.from_dict(sources_formatted, orient="index").reset_index()

{% raw %}

def _src_links(row):
    ret = []
    if row["url_doi"]:
        ret.append(
            "[ :simple-doi: DOI ]"
            f"({row['url_doi']})"
            "{ .sm-button } "
        )
    if row["url"] and (not row["doi"] or (row["doi"] == row["url_doi"])):
        ret.append(
            "[ :material-link-box: URL ]"
            f"({row['url']})"
            "{ .sm-button } "
        )
    if row["pdf"]:
        ret.append(
            "[ :fontawesome-solid-file-pdf: PDF ]"
            f"({row['pdf']})"
            "{ .sm-button } "
        )
    return "<br>".join(ret)

{% endraw %}

col1 = df_srcs["index"].apply(lambda r: f'<p id="{r}">`{r}`</p>').rename("Identifier")
col2 = df_srcs["bib"].rename("Bibliographic information")
col3 = df_srcs.apply(_src_links, axis=1).rename("Links")

print(
    pd.concat([col1, col2, col3], axis=1)
    .apply(lambda col: col.str.replace("|", "\\|").str.replace("\n", " "))
    .fillna("")
    .to_markdown(index=False)
)
```
