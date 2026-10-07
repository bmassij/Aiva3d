"""FastAPI entrypoint: uvicorn quote_api.app:app"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from quote_api.config import QUOTE_CORS_ORIGINS
from quote_api.routers import health, profiles, quote

app = FastAPI(
    title="Crooijmans Quote API",
    description="3MF analysis and commercial quote calculation (Pilot 3).",
    version="0.1.0",
)

if QUOTE_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=QUOTE_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(health.router)
app.include_router(profiles.router)
app.include_router(quote.router)
