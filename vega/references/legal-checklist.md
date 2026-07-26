# Legal Protection Checklist

The moment you collect user data, you are in legal territory. This is not optional. The cheapest 10 minutes of work you will do all year.

## Privacy Policy

- [ ] A real privacy policy exists, even if generated. Use Termly (termly.io) or PrivacyPolicies.com — both free, under 5 minutes.
- [ ] Privacy policy is linked in the app footer or settings page.
- [ ] Privacy policy states: what data is collected, how it is used, where it is stored, whether it is shared, how users can request deletion.

## Data Location

- [ ] You know exactly where user data lives:
  - Supabase region (e.g., us-east-1, eu-west-1)
  - Vercel region for serverless functions
  - Any third-party services touching the data (OpenAI, Stripe, Resend)
- [ ] If serving EU users: data is stored in EU regions, or you have a valid data transfer mechanism (SCCs, adequacy decision).
- [ ] If subject to CCPA (California users): you support right to know, right to delete, and right to opt-out of sale.

## Data Handling

- [ ] No selling user data to third parties.
- [ ] No exporting user data to personal email or personal accounts.
- [ ] No plaintext password storage. Use bcrypt, argon2, or your auth provider's built-in hashing.
- [ ] No keeping user data longer than necessary. Implement deletion flows.

## 2026 AI Copyright & Licensing Risks

The legal ground under AI-built apps shifted significantly in 2026. Most builders have not caught up.

### AI-Generated Code and Copyright

- The US Supreme Court let the human-authorship ruling stand. Code written purely by AI cannot be copyrighted in the US.
- If a competitor clones your AI-built app line for line, you may have no legal ground to stop them.
- **Mitigation:** Document human contributions. Have a developer review, modify, and commit AI-generated code with human-authored changes. The human-authored portions are copyrightable.

### GPL Contamination

- If your AI coding tool pulls in open-source code under a copyleft license (GPL, AGPL), you can be forced to open-source your entire codebase or face an infringement claim.
- You get all of the liability and none of the protection.
- **Mitigation:** Run a license scan before launch. Use `license-checker` (npm) or `pip-licenses` (Python). Flag any GPL/AGPL dependencies and replace them with permissive alternatives (MIT, Apache 2.0, BSD) where possible.

### AI Copyright Case Precedent

- The biggest AI copyright case to date ended in a $1.5 billion settlement with final court approval in 2026.
- The lawyers are already here. They are not coming — they are present.
- **Mitigation:** Do not train on copyrighted data without permission. Do not use AI to reproduce copyrighted code, text, or media. Keep records of your training data sources if you fine-tune models.

### Cease and Desist Risk

- Vibe coders have received cease and desist letters for:
  - Using copyrighted names, logos, or branding in their apps
  - Scraping data from third-party platforms without permission
  - Reproducing copyrighted content in AI-generated outputs
  - Violating platform terms of service (e.g., automated scraping of social platforms)
- **Mitigation:** Do not use trademarked names or logos without permission. Read and comply with platform ToS. Do not scrape without checking `robots.txt` and ToS.

## Platform Terms of Service

- [ ] Review the ToS of every platform you integrate with (OpenAI, Stripe, Supabase, Vercel, Google, Apple App Store, Google Play).
- [ ] Do not scrape platforms that prohibit scraping in their ToS.
- [ ] Do not use trademarked names in your app name or domain without permission.
- [ ] If using AI-generated content, ensure your AI provider's ToS allows your use case.

## Indemnification

- [ ] If you are building for a client, your contract should include:
  - Indemnification for IP infringement claims
  - Limitation of liability
  - Warranty disclaimers
  - Data breach notification requirements
- [ ] If building for yourself, consider forming an LLC to limit personal liability.

## What This Is Not

This checklist is not legal advice. It is a baseline for vibe coders and indie builders. If you are storing health data, financial data, or anything regulated, or if you have significant revenue or users, consult a lawyer who understands technology law.
