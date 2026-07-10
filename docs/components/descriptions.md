The descriptions contain contextual information about why a criterion is
necessary/relevant and how its threshold values were chosen.

```python exec="true" session="index" showcode="false"
import pandas as pd
from scenario_validation_criteria import load_criteria
from scenario_validation_criteria.formatting import (format_sources,
                                                  insert_citations)


for crit_type in load_criteria("criteria-types"):
    print(f"## {crit_type}")

    criteria_meta, criteria_types, sources = load_criteria(
        ["criteria-descriptions", "criteria-types", "sources"],
        criteria_types=crit_type,
    ).values()
    sources_formatted = format_sources(sources)
    
    print(
        pd.DataFrame.from_dict(criteria_meta, orient="index")
        .reset_index()
        .fillna("")
        .assign(
            index=lambda df: "`" + df["index"] + "`",
            justification_threshold=lambda df: df["justification_threshold"].apply(
                insert_citations, args=(sources_formatted, "../sources/")),
            justification_criterion=lambda df: df["justification_criterion"].apply(
                insert_citations, args=(sources_formatted, "../sources/")),
        )
        .rename(columns={
            "index": "NAME",
            "justification_criterion": "JUSTIFICATION OF THE CRITERION<br>(Why this criterion?)",
            "justification_threshold": "JUSTIFICATION OF THE THRESHOLD<br>(Why this threshold?)",
            "note": "NOTE",
        })
        .apply(
            lambda col: col.str.replace("\n", "<br>")
            if col.dtype == "object"
            else col
        )
        .to_markdown(index=False) + "\n\n"
    )
```
