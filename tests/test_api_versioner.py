"""Comprehensive tests for api_versioner."""

import pytest
from datetime import date, timedelta

from api_versioner import APIVersion, Endpoint, DeprecationManager, MigrationPath, VersionRouter
from api_versioner.migration import MigrationRegistry, FieldMapping, MigrationStep


class TestAPIVersionParsing:
    def test_parse_simple(self):
        v = APIVersion.parse("1.2.3")
        assert v.major == 1 and v.minor == 2 and v.patch == 3

    def test_parse_with_prerelease(self):
        v = APIVersion.parse("2.0.0-beta.1")
        assert v.prerelease == "beta.1" and str(v) == "2.0.0-beta.1"

    def test_parse_with_build(self):
        v = APIVersion.parse("1.0.0+build.42")
        assert v.build == "build.42" and str(v) == "1.0.0+build.42"

    def test_parse_full(self):
        v = APIVersion.parse("3.1.4-alpha.2+build.99")
        assert v.major == 3 and v.minor == 1 and v.patch == 4

    def test_parse_invalid(self):
        with pytest.raises(ValueError): APIVersion.parse("not-a-version")
        with pytest.raises(ValueError): APIVersion.parse("1.2")
        with pytest.raises(ValueError): APIVersion.parse("")

    def test_of_constructor(self):
        assert APIVersion.of(2, 1, 0) == APIVersion.parse("2.1.0")

    def test_str_roundtrip(self):
        for s in ["1.0.0", "2.3.4", "0.1.0", "10.20.30"]:
            assert str(APIVersion.parse(s)) == s


class TestAPIVersionComparison:
    def test_ordering(self):
        v1, v2, v3 = APIVersion.parse("1.0.0"), APIVersion.parse("1.1.0"), APIVersion.parse("2.0.0")
        assert v1 < v2 < v3 and v3 > v2 > v1

    def test_equality(self):
        assert APIVersion.parse("1.2.3") == APIVersion.parse("1.2.3")
        assert APIVersion.parse("1.2.3") != APIVersion.parse("1.2.4")

    def test_prerelease_sorts_before_release(self):
        assert APIVersion.parse("1.0.0-alpha") < APIVersion.parse("1.0.0")

    def test_sorting(self):
        versions = ["2.0.0", "1.0.0", "1.1.0", "0.5.0"]
        parsed = [APIVersion.parse(v) for v in versions]
        assert [str(v) for v in sorted(parsed)] == ["0.5.0", "1.0.0", "1.1.0", "2.0.0"]

    def test_hash_equality(self):
        v1, v2 = APIVersion.parse("1.2.3"), APIVersion.parse("1.2.3")
        assert hash(v1) == hash(v2) and len({v1, v2}) == 1


class TestAPIVersionCompatibility:
    def test_compatible_same_major(self):
        assert APIVersion.parse("1.0.0").is_compatible(APIVersion.parse("1.9.9"))

    def test_not_compatible_different_major(self):
        assert not APIVersion.parse("1.0.0").is_compatible(APIVersion.parse("2.0.0"))

    def test_can_upgrade(self):
        v1, v2 = APIVersion.parse("1.0.0"), APIVersion.parse("1.5.0")
        assert v1.can_upgrade_to(v2) and not v2.can_upgrade_to(v1)

    def test_cannot_upgrade_across_major(self):
        assert not APIVersion.parse("1.0.0").can_upgrade_to(APIVersion.parse("2.0.0"))

    def test_bump_type(self):
        v = APIVersion.parse("1.2.3")
        assert v.bump_type(APIVersion.parse("1.2.4")) == "patch"
        assert v.bump_type(APIVersion.parse("1.3.0")) == "minor"
        assert v.bump_type(APIVersion.parse("2.0.0")) == "major"
        assert v.bump_type(APIVersion.parse("3.0.0")) is None


class TestEndpoint:
    def test_create(self):
        ep = Endpoint("/users", "GET", description="List users")
        assert ep.path == "/users" and ep.method == "GET"

    def test_method_uppercased(self):
        assert Endpoint("/users", "get").method == "GET"

    def test_add_version(self):
        ep = Endpoint("/users", "GET")
        v = APIVersion.parse("1.0.0")
        ep.add_version(v)
        assert ep.is_available_in(v) and ep.available_versions() == [v]

    def test_remove_version(self):
        v1, v2 = APIVersion.parse("1.0.0"), APIVersion.parse("2.0.0")
        ep = Endpoint("/users", "GET", versions=[v1, v2])
        ep.remove_version(v1)
        assert not ep.is_available_in(v1) and ep.is_available_in(v2)

    def test_deprecation(self):
        ep = Endpoint("/users", "GET")
        v = APIVersion.parse("1.5.0")
        ep.deprecate(v)
        assert ep.is_deprecated and ep.deprecated_in == v

    def test_key_and_equality(self):
        ep1, ep2, ep3 = Endpoint("/users", "GET"), Endpoint("/users", "GET"), Endpoint("/users", "POST")
        assert ep1 == ep2 and ep1 != ep3
        assert ep1.key == "GET /users" and ep3.key == "POST /users"

    def test_hashable(self):
        assert len({Endpoint("/users", "GET"), Endpoint("/users", "GET")}) == 1


