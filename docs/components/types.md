The following types of validation criteria are defined.

```python exec="true" session="index" showcode="false"
import pandas as pd
from scenario_validation_criteria import load_criteria

criteria_types = load_criteria("criteria-types")


def _format_outcomes(outcomes):
    return "<br>".join(f"`{key}`: {desc}" for key, desc in outcomes.items())


rows = [
    {
        "type": f"`{name}`",
        "description": spec["description"],
        "validation outcomes": _format_outcomes(spec["validation_outcomes"]),
    }
    for name, spec in criteria_types.items()
]

print(
    pd.DataFrame(rows)
    .rename(columns=lambda x: x.upper())
    .to_markdown(index=False)
)
```
