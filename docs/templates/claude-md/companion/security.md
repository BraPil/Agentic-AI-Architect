# Security — [PROJECT NAME]

> Threat model, injection defense, secret hygiene, rate limiting, and dependency security.
> Security rules are never bent. When in doubt, the more restrictive choice is correct.

---

## Threat Model

*What are the realistic attack vectors for this system?*

| Threat | Vector | Impact | Mitigation |
|--------|--------|--------|-----------|
| Prompt injection | Malicious content in crawled web pages | LLM follows attacker instructions | `sanitize_text()` before all LLM prompts |
| Credential leak | Hardcoded API keys in source code | Unauthorized API access, billing | Env vars only; `.env` gitignored |
| Rate limit abuse | Unbounded external API calls | Service ban, cost runaway | `rate_limit()` before every external call |
| Dependency compromise | Malicious package in `requirements.txt` | Arbitrary code execution | Pin major versions; audit before adding |
| Data exfiltration via LLM | Sensitive data in prompts | Privacy breach | Audit what goes into prompts; no PII |
| Robots.txt violation | Crawling disallowed paths | Legal liability | CrawlerAgent respects `robots.txt` |
| Insecure deserialization | Loading untrusted JSON/pickle | RCE | Validate all external API responses |

---

## Prompt Injection Defense

*All content ingested from external sources must be sanitized before reaching any LLM.*

**The rule:** `sanitize_text()` is called on **every** string from external origin before it enters
a prompt. "External origin" includes: web pages, API responses, user input, database entries loaded
from external ingest, and file uploads. There are no exceptions.

**Implementation:**
- Central sanitization function lives at `[src/utils/helpers.py]`
- Do not inline sanitization logic in agents or pipelines
- If a new injection pattern is discovered, add it to the central `_INJECTION_PATTERNS` list
  AND add a test for it

**Injection pattern additions require:**
1. A description of the attack technique
2. The detection regex
3. A test case demonstrating detection
4. A log entry at `WARNING` level when the pattern fires (creates audit trail)

**Known patterns handled:** [List categories: role injection, system prompt override, instruction
injection, delimiter confusion, etc. — fill in as patterns are added]

---

## Secret Hygiene

**The rule:** API keys, tokens, passwords, and credentials exist **only** in environment variables.
No exceptions. Not in code comments, not in test fixtures, not in documentation examples.

| What | Where it lives | What NOT to do |
|------|---------------|----------------|
| API keys | Environment variables only | Never in source code, never in comments |
| Connection strings | `.env` file (gitignored) | Never committed to repo |
| Test credentials | `unittest.mock.patch` | Never in `tests/` fixtures |
| Example values | `.env.example` with placeholder strings | Never real values |

**`.env.example` format:**
```bash
# Required
[PREFIX]_API_KEY=your-api-key-here
[PREFIX]_DB_URL=sqlite:///path/to/db

# Optional (system works without these)
[PREFIX]_OPTIONAL_KEY=
```

**Pre-commit check:** CI should scan for high-entropy strings and known credential patterns.
Recommend `gitleaks` or `detect-secrets` as pre-commit hooks.

---

## Rate Limiting

**The rule:** every call to an external HTTP endpoint is preceded by a rate limiter call.

**Implementation:**
```python
from [src.utils.helpers] import rate_limit

# Before every external request:
rate_limit(calls_per_second=[N], endpoint="[service name]")
response = session.get(url)
```

**Default limits by service type:**

| Service Type | Default Limit | Override Mechanism |
|-------------|---------------|-------------------|
| Web crawl | 1 req/second | `CrawlerAgent` config |
| LLM API | Per-provider limits | Provider SDK retry logic |
| External data APIs | 10 req/minute | Agent config |
| Vector store | No limit (local) | N/A |

**User-Agent standard:** all external HTTP requests use the project's branded UA string defined
in `config/settings.py`. Never use the default `python-requests` UA.

---

## Dependency Security

*Before adding any new package:*

**Checklist:**
- [ ] Search for known CVEs: `pip-audit` or `safety check`
- [ ] Check last release date (inactive for 2+ years = risk)
- [ ] Check download count and maintainer reputation
- [ ] Pin major version only (allows security patch auto-updates)
- [ ] Document in `docs/architecture.md` and `docs/decision-log.md`

**Prohibited categories:**
- Packages with unpatched critical CVEs
- Packages abandoned for 2+ years with no security response history
- Packages with significantly fewer downloads than alternatives doing the same job

**Running the security audit:**
```bash
pip-audit                    # scan installed packages
safety check                 # alternative scanner
```

---

## Input Validation

**At system boundaries** (user input, external APIs, uploaded files):

- Validate structure before processing (Pydantic models preferred for API responses)
- Check expected keys exist before accessing them
- Set explicit size limits on inputs (max file size, max URL length, max prompt length)
- Reject unknown enum values explicitly

**Inside the system** (agent-to-agent data):
- Trust the internal contract; do not re-validate what the sending agent already validated
- If an internal agent can produce invalid data, fix the agent — don't add validation everywhere downstream

---

## Logging Security Events

*All security-relevant events must be logged at `WARNING` or higher:*

| Event | Level | What to log |
|-------|-------|------------|
| Sanitization pattern fires | `WARNING` | Pattern matched, source URL, snippet (truncated) |
| Rate limit triggered | `WARNING` | Endpoint, caller, current rate |
| Credential detected in content | `ERROR` | Source, do NOT log the credential itself |
| robots.txt violation attempt | `WARNING` | URL, disallowed path |
| External API error (4xx/5xx) | `WARNING` | Endpoint, status code, retry count |
| Schema validation failure | `WARNING` | Source, field names (not values) |

---

*Last updated: [YYYY-MM-DD]*
