# What is it?
The default bibtex exports from Semantic Scholar(S2) libraries do not include DOIs, which is problematic for some. This simple CLI app scratches that itch for you. It creates a new bibtex file with the missing DOIs. You may find it useful to ask Zotero SciHub plugin to fetch PDFs or find citation counts (with other plugins).


# How to use?

1. Install the deps
   ```
   pip install -r requirements.txt
   ```
2. Run in CLI
   ```
   python doi_lookup.py my_semantic_scholar_exported.bib
   ```
3. Check the results.

# How does it work?

We basically use the official S2 API to fetch full information with S2-assigned `CorpusId` number. The basic lookup quota is pretty generous and shoud suffice most library sizes.
