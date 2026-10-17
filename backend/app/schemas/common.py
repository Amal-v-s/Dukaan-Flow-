from typing import Any, List, Optional
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    loc: Optional[List[str]] = None
    msg: str
    type: Optional[str] = None


class ErrorBody(BaseModel):
    code: str
    message: str
    request_id: Optional[str] = None
    details: List[ErrorDetail] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    error: ErrorBody
