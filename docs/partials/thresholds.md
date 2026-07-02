Each criterion comes with a set of threshold values that scenarios have to
surpass in order to be assigned a specific level of concern in regards to this
criterion.

The thresholds values come in two levels of concern: medium concern and strong
concern.

Some thresholds are defined in relation to some reference, as set by the
reference data column. The [reference data](../reference_data.md) is defined
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
