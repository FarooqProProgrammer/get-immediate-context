# Privacy, Secrets Redaction, and Compliance Reference

## 1. Threat Model & Overview

When AI coding agents read repositories and generate persistent briefs or memory ledgers, there is a risk of inadvertently ingesting and storing:
1. Hardcoded API keys, database credentials, and personal access tokens.
2. Proprietary business notes or developer scratchpads containing uncommitted secrets.
3. Personal review notes that should not be shared across teams.

---

## 2. Privacy Mechanisms

### 1. Tag-Based Exclusion (`<private>...</private>`)
Developers or agents can wrap any sensitive code comments, notes, or configuration blocks with `<private>` markers:

```python
# <private>
# DB_PASSWORD = "staging-internal-pass-xyz"
# Internal admin portal: https://admin.internal.corp
# </private>
```

The privacy filter uses regular expression matching to strip all `<private>...</private>` blocks completely:
```python
PRIVATE_TAG_REGEX = re.compile(r"<private>[\s\S]*?</private>", re.IGNORECASE)
sanitized = PRIVATE_TAG_REGEX.sub("[REDACTED: PRIVATE BLOCK]", text)
```

---

### 2. Automatic Secret Pattern Redaction
The engine automatically detects and replaces common high-risk credential patterns:

| Pattern Type | Detection Regex | Redacted Output |
|---|---|---|
| Generic Key / Token | `(?i)(api[_-]?key\|secret\|password\|token\|bearer)\s*[:=]\s*['"]?[a-zA-Z0-9_\-\.]{8,}['"]?` | `\1: [REDACTED_SECRET]` |
| Stripe Live/Test Keys | `sk_[live\|test]_[0-9a-zA-Z]{24,}` | `[REDACTED_SECRET]` |
| GitHub Personal Tokens | `ghp_[0-9a-zA-Z]{36}` | `[REDACTED_SECRET]` |
| Private Key Headers | `-----BEGIN (RSA\|OPENSSH\|EC\|PRIVATE) KEY-----` | File ignored |

---

### 3. File-Level Exclusions
The following file patterns are strictly excluded from memory ingestion and embeddings:
- `.env*` (including `.env.local`, `.env.production`)
- `*.pem`, `*.key`, `id_rsa`, `id_ed25519`
- `*.pfx`, `*.p12`
- `credentials.json`, `service-account*.json`

---

## 3. TeamBrain Sharing Boundaries

In collaborative environments:
- **Shared**: Curated domain invariants (`[INV-xxx]`), architecture boundaries, and package maps.
- **Isolated to Local**: Personal handoff notes, active scratchpad entries, and uncommitted git stashes.
