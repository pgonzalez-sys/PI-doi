"""Generate DOIs from publication codes."""

import re
import logging
from typing import Union
from ..models.publication import Publication
from ..models.section import Section

logger = logging.getLogger(__name__)


class DOIGenerator:
    """Generates DOIs with configurable patterns."""

    def __init__(self, config: dict):
        self.prefix = config['doi']['prefix']
        self.pattern = config['doi']['pattern']
        self.fallback_pattern = config['doi'].get('fallback_pattern')

    def generate(self, item: Union[Publication, Section], parent_code: str = None) -> str:
        """Generate DOI with fallback strategy.

        Args:
            item: Publication or Section object
            parent_code: Parent publication code (for sections)

        Returns:
            DOI string (e.g., "10.64239/pi-opc-031" or "10.64239/pi-opc-031-s01")
        """
        # Handle Section
        if isinstance(item, Section):
            return self._generate_section_doi(item, parent_code)

        # Handle Publication
        if item.publication_code:
            code = self._sanitize_code(item.publication_code)
            doi = f"{self.prefix}/{self.pattern.replace('{publication_code}', code)}"
            logger.debug(f"Generated DOI: {doi} from code: {item.publication_code}")
            return doi
        elif self.fallback_pattern:
            doi = f"{self.prefix}/{self.fallback_pattern.replace('{wordpress_id}', str(item.id))}"
            logger.warning(f"Using fallback DOI pattern for publication {item.id}: {doi}")
            return doi
        else:
            raise ValueError(f"Cannot generate DOI for publication {item.id}: no publication_code and no fallback")

    def _generate_section_doi(self, section: Section, parent_code: str) -> str:
        """Generate DOI for a section.

        Args:
            section: Section object
            parent_code: Parent publication code

        Returns:
            DOI string (e.g., "10.64239/pi-opc-031-s01")
        """
        if not parent_code:
            raise ValueError(f"Cannot generate section DOI without parent code for section {section.id}")

        sanitized_parent = self._sanitize_code(parent_code)
        section_suffix = f"s{section.section_number:02d}"  # s01, s02, etc.

        doi = f"{self.prefix}/pi-{sanitized_parent}-{section_suffix}"
        logger.debug(f"Generated section DOI: {doi} for section {section.id}")
        return doi

    def _sanitize_code(self, code: str) -> str:
        """Ensure DOI suffix is valid.

        Args:
            code: Raw publication code

        Returns:
            Sanitized code suitable for DOI
        """
        # Remove leading/trailing whitespace
        code = code.strip()

        # Convert to lowercase
        code = code.lower()

        # Replace spaces and underscores with hyphens
        code = re.sub(r'[\s_]+', '-', code)

        # Remove any characters that aren't alphanumeric or hyphens
        code = re.sub(r'[^a-z0-9\-]', '', code)

        # Remove consecutive hyphens
        code = re.sub(r'-+', '-', code)

        # Remove leading/trailing hyphens
        code = code.strip('-')

        if not code:
            raise ValueError("Publication code resulted in empty string after sanitization")

        return code
