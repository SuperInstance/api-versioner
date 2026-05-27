"""Migration paths between API versions with field mappings and transformations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from .version import APIVersion


@dataclass
class FieldMapping:
    old_name: str
    new_name: str
    transform: Optional[Callable[[Any], Any]] = None
    description: str = ""

    def apply(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if self.old_name not in data:
            return data
        result = dict(data)
        value = result.pop(self.old_name)
        if self.transform is not None:
            value = self.transform(value)
        result[self.new_name] = value
        return result


@dataclass
class MigrationStep:
    description: str
    action: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"MigrationStep({self.action!r}: {self.description!r})"


@dataclass
class MigrationPath:
    from_version: APIVersion
    to_version: APIVersion
    field_mappings: List[FieldMapping] = field(default_factory=list)
    steps: List[MigrationStep] = field(default_factory=list)
    breaking_changes: List[str] = field(default_factory=list)
    notes: str = ""

    def add_field_mapping(
        self, old_name: str, new_name: str,
        transform: Optional[Callable[[Any], Any]] = None, description: str = "",
    ) -> MigrationPath:
        self.field_mappings.append(FieldMapping(old_name=old_name, new_name=new_name, transform=transform, description=description))
        return self

    def add_step(self, description: str, action: Optional[str] = None, **details: Any) -> MigrationPath:
        self.steps.append(MigrationStep(description=description, action=action, details=details))
        return self

    def add_breaking_change(self, description: str) -> MigrationPath:
        self.breaking_changes.append(description)
        return self

    def transform_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        result = dict(data)
        for mapping in self.field_mappings:
            result = mapping.apply(result)
        return result

    def summary(self) -> str:
        lines = [f"Migration: v{self.from_version} -> v{self.to_version}"]
        if self.breaking_changes:
            lines.append("Breaking changes:")
            for bc in self.breaking_changes:
                lines.append(f"  - {bc}")
        if self.field_mappings:
            lines.append("Field mappings:")
            for fm in self.field_mappings:
                lines.append(f"  - {fm.old_name} -> {fm.new_name}")
        if self.steps:
            lines.append("Steps:")
            for i, step in enumerate(self.steps, 1):
                lines.append(f"  {i}. {step.description}")
        if self.notes:
            lines.append(f"Notes: {self.notes}")
        return "\n".join(lines)


@dataclass
class MigrationRegistry:
    _paths: Dict[Tuple[str, str], MigrationPath] = field(default_factory=dict)

    def register(self, from_version: APIVersion, to_version: APIVersion) -> MigrationPath:
        path = MigrationPath(from_version=from_version, to_version=to_version)
        self._paths[(str(from_version), str(to_version))] = path
        return path

    def find_path(self, from_version: APIVersion, to_version: APIVersion) -> Optional[MigrationPath]:
        return self._paths.get((str(from_version), str(to_version)))

    def all_paths(self) -> List[MigrationPath]:
        return list(self._paths.values())

    def paths_from(self, version: APIVersion) -> List[MigrationPath]:
        return [p for p in self._paths.values() if p.from_version == version]

    def paths_to(self, version: APIVersion) -> List[MigrationPath]:
        return [p for p in self._paths.values() if p.to_version == version]
