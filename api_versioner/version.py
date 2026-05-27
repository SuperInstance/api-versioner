"""Semantic version parsing, comparison, and compatibility checking."""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import total_ordering
from typing import Optional

_SEMVER_RE = re.compile(
    r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<pre>[a-zA-Z0-9.\-]+))?"
    r"(?:\+(?P<build>[a-zA-Z0-9.\-]+))?$"
)


@dataclass(frozen=True)
@total_ordering
class APIVersion:
    major: int
    minor: int
    patch: int
    prerelease: Optional[str] = None
    build: Optional[str] = None

    @classmethod
    def parse(cls, version_str: str) -> APIVersion:
        m = _SEMVER_RE.match(version_str.strip())
        if m is None:
            raise ValueError(f"Invalid semver string: {version_str!r}")
        return cls(
            major=int(m["major"]),
            minor=int(m["minor"]),
            patch=int(m["patch"]),
            prerelease=m["pre"],
            build=m["build"],
        )

    @classmethod
    def of(cls, major: int, minor: int = 0, patch: int = 0) -> APIVersion:
        return cls(major=major, minor=minor, patch=patch)

    def __str__(self) -> str:
        s = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            s += f"-{self.prerelease}"
        if self.build:
            s += f"+{self.build}"
        return s

    def __repr__(self) -> str:
        return f"APIVersion.parse({str(self)!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, APIVersion):
            return NotImplemented
        return (self.major, self.minor, self.patch, self.prerelease) == (
            other.major, other.minor, other.patch, other.prerelease
        )

    def __hash__(self) -> int:
        return hash((self.major, self.minor, self.patch, self.prerelease))

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, APIVersion):
            return NotImplemented
        if (self.major, self.minor, self.patch) != (other.major, other.minor, other.patch):
            return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)
        if self.prerelease is None and other.prerelease is None:
            return False
        if self.prerelease is not None and other.prerelease is None:
            return True
        if self.prerelease is None and other.prerelease is not None:
            return False
        return self.prerelease < other.prerelease

    def is_compatible(self, other: APIVersion) -> bool:
        return self.major == other.major

    def can_upgrade_to(self, other: APIVersion) -> bool:
        return self.major == other.major and other >= self

    def bump_type(self, other: APIVersion) -> Optional[str]:
        if other.major == self.major + 1 and other.minor == 0 and other.patch == 0:
            return "major"
        if other.major == self.major and other.minor == self.minor + 1 and other.patch == 0:
            return "minor"
        if other.major == self.major and other.minor == self.minor and other.patch == self.patch + 1:
            return "patch"
        return None
