"""Article extraction and relevance models."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ArticleRelevance(BaseModel):
    """LLM output for article relevance filtering."""

    is_relevant: bool = Field(description="Whether the article is relevant for networking")
    reason: str = Field(description="Brief explanation of the decision")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score 0-1")


class ArticleContent(BaseModel):
    """Extracted article content."""

    url: str
    title: str
    text: str
    cleaned_text: str
    extracted_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
