"""Compatibility import for deployments or examples using `uvicorn server:app`."""

from main import app

__all__ = ["app"]
