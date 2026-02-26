from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """Standard error response body matching FastAPI's default HTTPException format."""

    detail: str
