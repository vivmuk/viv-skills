# Cloudflare DNS + Railway Custom Domain Setup

## Context

When deploying a Twilio voice bot on Railway's hobby plan, Railway does NOT auto-assign a `.up.railway.app` domain. You must create a custom domain and configure DNS via Cloudflare (or another provider). This reference covers the full automation flow via APIs.

## Prerequisites

- Railway API token (project-scoped works for GraphQL mutations)
- Cloudflare API token with permissions: `dns_records:edit`, `dns_records:read`, `zone:read`
- Domain already managed by Cloudflare

## Full Automation Flow

### 1. Create Custom Domain on Railway

```bash
mutation {
  customDomainCreate(input: {
    environmentId: "ENV_ID"
    projectId: "PROJECT_ID"
    serviceId: "SERVICE_ID"
    domain: "voice.example.com"
  }) { ... on CustomDomain { id domain } }
}
```

### 2. Query Required DNS Records

```
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

Returns:
- **CNAME**: `voice` → `<hash>.up.railway.app` (purpose: `DNS_RECORD_PURPOSE_TRAFFIC_ROUTE`)
- **TXT**: `_railway-verify.voice` → `railway-verify=<token>` (ownership verification)

### 3. Configure Cloudflare DNS via API

Get zone ID first:
```bash
curl -s "https://api.cloudflare.com/client/v4/zones?name=example.com" \
  -H "Authorization: Bearer CF_TOKEN" | python3 -m json.tool
```

Create or update CNAME (if existing, use PATCH with the record ID):
```bash
# Create new
curl -X POST "https://api.cloudflare.com/client/v4/zones/ZONE_ID/dns_records" \
  -H "Authorization: Bearer CF_TOKEN" -H "Content-Type: application/json" \
  -d '{"type":"CNAME","name":"voice","content":"<hash>.up.railway.app","proxied":false,"ttl":1}'

# Update existing (PATCH)
curl -X PATCH "https://api.cloudflare.com/client/v4/zones/ZONE_ID/dns_records/RECORD_ID" \
  -H "Authorization: Bearer CF_TOKEN" -H "Content-Type: application/json" \
  -d '{"content":"<hash>.up.railway.app","proxied":false}'
```

Create TXT verification record:
```bash
curl -X POST "https://api.cloudflare.com/client/v4/zones/ZONE_ID/dns_records" \
  -H "Authorization: Bearer CF_TOKEN" -H "Content-Type: application/json" \
  -d '{"type":"TXT","name":"_railway-verify.voice","content":"railway-verify=TOKEN","ttl":1}'
```

**Critical:** Set `proxied: false` (DNS-only / grey cloud) initially. Railway validates domain ownership directly. Enable Cloudflare proxy (orange cloud) only after SSL cert is provisioned.

### 4. Wait for Verification

Poll Railway status:
- `certificateStatus: CERTIFICATE_STATUS_TYPE_VALIDATING_OWNERSHIP` → still provisioning
- `certificateStatus: CERTIFICATE_STATUS_TYPE_VALID` → done
- `verified: true` → domain ownership confirmed

Check DNS propagation via Cloudflare DoH:
```bash
curl -s "https://1.1.1.1/dns-query?name=voice.example.com&type=CNAME" -H "Accept: application/dns-json"
```

### 5. Set BASE_URL and Redeploy

```bash
# Set env var
mutation { variableUpsert(input: {
  projectId: "PROJECT_ID", environmentId: "ENV_ID", serviceId: "SERVICE_ID",
  name: "BASE_URL", value: "https://voice.example.com"
}) }

# Redeploy (or push a new commit)
mutation { deploymentRestart(id: "DEPLOYMENT_ID") }
```

### 6. Configure Twilio Webhook

```python
from twilio.rest import Client
client = Client(ACCOUNT_SID, AUTH_TOKEN)
numbers = client.incoming_phone_numbers.list(phone_number='+1XXXXXXXXXX')
numbers[0].update(voice_url='https://voice.example.com/voice', voice_method='POST')
```

## Introspecting the Railway GraphQL Schema

The Railway GraphQL API is undocumented. When queries fail, introspect:

```bash
curl -s -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" \
  -X POST https://backboard.railway.app/graphql/v2 \
  -d '{"query":"{ __type(name: \"CustomDomainStatus\") { fields { name type { name kind ofType { name } } } } }"}'
```

Key types: `CustomDomainCreateInput`, `CustomDomainStatus`, `DNSRecords`, `CertificateStatus`, `DNSRecordType`, `DNSRecordPurpose`

## Common Issues

| Issue | Fix |
|-------|-----|
| Railway returns 404 "Application not found" (JSON) | No public domain configured. Must add custom domain or run `railway domain`. |
| Cloudflare CNAME already exists | Use PATCH instead of POST to update the existing record. |
| `certificateStatus` stuck at `VALIDATING_OWNERSHIP` | TXT verification record not propagated yet. Check with DoH query. |
| Twilio can't reach webhook URL | Ensure `proxied: false` on Cloudflare, or SSL cert is `VALID`. |
| `deployment.url` returns `null` in GraphQL API | Normal for hobby plan — Railway doesn't assign URLs without a custom domain or explicit `railway domain` command. |