class TestDeprecationManager:
    def test_deprecate_and_check(self):
        dm = DeprecationManager()
        v = APIVersion.parse("1.0.0")
        dm.deprecate(v, reason="Use v2", sunset_date=date(2025, 6, 1))
        assert dm.is_deprecated(v)

    def test_not_deprecated(self):
        assert not DeprecationManager().is_deprecated(APIVersion.parse("1.0.0"))

    def test_get_notice(self):
        dm = DeprecationManager()
        v = APIVersion.parse("1.0.0")
        notice = dm.deprecate(v, reason="Old")
        assert dm.get_notice(v) is notice and notice.reason == "Old"

    def test_remove_notice(self):
        dm = DeprecationManager()
        v = APIVersion.parse("1.0.0")
        dm.deprecate(v)
        assert dm.remove(v) is not None and not dm.is_deprecated(v)

    def test_sunset_header(self):
        dm = DeprecationManager()
        v = APIVersion.parse("1.0.0")
        dm.deprecate(v, sunset_date=date(2025, 1, 15))
        header = dm.get_sunset_header(v)
        assert header is not None and "2025" in header

    def test_deprecation_headers(self):
        dm = DeprecationManager()
        v = APIVersion.parse("1.0.0")
        dm.deprecate(v, sunset_date=date(2025, 6, 1), migration_guide="/docs/migrate")
        headers = dm.get_deprecation_headers(v)
        assert headers["Deprecation"] == "true" and "Sunset" in headers and "/docs/migrate" in headers["Link"]

    def test_active_vs_expired(self):
        dm = DeprecationManager()
        past = date.today() - timedelta(days=10)
        future = date.today() + timedelta(days=30)
        dm.deprecate(APIVersion.parse("1.0.0"), sunset_date=future)
        dm.deprecate(APIVersion.parse("0.9.0"), sunset_date=past)
        assert len(dm.active_notices()) == 1 and len(dm.expired_notices()) == 1

    def test_all_notices_sorted(self):
        dm = DeprecationManager()
        for s in ["1.0.0", "2.0.0", "1.5.0"]:
            dm.deprecate(APIVersion.parse(s))
        assert [str(n.version) for n in dm.all_notices()] == ["2.0.0", "1.5.0", "1.0.0"]


class TestFieldMapping:
    def test_rename(self):
        assert FieldMapping("old_field", "new_field").apply({"old_field": 42, "other": "keep"}) == {"new_field": 42, "other": "keep"}

    def test_transform(self):
        assert FieldMapping("cents", "dollars", transform=lambda v: v / 100).apply({"cents": 1999}) == {"dollars": 19.99}

    def test_missing_field(self):
        assert FieldMapping("missing", "new").apply({"other": 1}) == {"other": 1}


class TestMigrationPath:
    def test_add_field_mapping(self):
        path = MigrationPath(from_version=APIVersion.parse("1.0.0"), to_version=APIVersion.parse("2.0.0"))
        path.add_field_mapping("user_id", "id").add_field_mapping("full_name", "name")
        assert len(path.field_mappings) == 2

    def test_transform_data(self):
        path = MigrationPath(from_version=APIVersion.parse("1.0.0"), to_version=APIVersion.parse("2.0.0"))
        path.add_field_mapping("user_id", "id").add_field_mapping("full_name", "name")
        assert path.transform_data({"user_id": 1, "full_name": "Alice", "keep": True}) == {"id": 1, "name": "Alice", "keep": True}

    def test_add_step(self):
        path = MigrationPath(from_version=APIVersion.parse("1.0.0"), to_version=APIVersion.parse("2.0.0"))
        path.add_step("Update auth", action="change_auth").add_step("Rename fields", action="rename")
        assert len(path.steps) == 2

    def test_summary(self):
        path = MigrationPath(from_version=APIVersion.parse("1.0.0"), to_version=APIVersion.parse("2.0.0"), breaking_changes=["Removed legacy auth"], notes="30 min downtime")
        path.add_field_mapping("old", "new")
        s = path.summary()
        assert "1.0.0" in s and "2.0.0" in s and "Removed legacy auth" in s


class TestMigrationRegistry:
    def test_register_and_find(self):
        reg = MigrationRegistry()
        v1, v2 = APIVersion.parse("1.0.0"), APIVersion.parse("2.0.0")
        reg.register(v1, v2).add_field_mapping("old", "new")
        path = reg.find_path(v1, v2)
        assert path is not None and len(path.field_mappings) == 1

    def test_find_missing(self):
        assert MigrationRegistry().find_path(APIVersion.parse("1.0.0"), APIVersion.parse("9.0.0")) is None

    def test_paths_from(self):
        reg = MigrationRegistry()
        v1, v2, v3 = APIVersion.parse("1.0.0"), APIVersion.parse("2.0.0"), APIVersion.parse("3.0.0")
        reg.register(v1, v2); reg.register(v1, v3)
        assert len(reg.paths_from(v1)) == 2

    def test_paths_to(self):
        reg = MigrationRegistry()
        v1, v1b, v2 = APIVersion.parse("1.0.0"), APIVersion.parse("1.5.0"), APIVersion.parse("2.0.0")
        reg.register(v1, v2); reg.register(v1b, v2)
        assert len(reg.paths_to(v2)) == 2


