# Define path to data directory and check if it exists.
.DATA_DIR <- paste0(system.file(package = "scenariovalidationcriteria"), "/extdata")
if (!dir.exists(.DATA_DIR)) {
    stop("Could not find data directory.")
}

.csv_engines <- c('read.csv', 'readr', 'data.table')


.expand_metadata_templates <- function(metadata) {
    result <- list()
    for (key in names(metadata)) {
        spec <- metadata[[key]]
        if (is.null(spec[["replacements"]])) {
            result[[key]] <- spec
            next
        }
        replacements <- spec[["replacements"]]
        base_spec <- spec[names(spec) != "replacements"]
        var_names <- names(replacements)
        # Build list of (option_key, text_subs) pairs per variable.
        option_lists <- lapply(var_names, function(v) {
            lapply(names(replacements[[v]]), function(opt) {
                list(option_key = opt, text_subs = replacements[[v]][[opt]])
            })
        })
        # Cartesian product across variables.
        combos <- expand.grid(
            lapply(option_lists, seq_along),
            stringsAsFactors = FALSE
        )
        for (i in seq_len(nrow(combos))) {
            subs <- list()
            for (j in seq_along(var_names)) {
                entry <- option_lists[[j]][[combos[i, j]]]
                subs[[var_names[[j]]]] <- entry$option_key
                for (sub_var in names(entry$text_subs)) {
                    subs[[sub_var]] <- entry$text_subs[[sub_var]]
                }
            }
            new_key <- key
            for (sub_var in names(subs)) {
                sub_val <- subs[[sub_var]]
                if (identical(sub_val, "~")) {
                    # Tilde (~) entry: strip the placeholder and its adjacent pipe.
                    new_key <- gsub(paste0("\\|\\{", sub_var, "\\}"), "", new_key)
                    new_key <- gsub(paste0("\\{", sub_var, "\\}\\|"), "", new_key)
                    new_key <- gsub(paste0("\\{", sub_var, "\\}"), "", new_key)
                } else {
                    new_key <- gsub(paste0("\\{", sub_var, "\\}"), sub_val, new_key)
                }
            }
            new_spec <- lapply(base_spec, function(field_val) {
                if (is.character(field_val)) {
                    for (sub_var in names(subs)) {
                        sub_val <- subs[[sub_var]]
                        if (!identical(sub_val, "~")) {
                            field_val <- gsub(
                                paste0("\\{", sub_var, "\\}"),
                                sub_val, field_val
                            )
                        }
                    }
                }
                field_val
            })
            result[[new_key]] <- new_spec
        }
    }
    result
}

.format_prefix <- function(prefix) {
    # Convert dashes to spaces and capitalise every word.
    words <- strsplit(gsub("-", " ", prefix), " ", fixed = TRUE)[[1]]
    words <- paste0(toupper(substring(words, 1, 1)), substring(words, 2))
    paste(words, collapse = " ")
}

.deformat_prefix <- function(label) {
    # Inverse of .format_prefix: lower-case and convert spaces to dashes.
    # Idempotent for directory-form input (already lower-case, no spaces).
    tolower(gsub(" ", "-", label))
}

.read_csv <- function(file_path, csv_engine) {
    if (!(csv_engine %in% .csv_engines)) {
        stop(paste(
            "Unknown CSV engine:", csv_engine,
            ". Please choose one from:", toString(.csv_engines)
        ))
    }
    suppressMessages({
        if (csv_engine == 'read.csv') {
            read.csv(file_path, comment.char = "#")
        } else if (csv_engine == 'readr') {
            if (!requireNamespace("readr", quietly = TRUE)) {
                stop("CSV engine 'readr' requires the 'readr' package to be installed.")
            }
            readr::read_csv(file_path, comment = "#", show_col_types = FALSE)
        } else {
            if (!requireNamespace("data.table", quietly = TRUE)) {
                stop("CSV engine 'data.table' requires the 'data.table' package to be installed.")
            }
            lines <- readLines(file_path)
            data.table::fread(
                text = paste(lines[!startsWith(lines, "#")], collapse = "\n")
            )
        }
    })
}


