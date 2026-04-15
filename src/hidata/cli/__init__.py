from __future__ import annotations

# console_scripts entrypoint expects `hidata.cli:app`
# We expose `app` as a callable that invokes the Click root group.
from .main import cli as app

__all__ = ["app"]
