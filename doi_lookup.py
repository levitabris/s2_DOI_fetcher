import os
import argparse
import requests
import bibtexparser
from bibtexparser.bwriter import BibTexWriter

def lookup_dois(bib_file):

    # Load bibtex file
    with open(bib_file) as f:
        bib_database = bibtexparser.load(f)

    # Base API URL
    BASE_URL = 'https://api.semanticscholar.org/graph/v1/paper/'

    # Missing entries
    missing = []
    lookup_length = len(bib_database.entries)

    # Loop through bibtex entries
    for entry in bib_database.entries:
        print('=' * 110)
        if 'doi' not in entry:
            # Check if corpus ID is available
            corpus_id = entry.get('url').split(':')[2]
            if corpus_id:
                print(f'📄{entry.get("title")} \n🔎Fetching DOI... ')
                # Make API request
                url = BASE_URL + f'CorpusId:{corpus_id}?fields=externalIds'
                response = requests.get(url)

                # Extract DOI if present
                data = response.json()

                doi = data['externalIds'].get('DOI')
                arxiv = data['externalIds'].get('ArXiv')
                dblp = data['externalIds'].get('DBLP')

                # Write DOI info if found
                if doi:
                    entry['DOI'] = doi
                    print(f"✅Added DOI: {doi} to {entry['ID']}")
                elif arxiv:
                    entry['ArXiv'] = arxiv
                    print(f"🔄No DOI found for: {entry['ID']}, added ArXiv {arxiv}")
                elif dblp:
                    entry['DBLP'] = dblp
                    print(f"🔄No ArXiv found for: {entry['ID']}, added DBLP {dblp}")
                else:
                    missing += [entry.get('title')]
                    print(f"❌No DOI found for: {entry['ID']}")

    print('=' * 110)
    print(f'Found [{lookup_length - len(missing)} / {lookup_length}] DOIs\nMissing ones are:')
    print(''.join(['\n❓' + title for title in missing]))

    # Write out modified bibtex
    writer = BibTexWriter()

    name = os.path.splitext(bib_file)[0]
    with open(f'{name}_modified.bib', 'w') as outfile:
        bibtexparser.dump(bib_database, outfile, writer)

if  __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('bibfile', help='Bibtex file')
    args = parser.parse_args()

    lookup_dois(args.bibfile)
