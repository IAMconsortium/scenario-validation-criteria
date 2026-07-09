This page contains bibliographic information for the sources used for providing
the [reference data](reference_data.md) and in the justifications given in
the [criteria metadata](descriptions.md).

```python exec="true" session="index" showcode="false"
import pandas as pd
from scenario_validation_criteria import load_criteria
from scenario_validation_criteria.formatting import format_sources

sources = load_criteria("sources")
sources_formatted = format_sources(sources, target="html")
df_table = pd.DataFrame.from_dict(
    sources_formatted,
    orient="index",
).reset_index()

{% raw %}

def combine_urls(row: pd.Series) -> str:
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


col1 = (
    df_table["index"]
    .apply(lambda ref_id: f"<p id=\"{ref_id}\">`{ref_id}`</p>")
    .rename("Identifier")
)
col2 = df_table["bib"].rename("Bibliographic information")
col3 = df_table.apply(combine_urls, axis=1).rename("Links")

print(
    pd.concat([col1, col2, col3], axis=1)
    .apply(lambda col: col.str.replace("|", "\\|").str.replace("\n", " "))
    .fillna("")
    .to_markdown(index=False)
)
```
