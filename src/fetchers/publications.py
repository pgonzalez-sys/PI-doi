"""Fetch publications and related author data."""

from typing import List, Optional
import logging
from .base import WordPressClient
from ..models.publication import Publication
from ..models.section import Section
from ..models.author import Author
from ..utils.abstract_extractor import get_abstract

logger = logging.getLogger(__name__)


class PublicationFetcher:
    """Fetches publications with author details from WordPress."""

    # Publication codes that have already been submitted to Crossref
    # These will be excluded from new batches
    EXCLUDED_CODES = {
        'EC088',  # Managing Catatonia - submitted 2026-03-11
        '102',    # VL102 - Addiction Psychopharmacology - submitted 2026-03-11
    }

    # Valid code prefixes for DOI generation
    # Only publications with these codes will get DOIs
    VALID_PREFIXES = (
        'EC',     # Expert Consultations
        'QT',     # Quick Takes
        'BG',     # Brain Guides
        'SBG',    # Special Brain Guides
        'CAP',    # CAPSmart Takes (includes CAPS, CAPST)
    )

    def __init__(self, client: WordPressClient):
        self.client = client

    def _is_valid_for_doi(self, code: str) -> bool:
        """Check if a publication code should get a DOI.

        Valid codes:
        - Numeric only (Video Lectures): 102, 57, 000, 08, etc.
        - EC (Expert Consultations): EC088, EC054, etc.
        - QT (Quick Takes): QT52, etc.
        - BG/SBG (Brain Guides): BG800, SBG2025, etc.
        - CAP/CAPS/CAPST (CAPSmart Takes)

        Invalid codes (excluded):
        - NL (Newsletter)
        - OPC (Open Podcast)
        - OA (Open Access)
        - Any other prefixes
        """
        if not code:
            return False

        code = code.strip().upper()

        # Numeric-only codes are Video Lectures
        if code.isdigit():
            return True

        # Check for valid prefixes
        return code.startswith(self.VALID_PREFIXES)

    def fetch_all(self, limit: Optional[int] = None, exclude_submitted: bool = True) -> List[Publication]:
        """Fetch all publications with author details.

        Args:
            limit: Optional limit on number of publications to fetch
            exclude_submitted: If True, exclude already submitted DOIs (default: True)
        """
        logger.info("Fetching published publications...")

        raw_pubs = self.client.get_paginated(
            'wp/v2/sfwd-courses',
            params={
                '_fields': 'id,title,date,modified,link,author,coauthors,acf',
                'status': 'publish',  # Only fetch published, not drafts
                'per_page': min(limit, 100) if limit else 100
            }
        )

        # Filter to only include valid publication types for DOI
        original_count = len(raw_pubs)
        raw_pubs = [
            p for p in raw_pubs
            if self._is_valid_for_doi(p.get('acf', {}).get('pi_publication_code', ''))
        ]
        filtered_count = original_count - len(raw_pubs)
        if filtered_count > 0:
            logger.info(f"Filtered out {filtered_count} publications (NL, OPC, OA, etc. - no DOI needed)")

        # Filter out already submitted publications
        if exclude_submitted:
            before_exclusion = len(raw_pubs)
            raw_pubs = [
                p for p in raw_pubs
                if p.get('acf', {}).get('pi_publication_code', '') not in self.EXCLUDED_CODES
            ]
            excluded_count = before_exclusion - len(raw_pubs)
            if excluded_count > 0:
                logger.info(f"Excluded {excluded_count} already submitted publications")

        # Apply limit if specified
        if limit:
            raw_pubs = raw_pubs[:limit]

        logger.info(f"Found {len(raw_pubs)} publications to process")

        publications = []
        for raw_pub in raw_pubs:
            try:
                pub = self._parse_publication(raw_pub)
                publications.append(pub)
            except Exception as e:
                logger.error(f"Failed to parse publication {raw_pub.get('id')}: {e}")

        logger.info(f"Successfully parsed {len(publications)} publications")
        return publications

    def _parse_publication(self, data: dict) -> Publication:
        """Parse raw WordPress data into Publication model."""
        pub_id = data['id']

        # Fetch author details
        authors = self._fetch_authors(
            author_id=data.get('author'),
            coauthor_ids=data.get('coauthors', [])
        )

        # Extract publication code and abstract from ACF
        acf_data = data.get('acf', {}) or {}
        publication_code = acf_data.get('pi_publication_code', '')

        # Extract abstract from key points or learning objectives
        key_points = acf_data.get('pi_key_points', '')
        learning_objectives = acf_data.get('pi_learning_objectives', '')
        content = data.get('content', {}).get('rendered', '')

        # Use key points first, then learning objectives, then content
        abstract = get_abstract(
            key_points=key_points or learning_objectives,
            content=content,
            has_sections=False  # Will be updated after fetching sections
        )

        # Create publication
        publication = Publication(
            id=pub_id,
            title=data['title']['rendered'],
            date=data['date'],
            modified=data['modified'],
            link=data['link'],
            publication_code=publication_code,
            authors=authors,
            sections=[],
            abstract=abstract
        )

        # Fetch sections for this publication
        publication.sections = self._fetch_sections(pub_id, publication_code)

        return publication

    def _fetch_authors(self, author_id: Optional[int], coauthor_ids: List[int]) -> List[Author]:
        """Fetch author and coauthor details.

        NOTE: We only use coauthors (faculty), not the WordPress author field.
        The WordPress 'author' field is the person who uploaded/published the content,
        not the actual faculty member.

        Args:
            author_id: Primary author ID (WordPress user) - IGNORED
            coauthor_ids: List of coauthor IDs (actual faculty)

        Returns:
            List of Author objects (faculty only)
        """
        authors = []

        # Only fetch coauthors (actual faculty)
        # The WordPress 'author' field is just the uploader, not the faculty
        for idx, coauthor_id in enumerate(coauthor_ids):
            coauthor = self._fetch_coauthor(coauthor_id)
            if coauthor:
                # First coauthor is primary, rest are additional
                coauthor.sequence = 'first' if idx == 0 else 'additional'
                authors.append(coauthor)

        return authors

    def _fetch_user(self, user_id: int) -> Optional[Author]:
        """Fetch WordPress user details."""
        try:
            data = self.client.get(f"wp/v2/users/{user_id}")
            return Author(
                name=data['name'],
                role='author'
            )
        except Exception as e:
            logger.warning(f"Failed to fetch user {user_id}: {e}")
            return None

    def _fetch_coauthor(self, coauthor_id: int) -> Optional[Author]:
        """Fetch coauthor (faculty) details from Co-Authors Plus plugin.

        The description field contains: "{Display Name} {Display Name} {slug} {id} {email}"
        We extract the first occurrence of the display name.
        """
        try:
            data = self.client.get(f"wp/v2/coauthors/{coauthor_id}")

            # Parse display name from description field
            # Format: "Mark Horowitz Mark Horowitz mark-horowitz 1625256 email@..."
            description = data.get('description', '')
            if description:
                # Split and take first token (clean display name)
                parts = description.split()
                # The display name is typically the first 2+ words before the duplicate
                # Try to find where it repeats
                name = data.get('name', 'Unknown Author')

                # Better approach: extract until we hit the slug (lowercase-with-dashes)
                display_parts = []
                for part in parts:
                    # Stop when we hit a slug pattern (lowercase with dashes)
                    if '-' in part and part.islower():
                        break
                    # Stop when we hit an email
                    if '@' in part:
                        break
                    # Stop when we hit a number
                    if part.isdigit():
                        break
                    display_parts.append(part)

                if display_parts:
                    # Join parts but remove duplicates
                    # "Mark Horowitz Mark Horowitz" -> "Mark Horowitz"
                    name_text = ' '.join(display_parts)
                    # Check if it's duplicated (first half == second half)
                    words = name_text.split()
                    mid = len(words) // 2
                    if len(words) >= 2 and words[:mid] == words[mid:]:
                        name = ' '.join(words[:mid])
                    else:
                        name = name_text
                else:
                    name = data.get('name', 'Unknown Author')
            else:
                name = data.get('name', 'Unknown Author')

            return Author(
                name=name,
                role='author'
            )
        except Exception as e:
            logger.warning(f"Failed to fetch coauthor {coauthor_id}: {e}")
            return None

    def _fetch_sections(self, publication_id: int, publication_code: str) -> List[Section]:
        """Fetch sections (lessons) for a publication.

        Args:
            publication_id: WordPress course ID
            publication_code: Publication code for section numbering

        Returns:
            List of Section objects
        """
        try:
            # Fetch section IDs from course steps
            logger.debug(f"Fetching sections for publication {publication_id}")
            steps_data = self.client.get(f"ldlms/v2/sfwd-courses/{publication_id}/steps", timeout=10)

            # Extract lesson IDs from nested structure
            # API returns: {"t": {"sfwd-lessons": [id1, id2, ...]}, ...}
            section_ids = steps_data.get('t', {}).get('sfwd-lessons', [])

            if not section_ids:
                logger.debug(f"No sections found for publication {publication_id}")
                return []

            logger.info(f"Found {len(section_ids)} sections for publication {publication_id}")

            # Fetch details for each section
            sections = []
            for idx, section_id in enumerate(section_ids, start=1):
                section = self._fetch_section_details(section_id, publication_id, idx)
                if section:
                    sections.append(section)

            return sections

        except Exception as e:
            logger.warning(f"Failed to fetch sections for publication {publication_id}: {e}")
            return []

    def _fetch_section_details(self, section_id: int, parent_id: int, section_number: int) -> Optional[Section]:
        """Fetch details for a single section.

        Args:
            section_id: Section (lesson) ID
            parent_id: Parent publication ID
            section_number: Position in publication sequence

        Returns:
            Section object or None
        """
        try:
            data = self.client.get(f"wp/v2/sfwd-lessons/{section_id}")

            # Fetch authors
            authors = self._fetch_authors(
                author_id=data.get('author'),
                coauthor_ids=data.get('coauthors', [])
            )

            # Extract section code and abstract from ACF
            acf_data = data.get('acf', {}) or {}
            section_code = acf_data.get('pi_section_code', '')
            key_points = acf_data.get('pi_key_points', '')
            content = data.get('content', {}).get('rendered', '')

            # Extract abstract
            abstract = get_abstract(
                key_points=key_points,
                content=content,
                has_sections=True
            )

            return Section(
                id=section_id,
                title=data['title']['rendered'],
                date=data['date'],
                modified=data['modified'],
                link=data['link'],
                section_code=section_code,
                authors=authors,
                parent_publication_id=parent_id,
                section_number=section_number,
                abstract=abstract
            )

        except Exception as e:
            logger.warning(f"Failed to fetch section {section_id}: {e}")
            return None
