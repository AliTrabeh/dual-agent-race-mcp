"""Global semantic version tracking (SG-C10). Starts at 1.00, bumped on meaningful change."""

__version__ = "1.00"


def get_version() -> str:
    """Return the current package version string."""
    return __version__
