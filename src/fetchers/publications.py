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
    # Last updated: 2026-03-27 (Batch 1 + Batch 2 = 312 publications)
    EXCLUDED_CODES = {
        # Video Lectures (numeric codes) - Batch 1 & 2
        '000', '001', '01', '02', '002', '003', '03', '004', '04', '005',
        '05', '06', '006', '07', '007', '08', '09', '10', '12', '13',
        '14', '15', '16', '17', '18', '20', '21', '22', '23', '24',
        '25', '26', '27', '29', '30', '31', '32', '34', '35', '36',
        '37', '38', '39', '40', '41', '42', '43', '44', '45', '46',
        '47', '48', '49', '50', '51', '52', '53', '54', '56', '57',
        '58', '59', '60', '61', '62', '63', '65', '66', '67', '68',
        '69', '70', '71', '72', '73', '74', '75', '76', '77', '78',
        '79', '80', '81', '82', '83', '84', '85', '86', '87', '89',
        '90', '91', '92', '93', '94', '95', '96', '97', '98', '100',
        '101', '102',
        # Expert Consultations - Batch 1 & 2
        'EC001', 'EC002', 'EC003', 'EC005', 'EC006', 'EC007', 'EC008', 'EC010',
        'EC012', 'EC013', 'EC014', 'EC015', 'EC016', 'EC017', 'EC018', 'EC019',
        'EC020', 'EC021', 'EC022', 'EC023', 'EC024', 'EC025', 'EC026', 'EC027',
        'EC028', 'EC029', 'EC030', 'EC031', 'EC032', 'EC033', 'EC034', 'EC035',
        'EC036', 'EC037', 'EC038', 'EC039', 'EC040', 'EC041', 'EC042', 'EC043',
        'EC044', 'EC045', 'EC046', 'EC047', 'EC048', 'EC049', 'EC050', 'EC051',
        'EC052', 'EC053', 'EC054', 'EC055', 'EC056', 'EC057', 'EC058', 'EC059',
        'EC060', 'EC061', 'EC062', 'EC063', 'EC064', 'EC065', 'EC066', 'EC068',
        'EC069', 'EC070', 'EC071', 'EC072', 'EC073', 'EC074', 'EC075', 'EC076',
        'EC077', 'EC078', 'EC079', 'EC080', 'EC081', 'EC083', 'EC084', 'EC085',
        'EC086', 'EC088',
        # Quick Takes - Batch 2
        'QT01', 'QT02', 'QT03', 'QT04', 'QT05', 'QT06', 'QT07', 'QT08', 'QT09', 'QT10',
        'QT11', 'QT12', 'QT13', 'QT14', 'QT15', 'QT16', 'QT17', 'QT18', 'QT19', 'QT20',
        'QT21', 'QT22', 'QT23', 'QT24', 'QT25', 'QT26', 'QT27', 'QT28', 'QT29', 'QT30',
        'QT31', 'QT32', 'QT33', 'QT34', 'QT35', 'QT36', 'QT37', 'QT38', 'QT39', 'QT40',
        'QT41', 'QT42', 'QT43', 'QT44', 'QT45', 'QT46', 'QT47', 'QT48', 'QT49', 'QT50',
        'QT51', 'QT52', 'QT53', 'QT54', 'QT55', 'QT56', 'QT57', 'QT58', 'QT59', 'QT60',
        'QT61', 'QT62', 'QT63', 'QT64', 'QT65', 'QT66', 'QT67', 'QT68', 'QT69', 'QT70',
        'QT71', 'QT72', 'QT73', 'QT74', 'QT75', 'QT76', 'QT77', 'QT78', 'QT79', 'QT80',
        'QT81', 'QT82', 'QT83', 'QT84', 'QT85',
        # Brain Guides - Batch 2
        'BG001', 'BG002', 'BG003', 'BG004', 'BG005', 'BG006', 'BG007', 'BG008',
        'BG009', 'BG010', 'BG011', 'BG012', 'BG013', 'BG014', 'BG015', 'BG016',
        'BG017', 'BG018', 'BG019', 'BG020', 'BG021',
        # Special Brain Guides - Batch 2
        'SBG2024', 'SBG2025',
        # CAPSmart Takes - Batch 2
        'CAPST01', 'CAPST02', 'CAPST03', 'CAPST04', 'CAPST05', 'CAPST06', 'CAPST07',
        'CAPST08', 'CAPST09', 'CAPST10', 'CAPST11', 'CAPST12', 'CAPST13', 'CAPST14',
        'CAPST15', 'CAPST16', 'CAPST17', 'CAPST18', 'CAPST19', 'CAPST20',
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
