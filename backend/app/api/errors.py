"""Turn request validation failures into one short message the app can show.

FastAPI's default 422 body is a list of technical error objects. The app only
needs one sentence, so every validation error is returned as
``{"detail": "<message>"}`` with status 422.
"""

from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

AMOUNT_TOO_LOW = "Enter an amount greater than $0."
AMOUNT_TOO_HIGH = "Enter an amount of $1,000,000 or less."
AMOUNT_TOO_PRECISE = "Enter an amount with no more than two decimal places."
PERIOD_INVALID = "Choose daily, weekly, or monthly."
BODY_INVALID = 'Send a JSON body like {"period": "weekly", "amount": 400.00}.'
BUDGET_ID_INVALID = "Budget ID must be a whole number."


def message_for(error: dict[str, Any]) -> str:
    loc = tuple(error.get("loc", ()))
    kind = error.get("type", "")
    field = loc[-1] if loc else None

    if loc[:1] == ("path",):
        return BUDGET_ID_INVALID
    if kind == "extra_forbidden":
        return f"Unexpected field: {field}."
    if field == "amount":
        if kind == "less_than_equal":
            return AMOUNT_TOO_HIGH
        if kind == "decimal_max_places":
            return AMOUNT_TOO_PRECISE
        # missing, null, blank, non-numeric, zero, or negative
        return AMOUNT_TOO_LOW
    if field == "limit":
        return "Limit must be a whole number between 1 and 50."
    if field == "period":
        return PERIOD_INVALID
    return BODY_INVALID


async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors = exc.errors()
    message = message_for(errors[0]) if errors else BODY_INVALID
    return JSONResponse(status_code=422, content={"detail": message})
