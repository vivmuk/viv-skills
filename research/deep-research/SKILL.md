---
name: deep-research
description: "Conduct deep multi-source research reports using free academic APIs (PubMed, Wikipedia, arXiv, Semantic Scholar). Covers API selection, search strategy, literature synthesis, and report composition."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Research, Deep Research, PubMed, Literature Review, Report, Academic, Scientific]
    category: research
    related_skills: [arxiv, research-paper-writing]
    requires_toolsets: [terminal, web]
---

# Deep Research Reports

Conduct deep, multi-source research reports on scientific, medical, or technical topics using free APIs. Not just paper search — the full workflow from discovery through synthesis to structured report.

## API Selection Guide

| API | Reliability | Best For | Auth |
|-----|------------|----------|------|
| **PubMed E-Utilities** | ✅ High | Biomedical/life science papers, recent abstracts | None (rate: 3/sec) |
| **Wikipedia REST API** | ✅ High | Foundational knowledge, topic overviews | None |
| **arXiv API** | ⚠️ Moderate (slow) | CS/physics/math preprints | None |
| **Semantic Scholar** | ⚠️ Rate-limited | Citation data, recommendations | Free key recommended |
| **Europe PMC** | ❌ Often empty | — | None |
| **DuckDuckGo HTML** | ❌ Bot-blocked | — | None |

**Primary strategy:** PubMed for literature → Wikipedia for background → arXiv/Semantic Scholar for CS/ML topics.

## Research Workflow

### Phase 1: Foundation (Wikipedia)

Get topic overviews and key terminology before diving into papers.

```bash
# Summary (quick overview)
curl -s "https://en.wikipedia.org/api/rest_v1/page/summary/TOPIC" | python3 -c '
import sys, json
d = json.load(sys.stdin)
print(d.get("extract", "N/A"))
'

# Full article (detailed, for deep topics)
curl -s "https://en.wikipedia.org/w/api.php?action=query&titles=TOPIC&prop=extracts&explaintext=true&format=json" -o /tmp/wiki_TOPIC.json
# Then parse in Python:
# import json; d=json.load(open("/tmp/wiki_TOPIC.json")); [print(p["extract"][:8000]) for p in d["query"]["pages"].values() if "extract" in p]
```

**Tip:** Wikipedia articles reference primary sources. Mine the reference section mentally — those are the papers to find on PubMed.

### Phase 2: Literature Search (PubMed E-Utilities)

Two-step process: **esearch** (get IDs) → **efetch** (get abstracts). See `references/pubmed-eutilities.md` for full details.

```bash
# Step 1: Search — get PubMed IDs
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=YOUR+SEARCH+TERMS&retmax=10&sort=date&retmode=json&datetype=pdat&mindate=2024&maxdate=2026"

# Step 2: Fetch abstracts for those IDs
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=ID1,ID2,ID3&rettype=abstract&retmode=text"
```

**Search strategy:** Run multiple queries with different term combinations to cover different facets. Don't rely on a single search.

### Phase 3: CS/ML Supplement (arXiv + Semantic Scholar)

For computer science, AI, and ML topics, supplement PubMed with the `arxiv` skill and Semantic Scholar (see `arxiv` skill for details).

**Pitfall:** Semantic Scholar rate-limits aggressively (429 errors). Add delays between requests or apply for an API key. Don't rely on it as your primary source.

### Phase 4: Synthesis and Report

1. **Organize by theme** — not by source. Group findings into innovation domains, model categories, application areas, etc.
2. **Lead with the paradigm shift** — What changed? What's the new framing?
3. **Include specific citations** — PMID, arXiv ID, journal, year. Not vague references.
4. **Surface tensions and limitations** — Not just capabilities. Where do the models fail?
5. **Future directions** — What are the key open problems and where is the field heading?

## Report Structure Template

```
# Deep Research: [Topic]

## Executive Summary
[2-3 sentences: what changed, what matters, where it's going]

## 1. Current State / Major Models
[The established players and their capabilities]

## 2. Key Innovations (thematic, not chronological)
[Group by innovation type or application domain]

## 3. Critical Limitations
[What doesn't work, where models fail, known failure modes]

## 4. Future Frontiers
[Where the field is heading in 2-5 years]

## Sources
[PMIDs, arXiv IDs, DOIs, Wikipedia articles consulted]
```

## Pitfalls

- **Don't use delegate_task subagents for literature search.** They produce sparse summaries. Run searches directly via terminal() calls for full control.
- **Don't scrape DuckDuckGo/Google HTML.** Bot detection blocks curl-based scraping. Use proper APIs instead. When general search engines (Google, Bing, DDG) are all CAPTCHA-blocked in the browser, go directly to the source's own search page — e.g., `nvidianews.nvidia.com/search?q=TOPIC`, `blog.company.com/search?q=TOPIC`. Corporate newsrooms and press rooms often have their own search that works without bot detection.
- **Browser clicks not navigating? Use browser_console to extract links.** When a page has cookie banners or overlays that intercept clicks, run `document.querySelector('a[href*="keyword"]')?.href` via browser_console to get the actual URL, then navigate to it directly with browser_navigate.
- **Don't rely on Semantic Scholar without an API key.** You will hit 429 rate limits quickly.
- **PubMed abstracts ≠ full papers.** Abstracts may omit critical details, methodology, and nuance. Note where you only have abstracts.
- **Wikipedia can be outdated.** Check publication dates. For fast-moving fields, Wikipedia may lag 1-2 years.
- **PubMed is biomedical-focused.** For pure CS/physics, prefer arXiv. For cross-disciplinary work, use both.
- **macOS grep is BSD, not GNU.** Don't use `-P` (Perl regex) flag. Use `-E` (extended regex) or pipe through Python instead.
- **curl variable interpolation in execute_code.** Avoid nested quotes in f-strings. Save to file first, then parse in a separate Python step.
- **PubMed batch fetch: split large ID lists.** `efetch` can handle ~20 IDs per request. For larger sets, batch in groups of 15–20 and concatenate results.
- **Wikipedia full article pagination.** Full articles via the `extracts` action can be very long (>30K chars). Read in chunks or use the summary API for overviews and full articles only for deep dives.
- **Clean up credentials after use.** If you write API keys or app passwords to config files (e.g., himalaya config for sending reports via email), always wipe the file contents after the operation completes.

## References

- `references/pubmed-eutilities.md` — Full PubMed E-Utilities API reference: search syntax, field tags, date filtering, batch strategies, and parsing tips

## Related Skills

- `arxiv` — arXiv paper search + Semantic Scholar citation data
- `research-paper-writing` — Full pipeline for writing ML conference papers
