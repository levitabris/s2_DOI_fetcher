# What is it?
The default bibtex exports from Semantic Scholar(S2) libraries do not include DOIs, which is problematic for some. This simple CLI app scratches that itch for you. It creates a new bibtex file with the missing DOIs. You may find it useful to ask Zotero SciHub plugin to fetch PDFs or find citation counts (with other plugins).

<img width="1105" alt="image" src="https://github.com/levitabris/s2_DOI_fetcher/assets/1910117/35a100ad-5307-4142-a6fb-e96cb2bd8049">

# How to use?

1. Prepare the environment
   ```
   uv sync
   source .venv/bin/activate
   ```
   Use `source .venv/bin/activate.fish` if you are using fish shell. Same applies to other shells.

2. Run in CLI
   ```
   uv run doi_lookup.py my_semantic_scholar_exported.bib
   ```
3. Check the results.

# How does it work?

We basically use the official S2 API to fetch full information with the S2-assigned `CorpusId` number. The basic lookup quota is pretty generous and should suffice most library sizes.
