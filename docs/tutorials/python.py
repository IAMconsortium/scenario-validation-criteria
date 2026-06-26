# ---
# jupyter:
#   jupytext:
#     formats: py:percent
#     notebook_metadata_filter: source_hidden
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.17.2
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
#   source_hidden: true
# ---

# %% [markdown]
# ## Installation

# %% [markdown]
# While the Python package has not been released yet, you have to install it from GitHub source using:
#
# ```bash
# # When using poetry.
# poetry add git+https://github.com:PhilippVerpoort/scenario-vetting-criteria.git
#
# # When using pip.
# pip install git+https://github.com:PhilippVerpoort/scenario-vetting-criteria.git
# ```

# %% [markdown]
# ## Load functions

# %% [markdown]
# Use the built-in load functions from the package via `load_criteria`. For instance, the following will load the definition of the thresholds values.

# %%
from scenario_vetting_criteria import load_criteria

load_criteria("criteria-thresholds")

# %% [markdown]
# Multiple files can be loaded in one go.

# %%
criteria = load_criteria(["criteria-thresholds", "reference-data"])
display(criteria["reference-data"])

# %% [markdown]
# ## Formatting citations and sources

# %% [markdown]
# Loading the reference sources from the BibTeX file will return a pybtex object.

# %%
sources = load_criteria("sources")

# %% [markdown]
# The entries in this object can be formatted according to some predefined style.

# %%
from scenario_vetting_criteria.formatting import format_sources
sources_formatted = format_sources(sources)
display(sources_formatted["Creutzig-2014"])

# %% [markdown]
# The `insert_citations` function can be used to insert citations into text with citation patterns.

# %%
from scenario_vetting_criteria.formatting import insert_citations

text = load_criteria("criteria-descriptions")["Sustainability Concern|Unsustainable Bioenergy Use"]["justification_threshold"]
text_inserted = insert_citations(text, sources_formatted)

print(text[:50], "...   →  ", text_inserted[:43], "...")

# %% [markdown]
# ## Apply vetting criteria to scenarios

# %% [markdown]
# A tutorial on how to apply the vetting criteria to a list of scenarios based on the [IAMC Nomenclature](https://nomenclature-iamc.readthedocs.io/en/stable/user_guide.html) package will be made available later.
