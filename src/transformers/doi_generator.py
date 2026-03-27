"""Generate DOIs from publication codes."""

import re
import logging
from typing import Union
from ..models.publication import Publication
from ..models.section import Section

logger = logging.getLogger(__name__)


class DOIGenerator:
    """Generates DOIs with configurable patterns.

    DOI Format (UPPERCASE):
    - Publications: 10.64239/PI-{CODE} (e.g., PI-EC088, PI-VL102)
    - Sections: 10.64239/PI-{CODE}{NN} (e.g., PI-VL10201, PI-VL10202)

    Video Lectures have numeric-only codes in WordPress and need VL prefix added.
    Other products (EC, BG, OA, NL, QT, CAP, etc.) already have their prefix.
    """

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
            DOI string (e.g., "10.64239/PI-EC088" or "10.64239/PI-VL10201")
        """
        # Handle Section
        if isinstance(item, Section):
            return self._generate_section_doi(item, parent_code)

        # Handle Publication
        if item.publication_code:
            code = self._normalize_code(item.publication_code)
            doi = f"{self.prefix}/PI-{code}"
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

        Section DOIs append the section number directly to the parent code.
        Example: Parent VL102, Section 1 -> PI-VL10201

        Args:
            section: Section object
            parent_code: Parent publication code

        Returns:
            DOI string (e.g., "10.64239/PI-VL10201")
        """
        if not parent_code:
            raise ValueError(f"Cannot generate section DOI without parent code for section {section.id}")

        normalized_parent = self._normalize_code(parent_code)
        section_suffix = f"{section.section_number:02d}"  # 01, 02, etc.

        # Append section number directly (e.g., VL102 + 01 = VL10201)
        doi = f"{self.prefix}/PI-{normalized_parent}{section_suffix}"
        logger.debug(f"Generated section DOI: {doi} for section {section.id}")
        return doi

    def _normalize_code(self, code: str) -> str:
        """Normalize publication code for DOI.

        - Adds VL prefix to numeric-only codes (Video Lectures)
        - Converts to UPPERCASE
        - Removes hyphens for consistency

        Args:
            code: Raw publication code from WordPress

        Returns:
            Normalized code suitable for DOI (e.g., "EC088", "VL102")
        """
        # Remove leading/trailing whitespace
        code = code.strip()

        # Remove hyphens (OPC-031 -> OPC031)
        code = code.replace('-', '')

        # Convert to uppercase
        code = code.upper()

        # Check if code is numeric-only (Video Lecture)
        if code.isdigit():
            code = f"VL{code}"
            logger.debug(f"Added VL prefix for Video Lecture: {code}")

        if not code:
            raise ValueError("Publication code resulted in empty string after normalization")

        return code
