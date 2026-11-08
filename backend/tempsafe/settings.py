"""Read renamed environment settings while supporting existing installations."""

import os


def project_setting(name: str, default: str = "") -> str:
    """Prefer TEMPSAFE settings, including empty values, over the legacy prefix."""
    if name in os.environ:
        return os.environ[name]
    return os.environ.get(name.replace("TEMPSAFE_", "TEMSAFE_", 1), default)
