Each criterion is defined with one or more upper and/or lower threshold 
values. Scenarios with reported values outside the range are marker with the 
respective validation outcome.

The possible validation outcomes depend on the [criterion type](types.md). 
Feasibility and sustainability concerns mark scenarios as either `ok`, `medium` 
or  `high`, whereas historical vetting mark scenarios as `ok` or `failed`.

Scenarios that do not report all variables that are part of the vetting are 
marked as `insufficient reporting`. Feasibility and sustainability concerns 
where the relevant variable is not reported by the scenario are marked as 
`not assigned`.

Some thresholds are defined in relation to some reference, as set by the
reference data column. The [reference data](reference_data.md) is defined
separately. The values defined as thresholds therefore have to be multiplied
with the values from the reference data before applying the criteria to scenario
data.

```python exec="true" session="index" showcode="false"
import pandas as pd
from scenario_validation_criteria import load_criteria

for crit_type in load_criteria("criteria-types"):
    print(f"## {crit_type}")
    
    criteria_thrsh, criteria_meta = load_criteria(
        ["criteria-thresholds", "criteria-descriptions"],
        criteria_types=crit_type,
    ).values()
    
    print(
        criteria_thrsh
        .rename(columns=lambda x: x.upper().replace("_", " "))
        .apply(
            lambda col: col.str.replace("|", r"\|")
            if col.dtype == "object" else
            col
        )
        .fillna("")
        .to_markdown(index=False) + "\n\n"
    )
```
