"""Author data model."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Author:
    """Author or contributor information."""
    name: str
    role: str = 'author'
    sequence: str = 'additional'  # 'first' or 'additional'
    given_name: Optional[str] = None
    surname: Optional[str] = None
    orcid: Optional[str] = None
    affiliation: Optional[str] = None

    def parse_name(self):
        """Split name into given_name and surname."""
        if self.given_name and self.surname:
            return  # Already parsed

        parts = self.name.strip().split()
        if len(parts) == 0:
            self.surname = "Unknown"
        elif len(parts) == 1:
            self.surname = parts[0]
        elif len(parts) == 2:
            self.given_name = parts[0]
            self.surname = parts[1]
        else:
            # Multiple parts: assume last is surname
            self.surname = parts[-1]
            self.given_name = ' '.join(parts[:-1])
