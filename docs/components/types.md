The following types of validation criteria are defined.

```python exec="true" session="index" showcode="false"
import pandas as pd
from scenario_validation_criteria import load_criteria

criteria_types = load_criteria("criteria-types")

print(
    pd.DataFrame.from_dict(criteria_types, orient="index")
    .reset_index()
    .rename(columns={"index": "type", 0: "description"})
    .assign(
        type=lambda df: "`" + df["type"] + "`",
    )
    .rename(columns=lambda x: x.upper())
    .to_markdown(index=False)
)
```
