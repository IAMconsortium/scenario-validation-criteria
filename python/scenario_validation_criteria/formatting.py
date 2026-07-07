"""Format bibliographic information on sources."""

import re
from typing import Optional

try:
    from pybtex.database import BibliographyData
    from pybtex.plugin import find_plugin
except ImportError as e:
    raise ImportError(
        "The formatting of sources requires the 'pybtex' package."
    ) from e


def format_sources(
    bib_data: BibliographyData,
    style: str = "alpha",
    target: str = "plaintext",
    exclude_fields: Optional[list] = None,
) -> dict[str, str]:
    """Convert sources to specific format.

    Takes a citation style, a citation format, and (optionally) excluded
    fields, and returns a formatted list of sources based on the specified
    style and format. The sources are loaded from 'sources.bib' file.

    When two or more entries share the same first author and year, a
    lower-case letter suffix is appended to the year to disambiguate them
    (e.g. "IAEA, 2024a" and "IAEA, 2024b"). Entries within each collision
    group are sorted alphabetically by their BibTeX key to ensure a
    deterministic assignment of letters.

    Parameters
    ----------
    bib_data
        Bibliography data loaded from BibTeX file.
    style
        Specifies the formatting style for the bibliography entries.
    target
        Specifies the format in which the citation should be rendered.
        It determines how the citation information will be displayed or
        structured in the final output. This can be 'plaintext' or 'html'.
    exclude_fields
        Specifies a list of fields that should be excluded from the
        final output. These fields will be removed from the entries
        before formatting and returning the citation data.

    Returns
    -------
        list[dict]
            A list of dictionaries containing the identifier, citation,
            and URL information for each entry in the bibliography
            data, formatted according to the specified style and form,
            with any excluded fields removed.

    """
    from collections import defaultdict

    exclude_fields = exclude_fields or []

    # --- Pass 1: collect (cite_auth, cite_year) for every entry ----------
    auth_year: dict[str, tuple[str, str]] = {}
    for identifier, entry in bib_data.entries.items():
        first_author = entry.persons.get("author", [])[0].last_names
        cite_auth = re.sub("[{}]", "", " ".join(first_author))
        cite_year = entry.fields.get("year", "n.d.")
        auth_year[identifier] = (cite_auth, str(cite_year))

    # --- Assign disambiguation suffixes for (auth, year) collisions ------
    groups: dict[tuple[str, str], list[str]] = defaultdict(list)
    for identifier, key in auth_year.items():
        groups[key].append(identifier)

    suffixes: dict[str, str] = {}
    for ids in groups.values():
        if len(ids) > 1:
            for i, identifier in enumerate(sorted(ids)):
                suffixes[identifier] = chr(ord("a") + i)

    # --- Patch year fields in-place before formatting --------------------
    for identifier, suffix in suffixes.items():
        entry = bib_data.entries[identifier]
        entry.fields["year"] = auth_year[identifier][1] + suffix

    # --- Exclude undesired fields ----------------------------------------
    if exclude_fields:
        for entry in bib_data.entries.values():
            for ef in exclude_fields:
                if ef in entry.fields.__dict__["_dict"]:
                    del entry.fields.__dict__["_dict"][ef]

    # --- Pass 2: format each entry ---------------------------------------
    pyb_style = find_plugin("pybtex.style.formatting", style)()
    pyb_format = find_plugin("pybtex.backends", target)()

    ret = {}
    for identifier in bib_data.entries:
        try:
            entry = bib_data.entries[identifier]
            cite_auth, base_year = auth_year[identifier]
            suffix = suffixes.get(identifier, "")
            cite_year = base_year + suffix

            doi = entry.fields.get("doi", None)
            url = entry.fields.get("url", None)
            pdf = entry.fields.get("pdf", None)
            url_doi = f"https://doi.org/{doi}" if doi else None

            if doi:
                del entry.fields["doi"]
            if url:
                del entry.fields["url"]
            if pdf:
                del entry.fields["pdf"]

            bib = next(pyb_style.format_entries([entry])).text.render(
                pyb_format
            )

            ret[identifier] = {
                "cite_auth": cite_auth,
                "cite_year": cite_year,
                "cite": f"{cite_auth} ({cite_year})",
                "citep": f"({cite_auth}, {cite_year})",
                "bib": bib,
                "doi": doi,
                "url_doi": url_doi,
                "url": url or url_doi,
                "pdf": pdf,
            }
        except Exception as ex:
            raise Exception(
                f"Error occurred while parsing '{identifier}':\n{ex}"
            )

    return ret


def insert_citations(
    text: str,
    citations: dict[str, dict[str, str]],
    link: str | None = None,
) -> str:
    """Insert citations into placeholders in a text.

    Parameters
    ----------
    text
        Text that contains replacement patterns for citations.
    citations
        Formatted citations for each identifier.
    link
        Top-level page address for all citations.

    Returns
    -------
        str
            The updated text, which has the patterns replaced with citations.

    """
    return re.sub(
        r"{{(cite|citep):([^}]+)}}",
        lambda m: (
            (f'<a href="{link}#{m.group(2)}">' if link is not None else "")
            + citations.get(m.group(2), {}).get(m.group(1), m.group(0))
            + ("</a>" if link is not None else "")
        ),
        text,
    )
