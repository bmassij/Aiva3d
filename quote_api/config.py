"""Quote API configuration from environment."""

from __future__ import annotations

import os

# Max upload size (default 50 MB)
QUOTE_MAX_UPLOAD_BYTES = int(os.environ.get("QUOTE_MAX_UPLOAD_BYTES", str(50 * 1024 * 1024)))

# Comma-separated origins for CORS; empty = no CORS middleware
QUOTE_CORS_ORIGINS = [
    o.strip()
    for o in os.environ.get("QUOTE_CORS_ORIGINS", "").split(",")
    if o.strip()
]

CURRENCY = os.environ.get("QUOTE_CURRENCY", "EUR")
