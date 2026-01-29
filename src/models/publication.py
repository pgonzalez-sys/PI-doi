"""Publication data model."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from .section import Section
from .author import Author


@dataclass
class Publication:
    """WordPress publication data."""
    id: int
    title: str
    date: str  # ISO format from WordPress
    modified: str
    link: str
    publication_code: str
    authors: List[Author]
    sections: List['Section'] = field(default_factory=list)  # Child sections
    abstract: str = ''  # Abstract text (from key points or content)

    @property
    def publication_date(self) -> datetime:
        """Parse publication date to datetime."""
        # Remove 'Z' or timezone info and parse
        date_str = self.date.replace('Z', '+00:00')
        return datetime.fromisoformat(date_str)
