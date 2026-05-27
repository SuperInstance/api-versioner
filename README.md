# api-versioner

API version management — semantic versioning, deprecation tracking, migration guides, and version-aware routing.

A pure-Python library with zero external dependencies (beyond pytest for tests). Uses dataclasses and type hints throughout.

## Install

```bash
pip install api-versioner
```

## Quick Start

### Semantic Version Parsing & Comparison

```python
from api_versioner import APIVersion

v1 = APIVersion.parse("1.2.3")
v2 = APIVersion.parse("2.0.0-beta.1")

assert v1 < v2
assert APIVersion.parse("1.0.0").is_compatible(APIVersion.parse("1.9.0"))
assert APIVersion.parse("1.0.0").can_upgrade_to(APIVersion.parse("1.5.0"))
assert APIVersion.parse("1.2.3").bump_type(APIVersion.parse("1.2.4")) == "patch"
```

### Versioned Endpoints

```python
from api_versioner import Endpoint, APIVersion

ep = Endpoint("/users", "GET", description="List users")
ep.add_version(APIVersion.parse("1.0.0"))
ep.add_version(APIVersion.parse("2.0.0"))
assert ep.is_available_in(APIVersion.parse("1.0.0"))
```

### Deprecation Management

```python
from datetime import date
from api_versioner import DeprecationManager, APIVersion

dm = DeprecationManager()
dm.deprecate(
    APIVersion.parse("1.0.0"),
    sunset_date=date(2025, 6, 1),
    reason="Upgrade to v2",
    migration_guide="/docs/migrate-v2",
)

# RFC 8594 Sunset header
print(dm.get_sunset_header(APIVersion.parse("1.0.0")))

# Full deprecation headers for HTTP responses
headers = dm.get_deprecation_headers(APIVersion.parse("1.0.0"))
# {'Deprecation': 'true', 'Sunset': '...', 'Link': '</docs/migrate-v2>; rel="successor-version"'}
```

### Migration Paths

```python
from api_versioner import MigrationPath, APIVersion

path = MigrationPath(
    from_version=APIVersion.parse("1.0.0"),
    to_version=APIVersion.parse("2.0.0"),
)
path.add_field_mapping("user_id", "id")
path.add_field_mapping("price_cents", "price", transform=lambda v: v / 100)
path.add_step("Update auth to Bearer tokens", action="change_auth")
path.add_breaking_change("Removed /legacy/auth endpoint")

new_data = path.transform_data({"user_id": 42, "price_cents": 1999})
# {"id": 42, "price": 19.99}
```

### Version-Aware Router

```python
from api_versioner import VersionRouter, Endpoint, APIVersion

router = VersionRouter()
v1 = APIVersion.parse("1.0.0")
v2 = APIVersion.parse("2.0.0")

router.register(Endpoint("/users", "GET", versions=[v1, v2]))
router.register(Endpoint("/posts", "GET", versions=[v1]))

# Route a request
match = router.route("GET", "/users", v2)
assert match.version == v2

# Deprecation awareness
router.deprecation.deprecate(v1, sunset_date=date(2025, 12, 1))
match = router.route("GET", "/posts", v1)
assert match.is_deprecated
assert "Deprecation" in match.deprecation_headers
```

## Architecture

```
api_versioner/
├── __init__.py          # Public API — re-exports all main classes
├── version.py           # APIVersion — semver parsing, comparison, compatibility
├── endpoint.py          # Endpoint — versioned endpoint registration
├── deprecation.py       # DeprecationManager — sunset dates, HTTP headers, notices
├── migration.py         # MigrationPath, MigrationRegistry — field mappings, transformations
└── router.py            # VersionRouter — version-aware request dispatching
```

## License

MIT

---

Part of the [Cocapn fleet](https://github.com/Lucineer/the-fleet).

<i>Built with [Cocapn](https://github.com/Lucineer/cocapn-ai).</i>
