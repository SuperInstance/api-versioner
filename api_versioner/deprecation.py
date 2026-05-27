"""Deprecation manager with sunset dates, migration guides, and deprecation notices."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Dict, List, Optional

from .version import APIVersion


@dataclass
class DeprecationNotice:
    version: APIVersion
    announced_on: date
    sunset_date: Optional[date] = None
    migration_guide: str = ""
    reason: str = ""
    replacement: str = ""

    @property
    def is_past_sunset(self) -> bool:
        if self.sunset_date is None:
            return False
        return date.today() >= self.sunset_date

    @property
    def days_until_sunset(self) -> Optional[int]:
        if self.sunset_date is None:
            return None
        return (self.sunset_date - date.today()).days

    def __repr__(self) -> str:
        return f"DeprecationNotice(version={self.version}, sunset={self.sunset_date}, reason={self.reason!r})"


@dataclass
class DeprecationManager:
    _notices: Dict[str, DeprecationNotice] = field(default_factory=dict)

    def deprecate(
        self,
        version: APIVersion,
        *,
        announced_on: Optional[date] = None,
        sunset_date: Optional[date] = None,
        migration_guide: str = "",
        reason: str = "",
        replacement: str = "",
    ) -> DeprecationNotice:
        notice = DeprecationNotice(
            version=version,
            announced_on=announced_on or date.today(),
            sunset_date=sunset_date,
            migration_guide=migration_guide,
            reason=reason,
            replacement=replacement,
        )
        self._notices[str(version)] = notice
        return notice

    def remove(self, version: APIVersion) -> Optional[DeprecationNotice]:
        return self._notices.pop(str(version), None)

    def is_deprecated(self, version: APIVersion) -> bool:
        return str(version) in self._notices

    def get_notice(self, version: APIVersion) -> Optional[DeprecationNotice]:
        return self._notices.get(str(version))

    def all_notices(self) -> List[DeprecationNotice]:
        notices = list(self._notices.values())
        notices.sort(key=lambda n: n.version, reverse=True)
        return notices

    def active_notices(self) -> List[DeprecationNotice]:
        return [n for n in self.all_notices() if not n.is_past_sunset]

    def expired_notices(self) -> List[DeprecationNotice]:
        return [n for n in self.all_notices() if n.is_past_sunset]

    def get_sunset_header(self, version: APIVersion) -> Optional[str]:
        notice = self.get_notice(version)
        if notice is None or notice.sunset_date is None:
            return None
        dt = datetime(notice.sunset_date.year, notice.sunset_date.month, notice.sunset_date.day)
        return dt.strftime("%a, %d %b %Y 00:00:00 GMT")

    def get_deprecation_headers(self, version: APIVersion) -> Dict[str, str]:
        notice = self.get_notice(version)
        if notice is None:
            return {}
        headers: Dict[str, str] = {"Deprecation": "true"}
        sunset = self.get_sunset_header(version)
        if sunset:
            headers["Sunset"] = sunset
        if notice.migration_guide:
            headers["Link"] = f'<{notice.migration_guide}>; rel="successor-version"'
        return headers
