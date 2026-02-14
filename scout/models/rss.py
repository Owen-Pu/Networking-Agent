"""RSS feed models."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class RSSItem(BaseModel):
    """RSS feed item."""

    title: str
    link: str
    published: Optional[datetime] = None
    description: Optional[str] = None
    feed_name: str
    guid: str  # Unique identifier for deduplication

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
