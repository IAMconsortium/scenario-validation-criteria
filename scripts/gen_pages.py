"""Generate criteria definition documentation pages."""
from pathlib import Path

import mkdocs_gen_files


partials_dir = Path(__file__).parent.parent / "docs" / "partials"
if not partials_dir.is_dir():
    raise Exception("Partials directory not found!")


summary_partial = "summary"
component_partials = [
    "types",
    "descriptions",
    "thresholds",
    "reference_data",
    "sources",
]
all_partials = [summary_partial] + component_partials


summary_page_template = """\
{{% include 'partials/{partial}.md' %}}
"""

component_page_template = """
{{% include 'partials/{partial}.md' %}}
"""

# Write summary page.
with mkdocs_gen_files.open(f"{summary_partial}.md", "w") as file_handle:
    file_handle.write(summary_page_template.format(partial=summary_partial))

# Write component pages.
for partial in component_partials:
    with mkdocs_gen_files.open(f"{partial}.md", "w") as file_handle:
        file_handle.write(component_page_template.format(partial=partial))

# Build nav.
home_nav = [
    "- [Home](index.md)\n",
]
summary_nav = [
    "- [Summary](summary.md)\n",
]
component_nav = (
    ["- Components\n"]
    + [
        f"    - [{partial.capitalize().replace('_', ' ')}]({partial}.md)\n"
        for partial in component_partials
    ]
)

with open(partials_dir.parent / "nav.md") as file_handle:
    static_nav_lines = file_handle.readlines()

with mkdocs_gen_files.open("nav.md", "w") as file_handle:
    file_handle.writelines(home_nav + summary_nav + component_nav + static_nav_lines)
