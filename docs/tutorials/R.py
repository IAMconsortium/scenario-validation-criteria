# -*- coding: utf-8 -*-
# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.17.2
#   kernelspec:
#     display_name: R
#     language: R
#     name: ir
# ---

# This has to be run in order to compile this notebook while the R package is still under development.

devtools::load_all()

# ## Installation

# While the R package has not been released yet, you have to install it from GitHub source using:
#
# ```R
# devtools::install_github('PhilippVerpoort/scenario-vetting-criteria')
# ```

# ## Raw file paths

# The package contains definition files for the criteria. The paths to those files are contained in `file_paths`.

# +
library(scenariovalidationcriteria)

for (component_id in names(file_paths)) {
  component_path <- file_paths[[component_id]]
  print(paste0(component_id, ":  ...", substr(as.character(component_path), nchar(as.character(component_path)) - 39, nchar(as.character(component_path)))))
}
# -

# ## Load functions

# Instead of loading the data from these files manually, it is recommended to use the built-in load functions from the package via `load_criteria`. For instance, the following will load the definition of the thresholds values.

load_criteria('criteria-thresholds')

# Multiple files can be loaded in one go.

criteria <- load_criteria(c('criteria-thresholds', 'operations'))
criteria$operations

# ## Apply vetting criteria to scenarios

# A tutorial on how to apply the vetting criteria to a list of scenarios based on [piamValidation](https://pik-piam.github.io/piamValidation/) will be made available later.
