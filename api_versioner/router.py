"""Version-aware router that dispatches requests to the correct API version handler."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .deprecation import DeprecationManager
from .endpoint import Endpoint
from .migration import MigrationRegistry
from .version import APIVersion


@dataclass
class RouteMatch:
    endpoint: Endpoint
    version: APIVersion
    is_deprecated: bool = False
    deprecation_headers: Dict[str, str] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

    @property
    def handler(self) -> Optional[Callable[..., Any]]:
        return self.endpoint.handler


@dataclass
class VersionRouter:
    endpoints: Dict[str, Endpoint] = field(default_factory=dict)
    deprecation: DeprecationManager = field(default_factory=DeprecationManager)
    migrations: MigrationRegistry = field(default_factory=MigrationRegistry)
    default_version: Optional[APIVersion] = None

    def register(self, endpoint: Endpoint) -> VersionRouter:
        self.endpoints[endpoint.key] = endpoint
        return self

    def unregister(self, method: str, path: str) -> Optional[Endpoint]:
        return self.endpoints.pop(f"{method.upper()} {path}", None)

    def set_default_version(self, version: APIVersion) -> VersionRouter:
        self.default_version = version
        return self

    def route(self, method: str, path: str, version: Optional[APIVersion] = None) -> Optional[RouteMatch]:
        version = version or self.default_version
        if version is None:
            return None

        key = f"{method.upper()} {path}"
        endpoint = self.endpoints.get(key)
        if endpoint is None:
            return None

        if endpoint.is_available_in(version):
            return self._build_match(endpoint, version)

        compatible = [v for v in endpoint.versions if v.is_compatible(version) and v <= version]
        if compatible:
            best = max(compatible)
            match = self._build_match(endpoint, best)
            if best != version:
                match.warnings.append(f"Exact version {version} not available; fell back to {best}")
            return match

        return None

    def _build_match(self, endpoint: Endpoint, version: APIVersion) -> RouteMatch:
        warnings: List[str] = []
        is_deprecated = self.deprecation.is_deprecated(version)
        if endpoint.is_deprecated:
            is_deprecated = True
            warnings.append(f"Endpoint {endpoint.key} is deprecated")
        deprecation_headers = self.deprecation.get_deprecation_headers(version) if is_deprecated else {}
        notice = self.deprecation.get_notice(version)
        if notice and notice.reason:
            warnings.append(f"Version {version} deprecated: {notice.reason}")
        return RouteMatch(endpoint=endpoint, version=version, is_deprecated=is_deprecated, deprecation_headers=deprecation_headers, warnings=warnings)

    def list_endpoints(self, version: Optional[APIVersion] = None) -> List[Endpoint]:
        eps = list(self.endpoints.values())
        if version is not None:
            eps = [e for e in eps if e.is_available_in(version)]
        return sorted(eps, key=lambda e: e.key)

    def list_versions(self) -> List[APIVersion]:
        versions: set = set()
        for ep in self.endpoints.values():
            versions.update(ep.versions)
        return sorted(versions)

    def endpoint_for(self, method: str, path: str) -> Optional[Endpoint]:
        return self.endpoints.get(f"{method.upper()} {path}")
