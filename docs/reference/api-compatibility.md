# API Compatibility Policy

This document defines the API stability guarantees for Django Automate.

---

## Version Strategy

Django Automate uses **URI versioning**:

```
/api/v1/...  ← Current stable version
/api/v2/...  ← Future major version (breaking changes)
```

---

## Stability Guarantees (v1)

Within a major version, we guarantee:

| Change Type | Allowed? |
|-------------|----------|
| **Add new endpoints** | ✅ Yes |
| **Add new optional fields** | ✅ Yes |
| **Add new optional query params** | ✅ Yes |
| **Remove endpoints** | ❌ No |
| **Remove fields** | ❌ No |
| **Change field types** | ❌ No |
| **Change URL paths** | ❌ No |

---

## Deprecation Process

1. **Announce**: Deprecated features marked in OpenAPI schema
2. **Warn**: Response headers include `Deprecation` header
3. **Migrate**: Minimum 3 months before removal
4. **Remove**: Only in next major version (v2)

Example deprecation header:

```http
Deprecation: true
Sunset: Sat, 01 Jan 2026 00:00:00 GMT
Link: </api/v1/new-endpoint>; rel="successor-version"
```

---

## Breaking Changes

Breaking changes only occur in major version bumps:

- v1 → v2: Breaking changes allowed
- v1.1 → v1.2: No breaking changes

---

## Changelog

API changes documented in:

- `CHANGELOG.md` (repository root)
- OpenAPI schema `info.version` field
- Release notes on GitHub
