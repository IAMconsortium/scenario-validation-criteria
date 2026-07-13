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
# devtools::install_github('IAMconsortium/scenario-validation-criteria')
# ```

# ## Load functions

# Instead of loading the data from these files manually, it is recommended to use the built-in load functions from the package via `load_criteria`. For instance, the following will load the definition of the thresholds values.

load_criteria('criteria-thresholds')

# Multiple files can be loaded in one go.

criteria <- load_criteria(c('criteria-thresholds', 'reference-data'))
criteria[['reference-data']]

# ## Apply vetting criteria to scenarios

# A tutorial on how to apply the vetting criteria to a list of scenarios based on [piamValidation](https://pik-piam.github.io/piamValidation/) will be made available later.
