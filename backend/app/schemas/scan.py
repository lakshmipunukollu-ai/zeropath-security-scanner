from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ScanCreateRequest(BaseModel):
    repo_url: str


class ScanResponse(BaseModel):
    id: str
    repo_id: str
    status: str
    files_scanned: int = 0
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


class ScanStatusResponse(BaseModel):
    id: str
    status: str
    files_scanned: int
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
