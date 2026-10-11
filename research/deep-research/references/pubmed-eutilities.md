# PubMed E-Utilities API Reference

Free, no-auth API for searching and retrieving biomedical literature from NCBI. Most reliable free academic search API as of 2026.

## Rate Limits
- 3 requests/second without API key
- 10 requests/second with API key (free: register at https://www.ncbi.nlm.nih.gov/account/settings/)
- Add `api_key=YOUR_KEY` parameter to requests

## Two-Step Workflow

### Step 1: esearch — Get PubMed IDs

```
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=QUERY&retmax=N&sort=date&retmode=json
```

**Key parameters:**
- `db=pubmed` — always use pubmed
- `term=QUERY` — search terms, + separated (e.g., `protein+folding+deep+learning`)
- `retmax=N` — max results to return (default 20, max 100000)
- `sort=date` — sort by publication date
- `retmode=json` — return JSON (vs XML default)
- `datetype=pdat` — date type to filter on
- `mindate=YYYY` / `maxdate=YYYY` — date range filter
- `retstart=N` — offset for pagination

**Returns:** JSON with `esearchresult.idlist` — array of PubMed IDs

### Step 2: efetch — Get Abstracts/Metadata

```
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=ID1,ID2,...&rettype=abstract&retmode=text
```

**Key parameters:**
- `id=ID1,ID2,...` — comma-separated PubMed IDs (up to 200 per request)
- `rettype=abstract` — full abstract with journal, authors, DOI
- `retmode=text` — human-readable text (vs XML)
- `rettype=medline` — MEDLINE format (more structured, good for parsing)
- `rettype=full` — full text (only available for open-access articles in PMC)

**Returns:** Plain text with structured abstract sections

### Step 3 (optional): elink — Find Related Articles

```
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi?dbfrom=pubmed&db=pubmed&id=PMID&retmode=json
```

## Search Term Syntax

| Operator | Example | Meaning |
|----------|---------|---------|
| + (space) | `protein+folding` | AND (all terms required) |
| OR | `protein+OR+peptide` | Either term |
| NOT | `cancer+NOT+breast` | Exclude |
| Quotes | `"deep+learning"` | Exact phrase |
| [field] | `smith[au]` | Author field |
| [field] | `nature[journal]` | Journal field |
| [field] | `2024:2026[dp]` | Date published range |
| [field] | `review[pt]` | Publication type (review) |
| [field] | `english[la]` | Language |

### Common Field Tags
- `[au]` — Author
- `[ti]` — Title
- `[tiab]` — Title + Abstract
- `[journal]` — Journal name
- `[dp]` — Date published
- `[pt]` — Publication type
- `[la]` — Language
- `[mh]` — MeSH term (controlled vocabulary)
- `[ot]` — Other term (author keywords)

### Date Filtering

```bash
# Papers from 2024-2026
&datetype=pdat&mindate=2024&maxdate=2026

# Papers from last 2 years
&datetype=pdat&mindate=2024&maxdate=2026
```

## Practical Examples

### Search by topic with date filter
```bash
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=AlphaFold+drug+discovery&retmax=10&sort=date&retmode=json&datetype=pdat&mindate=2024&maxdate=2026"
```

### Fetch multiple abstracts
```bash
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=42129084,42123499,42103936&rettype=abstract&retmode=text"
```

### Search for reviews only
```bash
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=protein+folding+deep+learning+review[pt]&retmax=10&sort=date&retmode=json"
```

### Paginate through results
```bash
# First page
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=TOPIC&retmax=20&retstart=0&retmode=json"

# Second page
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=TOPIC&retmax=20&retstart=20&retmode=json"
```

## Parsing Tips

- efetch with `retmode=text` returns structured plain text. Journal, title, authors, and abstract are clearly delineated.
- For programmatic parsing, use `retmode=xml` and parse with Python's `xml.etree.ElementTree`.
- PMID is always shown at the end as `PMID: 12345678 [Indexed for MEDLINE]`.
- DOI is shown as `DOI: 10.xxxx/...`.
- PMCID (PubMed Central ID for open-access full text) shown as `PMCID: PMC1234567`.

## Batch Strategy for Deep Research

1. Run 5-8 different search queries covering different facets of the topic
2. Collect all unique PMIDs (deduplicate)
3. Fetch abstracts in batches of up to 200 IDs per efetch call
4. Parse and synthesize

This gives comprehensive coverage without relying on a single search formulation.
