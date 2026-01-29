"""Crossref metadata model."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from .author import Author


@dataclass
class CrossrefDate:
    """Crossref date structure."""
    year: int
    month: int
    day: int


@dataclass
class CrossrefMetadata:
    """Crossref report metadata."""
    doi: str
    title: str
    contributors: List[Author]
    publication_date: CrossrefDate
    resource_url: str
    publisher_name: str
    publisher_place: str
    report_number: str
    content_type: str = "report"
    parent_doi: Optional[str] = None  # For sections that belong to a parent publication
    is_section: bool = False  # True if this is a section
    abstract: str = ''  # Abstract text
