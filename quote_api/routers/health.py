from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    return {"ok": True, "service": "crooijmans-quote-api", "version": "0.1.0"}
