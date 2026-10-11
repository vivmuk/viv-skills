# Venice Augment REST API — Direct HTTP Endpoints

These endpoints are used by the MCP server under the hood but are also
callable directly via HTTP. Essential when integrating Venice web
search/scrape into a Python codebase (httpx, requests) without the MCP
server as a dependency.

## Base URL

```
https://api.venice.ai/api/v1
```

## Authentication

```
Authorization: Bearer <VENICE_API_KEY>
Content-Type: application/json
```

## POST /augment/search

Web search powered by Firecrawl. Returns structured results with titles,
URLs, and content excerpts.

**Request body:**
```json
{
  "query": "Naval Ravikant podcast interviews frameworks principles",
  "limit": 10
}
```

**Response shape:**
```json
{
  "query": "...",
  "results": [
    {
      "url": "https://example.com/article",
      "title": "Article Title",
      "content": "Full excerpt text with <strong>HTML</strong> tags...",
      "date": ""
    }
  ]
}
```

**Notes:**
- `content` may contain HTML tags (e.g., `<strong>`)
- `date` is often empty string
- Results are summaries/excerpts, not full page content
- The MCP server's `venice_web_search` tool calls this endpoint

## POST /augment/scrape

Scrape a URL and return its content as markdown or HTML.

**Request body:**
```json
{
  "url": "https://en.wikipedia.org/wiki/Naval_Ravikant",
  "format": "markdown"
}
```

**Response shape:**
```json
{
  "url": "https://en.wikipedia.org/wiki/Naval_Ravikant",
  "content": "# Article Title\n\nFull markdown content...",
  "format": "markdown"
}
```

**Notes:**
- `format` can be `"markdown"` or `"html"`
- Some URLs fail with `{"error": "Could not resolve hostname"}` — not all
  domains are reachable through Venice's scraper
- Wikipedia and major sites work reliably
- The MCP server's `venice_web_scrape` tool calls this endpoint

## POST /augment/text-parser

Extract text from documents (PDF, DOCX, EPUB, PPTX, XLSX) via URL.

**Request:** multipart form upload (not JSON).

The MCP server's `venice_text_parser` tool calls this endpoint.

## Discovery Technique

The REST endpoints are NOT documented in Venice's public API docs as of
2026-05. To find them, unpack the MCP server npm package:

```bash
npm pack @veniceai/mcp-server@0.2.0 --pack-destination /tmp
cd /tmp && tar xzf veniceai-mcp-server-*.tgz
grep -r "augment" /tmp/package/dist/tools/
```

This reveals the `/v1/augment/search`, `/v1/augment/scrape`, and
`/v1/augment/text-parser` paths.
