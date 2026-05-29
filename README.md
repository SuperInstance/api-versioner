# api-versioner

**API version management** — semantic versioning, deprecation tracking, migration guides, and version-aware routing. Pure Python, zero dependencies.

## What This Gives You

- **Semantic version parsing** — parse, compare, bump, and check compatibility
- **Versioned endpoints** — track which API versions expose which endpoints
- **Deprecation management** — sunset dates, migration paths, and deprecation notices
- **Version-aware routing** — route requests to the correct handler by API version
- **Migration guides** — auto-generate migration documentation between versions

## Installation

```bash
pip install api-versioner
```

## Quick Start

```python
from api_versioner import APIVersion, Endpoint, DeprecationManager, VersionRouter
from datetime import date

# Parse and compare versions
v1 = APIVersion.parse("1.2.3")
v2 = APIVersion.parse("2.0.0-beta.1")
assert v1 < v2
assert v1.is_compatible(APIVersion.parse("1.9.0"))

# Deprecation tracking
dm = DeprecationManager()
dm.deprecate(APIVersion.parse("1.0.0"), sunset_date=date(2025, 6, 1), reason="Upgrade to v2")

# Version-aware routing
router = VersionRouter()
router.add_route(APIVersion.parse("1.0.0"), handler_v1)
router.add_route(APIVersion.parse("2.0.0"), handler_v2)
handler = router.resolve(APIVersion.parse("2.1.0"))
```

## Testing

```bash
pip install -e .
pytest
```

## License

MIT
