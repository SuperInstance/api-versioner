"""api-versioner — API version management with semver parsing, deprecation tracking, and migration paths."""

from .version import APIVersion
from .endpoint import Endpoint
from .deprecation import DeprecationManager
from .migration import MigrationPath, MigrationRegistry
from .router import VersionRouter

__all__ = ["APIVersion", "Endpoint", "DeprecationManager", "MigrationPath", "MigrationRegistry", "VersionRouter"]
__version__ = "1.0.0"
