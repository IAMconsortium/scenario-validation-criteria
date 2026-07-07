The reference data is used to define some of the [criteria thresholds](thresholds.md).
The identifiers in the reference data column of the thresholds correspond to
the dataset identifiers listed below.

```python exec="true" session="refdata" showcode="false"
from itables import to_html_datatable
from scenario_validation_criteria import load_criteria
from scenario_validation_criteria.formatting import format_sources

sources = load_criteria("sources")
sources_formatted = format_sources(sources)
reference_data_all, reference_metadata = load_criteria(
    ["reference-data", "reference-metadata"],
).values()

all_datasets = sorted(reference_data_all["reference_data"].unique())


def source_link(source_key):
    if not source_key:
        return "—"
    page = f"../sources/#{source_key}"
    cite = (
        sources_formatted[source_key]["cite"]
        if source_key in sources_formatted
        else source_key
    )
    return f"[{cite}]({page})"


# Overview table
print("| Dataset | Source | Description |")
print("|---|---|---|")
for ref in all_datasets:
    meta = reference_metadata.get(ref, {})
    src = source_link(meta.get("source"))
    desc = meta.get("description", "").replace(
        "{% raw %}{{source}}{% endraw %}", src
    )
    print(f"| [`{ref}`](#{ref.lower()}) | {src} | {desc} |")

print()

# Per-dataset sections
for ref in all_datasets:
    meta = reference_metadata.get(ref, {})
    src = source_link(meta.get("source"))
    desc = meta.get("description", "").replace(
        "{% raw %}{{source}}{% endraw %}", src
    )
    df = (
        reference_data_all[reference_data_all["reference_data"] == ref]
        .drop(columns="reference_data")
    )
    print(f"\n## {ref}\n")
    if desc:
        print(f"{desc}\n")
    table_html = to_html_datatable(df, connected=True, style="width:100%")
    print(f"<div>\n{table_html}\n</div>\n")
```
