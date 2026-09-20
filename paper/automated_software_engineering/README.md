# Automated Software Engineering manuscript

This directory contains the journal-specific English manuscript for
*Automated Software Engineering*. The original manuscript in `../en/` is kept
unchanged.

## Format decisions

- Springer Nature LaTeX template, December 2024 distribution
- `\documentclass[pdflatex,sn-basic]{sn-jnl}`
- Author-year citations and alphabetized references
- Single-blind title page with author names, affiliations, correspondence, and
  Liang Song's ORCID
- 161-word unstructured abstract and six keywords
- AI-tool use disclosed in Experimental Design
- Funding, competing interests, author contributions, availability, ethics,
  and consent statements included
- One embedded vector figure, named `Fig1.pdf`

The manuscript source is self-contained: it does not use `\input` or
`\include`. The required class, bibliography style, BibTeX database, and figure
are stored beside `main.tex` so the journal can compile a flat source archive.

## Build

Run:

```bash
./build.sh
```

The script uses `latexmk` with `pdflatex` and fails on unresolved references,
unresolved citations, overfull boxes, or fatal LaTeX errors.

## Submission status

Journal formatting is complete, the public source URL and versioned Zenodo DOI
are included, and both authors have confirmed originality, exclusive
submission, author order, contributions, funding, and competing interests. The
remaining actions are portal entry and inspection of the journal-generated PDF.

Journal guidance checked on 20 September 2026:

- https://link.springer.com/journal/10515/submission-guidelines
- https://link.springer.com/journal/10515/aims-and-scope
- https://www.springernature.com/gp/authors/campaigns/latex-author-support
