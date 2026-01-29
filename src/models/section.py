"""Section data model."""

from dataclasses import dataclass
from datetime import datetime
from typing import List
from .author import Author


@dataclass
class Section:
    """WordPress section (lesson) data."""
    id: int
    title: str
    date: str  # ISO format from WordPress
    modified: str
    link: str
    section_code: str
    authors: List[Author]
    parent_publication_id: int  # Link to parent publication
    section_number: int  # Position in publication
    abstract: str = ''  # Abstract text (from key points or content)

    @property
    def publication_date(self) -> datetime:
        """Parse publication date to datetime."""
        date_str = self.date.replace('Z', '+00:00')
        return datetime.fromisoformat(date_str)