class TestVersionRouter:
    def test_register_and_route(self):
        router = VersionRouter()
        v1 = APIVersion.parse("1.0.0")
        ep = Endpoint("/users", "GET", versions=[v1])
        router.register(ep)
        match = router.route("GET", "/users", v1)
        assert match is not None and match.version == v1 and match.endpoint == ep

    def test_route_no_version(self):
        router = VersionRouter()
        v1 = APIVersion.parse("1.0.0")
        router.register(Endpoint("/users", "GET", versions=[v1])).set_default_version(v1)
        assert router.route("GET", "/users").version == v1

    def test_route_not_found(self):
        assert VersionRouter().route("GET", "/nonexistent", APIVersion.parse("1.0.0")) is None

    def test_route_compatible_fallback(self):
        router = VersionRouter()
        v10, v11, v12 = APIVersion.parse("1.0.0"), APIVersion.parse("1.1.0"), APIVersion.parse("1.2.0")
        router.register(Endpoint("/users", "GET", versions=[v10, v11]))
        match = router.route("GET", "/users", v12)
        assert match is not None and match.version == v11 and len(match.warnings) > 0

    def test_route_no_compatible(self):
        router = VersionRouter()
        v1, v2 = APIVersion.parse("1.0.0"), APIVersion.parse("2.0.0")
        router.register(Endpoint("/users", "GET", versions=[v1]))
        assert router.route("GET", "/users", v2) is None

    def test_deprecation_integration(self):
        router = VersionRouter()
        v1 = APIVersion.parse("1.0.0")
        router.register(Endpoint("/old", "GET", versions=[v1]))
        router.deprecation.deprecate(v1, reason="Use v2", sunset_date=date(2025, 12, 1))
        match = router.route("GET", "/old", v1)
        assert match.is_deprecated and "Deprecation" in match.deprecation_headers

    def test_list_endpoints(self):
        router = VersionRouter()
        v1, v2 = APIVersion.parse("1.0.0"), APIVersion.parse("2.0.0")
        router.register(Endpoint("/users", "GET", versions=[v1, v2]))
        router.register(Endpoint("/posts", "GET", versions=[v1]))
        assert len(router.list_endpoints()) == 2 and len(router.list_endpoints(v2)) == 1

    def test_list_versions(self):
        router = VersionRouter()
        v1, v2 = APIVersion.parse("1.0.0"), APIVersion.parse("2.0.0")
        router.register(Endpoint("/a", "GET", versions=[v1]))
        router.register(Endpoint("/b", "GET", versions=[v1, v2]))
        assert router.list_versions() == [v1, v2]

    def test_unregister(self):
        router = VersionRouter()
        ep = Endpoint("/users", "GET")
        router.register(ep)
        assert router.unregister("GET", "/users") == ep
        assert router.route("GET", "/users", APIVersion.parse("1.0.0")) is None

    def test_endpoint_for(self):
        router = VersionRouter()
        ep = Endpoint("/users", "GET")
        router.register(ep)
        assert router.endpoint_for("GET", "/users") is ep and router.endpoint_for("POST", "/users") is None


class TestIntegration:
    def test_full_workflow(self):
        v1, v11, v2 = APIVersion.parse("1.0.0"), APIVersion.parse("1.1.0"), APIVersion.parse("2.0.0")
        router = VersionRouter()
        users_v1 = Endpoint("/users", "GET", versions=[v1, v11])
        users_v2 = Endpoint("/users", "GET", versions=[v2])
        old_api = Endpoint("/legacy/auth", "POST", versions=[v1])
        old_api.deprecate(v11); old_api.mark_removed(v2)
        router.register(users_v1).register(users_v2).register(old_api)
        router.deprecation.deprecate(v1, reason="Upgrade to v2", sunset_date=date(2026, 1, 1), migration_guide="/docs/migrate-v2")
        migration = router.migrations.register(v1, v2)
        migration.add_field_mapping("user_id", "id")
        migration.add_field_mapping("full_name", "name")
        migration.add_step("Update auth to Bearer tokens", action="change_auth")
        migration.add_breaking_change("Removed /legacy/auth endpoint")

        match = router.route("GET", "/users", v2)
        assert match is not None and match.version == v2 and not match.is_deprecated

        path = router.migrations.find_path(v1, v2)
        assert path.transform_data({"user_id": 42, "full_name": "Alice", "meta": True}) == {"id": 42, "name": "Alice", "meta": True}

        headers = router.deprecation.get_deprecation_headers(v1)
        assert headers["Deprecation"] == "true" and "/docs/migrate-v2" in headers["Link"]
