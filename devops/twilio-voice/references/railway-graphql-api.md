# Railway GraphQL API — Environment Variable Management

When the Railway CLI doesn't work (project-scoped tokens fail `railway login`), you can still manage environment variables through the GraphQL API at `https://backboard.railway.app/graphql/v2`.

## Authentication

Project-scoped tokens (like `892faa4f-...`) work for GraphQL reads AND mutations, despite failing CLI auth (`railway whoami`, `railway link`, `railway variables`). Use the token as a Bearer token:

```bash
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Authorization: Bearer <RAILWAY_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"query": "..."}'
```

## List Project IDs and Environment Variables

```graphql
{
  project(id: "195c354e-1b7c-41f9-9823-463a2fd34eaa") {
    name
    environments {
      edges {
        node {
          id
          name
          variables
        }
      }
    }
    services {
      edges {
        node {
          id
          name
          variables
        }
      }
    }
  }
}
```

Run via curl:
```bash
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ project(id: \"195c354e-1b7c-41f9-9823-463a2fd34eaa\") { name environments { edges { node { id name variables } } } services { edges { node { id name variables } } } } }"}'
```

## Update Environment Variables (variableUpsert)

The mutation requires all 5 fields: `projectId`, `environmentId`, `serviceId`, `name`, and `value`.

```graphql
mutation {
  variableUpsert(input: {
    projectId: "195c354e-1b7c-41f9-9823-463a2fd34eaa"
    environmentId: "98f0d4e2-2799-49e3-b390-4ab93c524f32"
    serviceId: "91da60db-fb63-4dcb-b140-eeb8b30b70c2"
    name: "CHAT_MODEL"
    value: "qwen3-5-9b"
  })
}
```

Run via curl:
```bash
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "mutation { variableUpsert(input: { projectId: \"195c354e-1b7c-41f9-9823-463a2fd34eaa\", environmentId: \"98f0d4e2-2799-49e3-b390-4ab93c524f32\", serviceId: \"91da60db-fb63-4dcb-b140-eeb8b30b70c2\", name: \"CHAT_MODEL\", value: \"qwen3-5-9b\" }) }"}'
```

**Important:** Changing env vars via `variableUpsert` automatically triggers a redeploy. Wait ~60s, then verify via the app's status endpoint (e.g., `curl https://voice.example.com/`).

## Batch Update Multiple Variables

Run separate mutations for each variable. Each one triggers a deploy — to avoid multiple deploys, batch them quickly or accept that the last one wins (Railway may batch them into a single deploy if they arrive within seconds).

```bash
# Update CHAT_MODEL
curl -s -X POST ... -d '{"query": "mutation { variableUpsert(input: { ... name: \"CHAT_MODEL\", value: \"qwen3-5-9b\" }) }"}'

# Update TTS_MODEL  
curl -s -X POST ... -d '{"query": "mutation { variableUpsert(input: { ... name: \"TTS_MODEL\", value: \"tts-kokoro\" }) }"}'

# Update TTS_VOICE
curl -s -X POST ... -d '{"query": "mutation { variableUpsert(input: { ... name: \"TTS_VOICE\", value: \"af_sarah\" }) }"}'
```

## Verify Deployment Status

```graphql
{
  service(id: "91da60db-fb63-4dcb-b140-eeb8b30b70c2") {
    deployments {
      edges {
        node {
          id
          status
          createdAt
        }
      }
    }
  }
}
```

Look for the latest deployment with `status: "SUCCESS"`.

## Hermes Voice Project Details

- **Project ID**: `195c354e-1b7c-41f9-9823-463a2fd34eaa`
- **Environment ID**: `98f0d4e2-2799-49e3-b390-4ab93c524f32` (production)
- **Service ID**: `91da60db-fb63-4dcb-b140-eeb8b30b70c2` (hermes-voice)
- **Domain**: `voice.genaichutney.com`
- **Status endpoint**: `GET https://voice.genaichutney.com/` — returns JSON with `chat_model`, `tts_model`, `tts_voice`

## Common Issue: Account Token Fails Too

Both project-scoped AND account-level tokens from `.env` files may be expired/revoked. If both fail:
1. Generate a new token at `railway.app/account/tokens` (requires browser login)
2. Or push code changes to GitHub — Railway auto-deploys from the connected repo
3. Code defaults in `main.py` are overridden by Railway env vars, so if you can't change env vars, you MUST push code AND clear the env vars (or the env vars will still override)