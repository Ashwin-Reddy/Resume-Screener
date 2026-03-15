"""Pydantic models for request/response validation."""
from pydantic import BaseModel
from typing import Dict, List


class MessageResponse(BaseModel):
    message: str


class AnalyzeResumeResponse(BaseModel):
    match_score: float
    missing_skills: Dict[str, List[str]]
    explanation: str
