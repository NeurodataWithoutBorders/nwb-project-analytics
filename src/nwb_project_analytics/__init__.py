"""NWB Project Analytics package."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("nwb_project_analytics")
except PackageNotFoundError:
    # Package is not installed
    __version__ = "unknown"
