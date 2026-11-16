"""FastAPI application entry point.

Run locally from ``backend/``::

    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Interactive API docs are then at http://localhost:8000/docs.
"""

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api import budgets
from app.api.errors import validation_error_handler
from app.core.config import settings

app = FastAPI(title="Balance API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET", "PUT"],
    allow_headers=["Content-Type"],
)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.include_router(budgets.router)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
