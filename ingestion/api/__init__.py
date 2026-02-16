"""
HTTP entry points for ingestion: web form POST and webhooks for each source.
"""

from ingestion.api.app import create_app

__all__ = ["create_app"]
