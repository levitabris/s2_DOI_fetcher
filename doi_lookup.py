import os
import time
import argparse
import requests
import bibtexparser
from bibtexparser.bwriter import BibTexWriter
from typing import List, Dict, Any

class DOIBatchFetcher:
    """Batch fetcher for DOIs from Semantic Scholar API"""

    BASE_URL = 'https://api.semanticscholar.org/graph/v1/paper/batch'
    SINGLE_URL = 'https://api.semanticscholar.org/graph/v1/paper/'
    BATCH_SIZE = 500  # Semantic Scholar allows up to 500 papers per batch
    RATE_LIMIT_DELAY = 3  # Delay in seconds when rate limited

    def __init__(self, bib_file: str):
        self.bib_file = bib_file
        self.bib_database = None
        self.missing = []

    def load_bibtex(self):
        """Load the bibtex file"""
        with open(self.bib_file) as f:
            self.bib_database = bibtexparser.load(f)

    def extract_corpus_ids(self) -> Dict[str, Dict[str, Any]]:
        """Extract corpus IDs from entries that don't have DOIs"""
        corpus_map = {}

        for entry in self.bib_database.entries:
            if 'doi' not in entry and 'DOI' not in entry:
                url = entry.get('url', '')
                if url and 'CorpusID:' in url:
                    try:
                        corpus_id = url.split('CorpusID:')[1].split('/')[0].split('?')[0]
                        corpus_map[f"CorpusID:{corpus_id}"] = entry
                    except (IndexError, AttributeError):
                        print(f"⚠️ Could not extract corpus ID from: {entry.get('ID', 'unknown')}")

        return corpus_map

    def batch_fetch(self, corpus_ids: List[str]) -> Dict[str, Any]:
        """Fetch paper data in batches"""
        all_results = {}

        # Process in batches
        for i in range(0, len(corpus_ids), self.BATCH_SIZE):
            batch = corpus_ids[i:i + self.BATCH_SIZE]
            batch_num = i // self.BATCH_SIZE + 1
            total_batches = (len(corpus_ids) + self.BATCH_SIZE - 1) // self.BATCH_SIZE

            print(f"📦 Fetching batch {batch_num}/{total_batches} ({len(batch)} papers)...")

            # Prepare batch request
            params = {
                'fields': 'externalIds,title'
            }

            # Make batch request
            response = self.make_request_with_retry(batch, params)

            if response:
                # Map results back to corpus IDs
                for j, paper_data in enumerate(response):
                    if paper_data:  # Check if data exists
                        all_results[batch[j]] = paper_data

            # Small delay between batches to be respectful
            if i + self.BATCH_SIZE < len(corpus_ids):
                time.sleep(0.5)

        return all_results

    def make_request_with_retry(self, batch: List[str], params: Dict) -> List[Dict]:
        """Make API request with retry logic for rate limiting"""
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                response = requests.post(
                    self.BASE_URL,
                    json={"ids": batch},
                    params=params,
                    headers={'Content-Type': 'application/json'}
                )

                if response.status_code == 429:
                    # Rate limited
                    retry_after = int(response.headers.get('Retry-After', self.RATE_LIMIT_DELAY))
                    print(f"⏳ Rate limited. Waiting {retry_after} seconds...")
                    time.sleep(retry_after)
                    retry_count += 1
                    continue

                elif response.status_code == 200:
                    return response.json()

                else:
                    print(f"❌ Error {response.status_code}: {response.text}")
                    return None

            except requests.exceptions.RequestException as e:
                print(f"❌ Request error: {e}")
                retry_count += 1
                if retry_count < max_retries:
                    time.sleep(self.RATE_LIMIT_DELAY)

        return None

    def update_entries(self, corpus_map: Dict[str, Dict], results: Dict[str, Any]):
        """Update bibtex entries with fetched DOIs"""
        updated_count = 0
        doi_count = 0
        arxiv_count = 0
        dblp_count = 0

        for corpus_id, entry in corpus_map.items():
            if corpus_id in results:
                paper_data = results[corpus_id]
                external_ids = paper_data.get('externalIds', {})

                doi = external_ids.get('DOI')
                arxiv = external_ids.get('ArXiv')
                dblp = external_ids.get('DBLP')

                if doi:
                    entry['DOI'] = doi
                    doi_count += 1
                    updated_count += 1
                    print(f"✅ Added DOI: {doi} to {entry['ID']}")
                elif arxiv:
                    entry['ArXiv'] = arxiv
                    arxiv_count += 1
                    updated_count += 1
                    print(f"🔄 No DOI found for: {entry['ID']}, added ArXiv: {arxiv}")
                elif dblp:
                    entry['DBLP'] = dblp
                    dblp_count += 1
                    updated_count += 1
                    print(f"🔄 No DOI/ArXiv found for: {entry['ID']}, added DBLP: {dblp}")
                else:
                    self.missing.append(entry.get('title', entry.get('ID', 'unknown')))
                    print(f"❌ No identifiers found for: {entry['ID']}")
            else:
                self.missing.append(entry.get('title', entry.get('ID', 'unknown')))
                print(f"❌ No data returned for: {entry['ID']}")

        return updated_count, doi_count, arxiv_count, dblp_count

    def save_modified_bibtex(self):
        """Save the modified bibtex file"""
        writer = BibTexWriter()
        name = os.path.splitext(self.bib_file)[0]
        output_file = f'{name}_modified.bib'

        with open(output_file, 'w') as outfile:
            bibtexparser.dump(self.bib_database, outfile, writer)

        return output_file

    def run(self):
        """Main execution method"""
        print("=" * 110)
        print(f"📚 Processing: {self.bib_file}")
        print("=" * 110)

        # Load bibtex file
        self.load_bibtex()
        total_entries = len(self.bib_database.entries)
        print(f"📖 Loaded {total_entries} entries from bibtex file")

        # Extract corpus IDs for entries without DOIs
        corpus_map = self.extract_corpus_ids()

        if not corpus_map:
            print("✅ All entries already have DOIs or no corpus IDs found!")
            return

        print(f"🔍 Found {len(corpus_map)} entries without DOIs")
        print("=" * 110)

        # Fetch in batches
        corpus_ids = list(corpus_map.keys())
        results = self.batch_fetch(corpus_ids)

        print("=" * 110)
        print("📝 Updating entries...")
        print("=" * 110)

        # Update entries with results
        updated, doi_count, arxiv_count, dblp_count = self.update_entries(corpus_map, results)

        # Save modified bibtex
        output_file = self.save_modified_bibtex()

        # Print summary
        print("=" * 110)
        print("📊 Summary:")
        print(f"  • Total entries processed: {len(corpus_map)}")
        print(f"  • Successfully updated: {updated}")
        print(f"    - DOIs added: {doi_count}")
        print(f"    - ArXiv IDs added: {arxiv_count}")
        print(f"    - DBLP IDs added: {dblp_count}")
        print(f"  • Missing identifiers: {len(self.missing)}")

        if self.missing:
            print("\n❓ Entries with missing identifiers:")
            for title in self.missing[:10]:  # Show first 10
                print(f"  • {title}")
            if len(self.missing) > 10:
                print(f"  ... and {len(self.missing) - 10} more")

        print(f"\n💾 Modified bibtex saved to: {output_file}")
        print("=" * 110)


def main():
    parser = argparse.ArgumentParser(
        description='Batch fetch DOIs for papers in a BibTeX file using Semantic Scholar API'
    )
    parser.add_argument('bibfile', help='Path to the BibTeX file')
    parser.add_argument(
        '--batch-size',
        type=int,
        default=500,
        help='Number of papers to fetch per batch (max 500, default 500)'
    )
    args = parser.parse_args()

    # Validate batch size
    if args.batch_size > 500:
        print("⚠️ Batch size exceeds maximum (500), using 500")
        DOIBatchFetcher.BATCH_SIZE = 500
    else:
        DOIBatchFetcher.BATCH_SIZE = args.batch_size

    # Run the fetcher
    fetcher = DOIBatchFetcher(args.bibfile)
    fetcher.run()


if __name__ == '__main__':
    main()
