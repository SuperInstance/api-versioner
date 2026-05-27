"""Versioned API endpoint with method signatures and deprecation status."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .version import APIVersion


@dataclass
class Endpoint:
    path: str
    method: str
    description: str = ""
    handler: Optional[Callable[..., Any]] = None
    versions: List[APIVersion] = field(default_factory=list)
    deprecated_in: Optional[APIVersion] = None
    removed_in: Optional[APIVersion] = None
    parameters: Dict[str, str] = field(default_factory=dict)
    response_type: Optional[str] = None

    def __post_init__(self) -> None:
        self.method = self.method.upper()

    def add_version(self, version: APIVersion) -> Endpoint:
        if version not in self.versions:
            self.versions.append(version)
        return self

    def remove_version(self, version: APIVersion) -> Endpoint:
        self.versions = [v for v in self.versions if v != version]
        return self

    def is_available_in(self, version: APIVersion) -> bool:
        return any(v == version for v in self.versions)

    def available_versions(self) -> List[APIVersion]:
        return sorted(self.versions)

    def deprecate(self, version: APIVersion) -> Endpoint:
        self.deprecated_in = version
        return self

    def mark_removed(self, version: APIVersion) -> Endpoint:
        self.removed_in = version
        return self

    @property
    def is_deprecated(self) -> bool:
        return self.deprecated_in is not None

    @property
    def is_removed(self) -> bool:
        return self.removed_in is not None

    @property
    def key(self) -> str:
        return f"{self.method} {self.path}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Endpoint):
            return NotImplemented
        return self.method == other.method and self.path == other.path

    def __hash__(self) -> int:
        return hash((self.method, self.path))

    def __repr__(self) -> str:
        return f"Endpoint({self.path!r}, {self.method!r}, versions={[str(v) for v in self.versions]})"