.load_criteria_file <- function(
    component,
    csv_engine,
    criteria_types,
    reference_subset,
    data_dir
) {
    if (component %in% c("criteria-thresholds", "criteria-descriptions")) {
        # Build list of criteria-type directories.
        criteria_dirs <- list.dirs(
            file.path(data_dir, "criteria"),
            full.names = TRUE, recursive = FALSE
        )
        criteria_dirs <- setNames(as.list(criteria_dirs), basename(criteria_dirs))

        if (!is.null(criteria_types)) {
            # Accept formatted labels (e.g. "Historical Vetting") by
            # converting them back to directory-name form.
            criteria_types <- .deformat_prefix(criteria_types)
            unknown <- setdiff(criteria_types, names(criteria_dirs))
            if (length(unknown) > 0) {
                stop(paste("Criteria type(s) unknown:", toString(unknown)))
            }
            criteria_dirs <- criteria_dirs[criteria_types]
        }

        if (component == "criteria-thresholds") {
            dfs <- lapply(names(criteria_dirs), function(criteria_type) {
                df <- .read_csv(
                    file.path(criteria_dirs[[criteria_type]], "thresholds.csv"),
                    csv_engine
                )
                df$criterion <- paste0(.format_prefix(criteria_type), "|", df$criterion)
                df
            })
            do.call(rbind, dfs)
        } else {
            if (!requireNamespace("yaml", quietly = TRUE)) {
                stop("Loading 'criteria-descriptions' requires the 'yaml' package to be installed.")
            }
            ret <- list()
            for (criteria_type in names(criteria_dirs)) {
                crit_defs <- yaml::yaml.load_file(
                    file.path(criteria_dirs[[criteria_type]], "descriptions.yaml")
                )
                crit_defs <- .expand_metadata_templates(crit_defs)
                names(crit_defs) <- paste0(.format_prefix(criteria_type), "|", names(crit_defs))
                ret <- c(ret, crit_defs)
            }
            ret
        }

    } else if (component == "criteria-variables") {
        thresholds <- .load_criteria_file(
            "criteria-thresholds", csv_engine, criteria_types,
            reference_subset, data_dir
        )
        vars <- unlist(strsplit(as.character(thresholds$variable), ","))
        sort(unique(trimws(vars)))

    } else if (component == "criteria-types") {
        if (!requireNamespace("yaml", quietly = TRUE)) {
            stop("Loading 'criteria-types' requires the 'yaml' package to be installed.")
        }
        yaml::yaml.load_file(file.path(data_dir, "criteria-types.yaml"))

    } else if (component %in% c("reference-data", "reference-metadata")) {
        ref_files <- list.files(
            file.path(data_dir, "reference-data"),
            pattern = "\\.csv$", full.names = TRUE
        )
        ref_names <- tools::file_path_sans_ext(basename(ref_files))
        reference_data <- setNames(as.list(ref_files), ref_names)
        reference_data <- reference_data[order(names(reference_data))]

        if (!is.null(reference_subset)) {
            unknown <- setdiff(reference_subset, names(reference_data))
            if (length(unknown) > 0) {
                stop(paste("Reference dataset(s) unknown:", toString(unknown)))
            }
            reference_data <- reference_data[reference_subset]
        }

        if (component == "reference-data") {
            dfs <- lapply(names(reference_data), function(ref_name) {
                df <- .read_csv(reference_data[[ref_name]], csv_engine)
                df$reference_data <- ref_name
                df
            })
            do.call(rbind, dfs)
        } else {
            if (!requireNamespace("yaml", quietly = TRUE)) {
                stop("Loading 'reference-metadata' requires the 'yaml' package to be installed.")
            }
            ret <- list()
            for (ref_name in names(reference_data)) {
                lines <- readLines(reference_data[[ref_name]])
                comment_lines <- lines[startsWith(lines, "#")]
                stripped <- sub("^#", "", comment_lines)
                meta <- yaml::yaml.load(paste(stripped, collapse = "\n"))
                ret[[ref_name]] <- if (is.null(meta)) list() else meta
            }
            ret
        }

    } else if (component == "sources") {
        if (!requireNamespace("bibtex", quietly = TRUE)) {
            stop("Loading 'sources' requires the 'bibtex' package to be installed.")
        }
        bibtex::read.bib(file.path(data_dir, "sources.bib"))

    } else {
        stop(paste("Unknown component:", component))
    }
}


#' Load criteria definitions.
#'
#' Loads and returns the criteria definitions contained in the package.
#'
#' @param components A string or character vector of component names. The
#'   return type changes depending on whether a single string or a vector is
#'   provided. Available components: `"criteria-thresholds"`,
#'   `"criteria-descriptions"`, `"criteria-variables"`, `"criteria-types"`,
#'   `"reference-data"`, `"reference-metadata"`, `"sources"`.
#' @param load_all Logical. Load all available components. Cannot be combined
#'   with `components`.
#' @param csv_engine The method for loading CSV files. One of `"read.csv"`
#'   (default), `"readr"`, or `"data.table"`.
#' @param criteria_types Character string or vector. When loading
#'   `"criteria-thresholds"` or `"criteria-descriptions"`, restrict to these
#'   criteria types only. Defaults to all types.
#' @param reference_subset Character string or vector. When loading
#'   `"reference-data"` or `"reference-metadata"`, restrict to these datasets
#'   only. Defaults to all datasets.
#'
#' @return The loaded data. A data frame or named list for a single component;
#'   a named list of those when multiple components are requested.
#'
#' @examples
#' df_thresholds <- load_criteria("criteria-thresholds")
#' print(df_thresholds)
#'
#' list_metadata <- load_criteria("criteria-descriptions")
#' print(list_metadata)
#'
#' criteria <- load_criteria(c("criteria-thresholds", "criteria-descriptions"))
#' print(criteria[["criteria-descriptions"]])
#'
#' @export
load_criteria <- function(
    components = NULL,
    load_all = FALSE,
    csv_engine = 'read.csv',
    criteria_types = NULL,
    reference_subset = NULL
) {
    all_components <- c(
        "criteria-thresholds",
        "criteria-variables",
        "criteria-descriptions",
        "criteria-types",
        "reference-data",
        "reference-metadata",
        "sources"
    )

    if (is.null(components) && !load_all) {
        stop("At least one component must be provided as a function argument.")
    }
    if (!is.null(components) && load_all) {
        stop("'components' and 'load_all' cannot be provided at the same time.")
    }
    if (load_all) {
        components <- all_components
    }

    data_dir <- .DATA_DIR

    if (is.character(components) && length(components) == 1) {
        .load_criteria_file(
            components, csv_engine, criteria_types, reference_subset, data_dir
        )
    } else if (is.character(components) && length(components) > 1) {
        result <- lapply(components, function(component) {
            .load_criteria_file(
                component, csv_engine, criteria_types, reference_subset, data_dir
            )
        })
        setNames(result, components)
    } else {
        stop("Argument 'components' must be a character string or character vector.")
    }
}
