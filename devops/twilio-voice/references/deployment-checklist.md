# Full Deployment Checklist: Twilio Voice Bot on Railway + Cloudflare

## Overview

Complete walkthrough for deploying the Hermes Voice bot to Railway with a custom domain via Cloudflare DNS. This covers everything from Railway custom domain creation to DNS automation to Twilio webhook configuration.

## Prerequisites

- Railway account with an API token (project-scoped works for GraphQL, account-level for CLI)
- Cloudflare account with API token (permissions: `dns_records:edit`, `dns_records:read`, `zone:read`)
- Twilio account SID, auth token, and phone number
- Venice AI API key
- Domain managed by Cloudflare (e.g., `genaichutney.com`)

## Step-by-Step

### 1. Create Custom Domain on Railway

Use the GraphQL API (`https://backboard.railway.app/graphql/v2`):

```bash
mutation {
  customDomainCreate(input: {
    environmentId: "ENV_ID",
    projectId: "PROJECT_ID",
    serviceId: "SERVICE_ID",
    domain: "voice.example.com"
  }) { ... on CustomDomain { id domain } }
}
```

Returns: `{ "data": { "customDomainCreate": { "id": "DOMAIN_ID", "domain": "voice.example.com" } } }`

### 2. Query Required DNS Records

```bash
{
  customDomain(id: "DOMAIN_ID", projectId: "PROJECT_ID") {
    id domain
    status {
      verified
      certificateStatus
      dnsRecords {
        fqdn hostlabel purpose recordType requiredValue currentValue status zone
      }
      verificationDnsHost verificationToken
    }
  }
}
```

This returns:
- **CNAME record**: `voice` → `qcfbi9ai.up.railway.app` (purpose: `DNS_RECORD_PURPOSE_TRAFFIC_ROUTE`)
- **TXT record**: `_railway-verify.voice` → `railway-verify=<token>` (for domain ownership verification)

### 3. Configure Cloudflare DNS (API)

Get the zone ID first:

```bash
curl -s "https://api.cloudflare.com/client/v4/zones?name=example.com" \
  -H "Authorization: Bearer CF_API_TOKEN"
```

#### Create or Update CNAME Record

If the subdomain doesn't exist yet:

```bash
curl -X POST "https://api.cloudflare.com/client/v4/zones/ZONE_ID/dns_records" \
  -H "Authorization: Bearer CF_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type":"CNAME","name":"voice","content":"qcfbi9ai.up.railway.app","proxied":false,"ttl":1}'
```

If it already exists (e.g., was pointing to a Cloudflare Tunnel), PATCH it:

```bash
curl -X PATCH "https://api.cloudflare.com/client/v4/zones/ZONE_ID/dns_records/RECORD_ID" \
  -H "Authorization: Bearer CF_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"qcfbi9ai.up.railway.app","proxied":false}'
```

**Important:** Set `proxied: false` (DNS-only / grey cloud) initially. Railway needs to validate the domain directly. You can enable Cloudflare proxy (orange cloud) after SSL cert is provisioned.

#### Create TXT Verification Record

```bash
curl -X POST "https://api.cloudflare.com/client/v4/zones/ZONE_ID/dns_records" \
  -H "Authorization: Bearer CF_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type":"TXT","name":"_railway-verify.voice","content":"railway-verify=TOKEN","ttl":1}'
```

### 4. Wait for Domain Verification

Poll the Railway custom domain status:

```
certificateStatus: CERTIFICATE_STATUS_TYPE_VALIDATING_OWNERSHIP  →  still provisioning
certificateStatus: CERTIFICATE_STATUS_TYPE_VALID  →  done!
verified: true  →  domain ownership confirmed
```

DNS propagation through Cloudflare is typically fast (1-5 minutes). Use Cloudflare's DNS-over-HTTPS to check:

```bash
curl -s "https://1.1.1.1/dns-query?name=voice.example.com&type=CNAME" -H "Accept: application/dns-json"
```

### 5. Set BASE_URL on Railway

```bash
mutation { variableUpsert(input: {
  projectId: "PROJECT_ID",
  environmentId: "ENV_ID",
  serviceId: "SERVICE_ID",
  name: "BASE_URL",
  value: "https://voice.example.com"
}) }
```

### 6. Redeploy

```bash
mutation { deploymentRestart(id: "DEPLOYMENT_ID") }
```

Or push a new commit to trigger auto-deploy.

### 7. Configure Twilio Webhook

```python
from twilio.rest import Client

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
numbers = client.incoming_phone_numbers.list(phone_number='+1XXXXXXXXXX')
numbers[0].update(
    voice_url='https://voice.example.com/voice',
    voice_method='POST'
)
```

### 8. Verify End-to-End

```bash
# Health check
curl https://voice.example.com/

# Voice webhook test (allowed caller)
curl -X POST https://voice.example.com/voice -d "From=%2B1XXXXXXXXXX&CallSid=test123"

# Should return TwiML with <Gather> and <Say>
```

## Common Issues

| Issue | Fix |
|-------|-----|
| Railway domain returns 404 "Application not found" | No public domain set up. Must add custom domain via API or CLI. |
| Cloudflare CNAME already exists | Use PATCH instead of POST to update the existing record. |
| `certificateStatus` stuck at `VALIDATING_OWNERSHIP` | TXT record may not have propagated yet. Check with `dig _railway-verify.voice.example.com TXT`. |
| Twilio can't reach webhook URL | Ensure `proxied: false` on Cloudflare (grey cloud), or that SSL certificate is `VALID`. |
| Audio files not playing on calls | `BASE_URL` env var must be set to `https://voice.example.com` (no trailing slash). |

## GraphQL Schema Introspection Tip

The Railway GraphQL schema is undocumented. When queries fail, introspect:

```bash
curl -s -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" \
  -X POST https://backboard.railway.app/graphql/v2 \
  -d '{"query":"{ __type(name: \"CustomDomainStatus\") { fields { name type { name kind ofType { name } } } } }"}'
```

Key types to introspect when working with custom domains: `CustomDomainCreateInput`, `CustomDomainStatus`, `DNSRecords`, `CertificateStatus`.