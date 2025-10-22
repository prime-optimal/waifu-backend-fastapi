"""Application package for Waifu backend."""

# Re-export factory for convenience
from .app.factory import create_app

__all__ = ["create_app"]
