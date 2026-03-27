"""Transform WordPress data to Crossref metadata."""

from typing import List
import yaml
import logging
from datetime import datetime
from ..models.publication import Publication
from ..models.section import Section
from ..models.metadata import CrossrefMetadata, CrossrefDate
from .doi_generator import DOIGenerator

logger = logging.getLogger(__name__)


class CrossrefTransformer:
    """Transforms WordPress publications to Crossref metadata."""

    def __init__(self, config_path: str = 'config/crossref_config.yml'):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)
        self.doi_gen = DOIGenerator(self.config)

    def transform_batch(self, publications: List[Publication]) -> List[CrossrefMetadata]:
        """Transform multiple publications and their sections."""
        logger.info(f"Transforming {len(publications)} publications to Crossref metadata")
        metadata_list = []

        for pub in publications:
            try:
                # Transform publication
                pub_metadata = self.transform(pub)
                metadata_list.append(pub_metadata)

                # Transform sections
                if pub.sections:
                    logger.debug(f"Transforming {len(pub.sections)} sections for publication {pub.id}")
                    for section in pub.sections:
                        section_metadata = self.transform_section(section, pub.publication_code, pub_metadata.doi)
                        metadata_list.append(section_metadata)

            except Exception as e:
                logger.error(f"Failed to transform publication {pub.id}: {e}")

        logger.info(f"Successfully transformed {len(metadata_list)} items (publications + sections)")
        return metadata_list

    def transform(self, publication: Publication) -> CrossrefMetadata:
        """Transform single publication to Crossref metadata."""
        # Parse author names
        for author in publication.authors:
            author.parse_name()

        # Generate DOI
        doi = self.doi_gen.generate(publication)

        # Parse publication date
        pub_date = self._parse_date(publication.publication_date)

        # Normalize report number to match DOI format (e.g., EC088, VL102)
        report_number = self.doi_gen._normalize_code(publication.publication_code) if publication.publication_code else str(publication.id)

        # Create metadata
        return CrossrefMetadata(
            doi=doi,
            title=publication.title,
            contributors=publication.authors,
            publication_date=pub_date,
            resource_url=publication.link,
            publisher_name=self.config['publisher']['name'],
            publisher_place=self.config['publisher']['place'],
            report_number=report_number,
            content_type='report',
            abstract=publication.abstract
        )

    def transform_section(self, section: Section, parent_code: str, parent_doi: str) -> CrossrefMetadata:
        """Transform section to Crossref metadata.

        Args:
            section: Section object
            parent_code: Parent publication code
            parent_doi: Parent publication DOI

        Returns:
            CrossrefMetadata for the section
        """
        # Parse author names
        for author in section.authors:
            author.parse_name()

        # Generate DOI
        doi = self.doi_gen.generate(section, parent_code=parent_code)

        # Parse publication date
        pub_date = self._parse_date(section.publication_date)

        # Generate report number to match DOI format (e.g., VL10201, VL10202)
        normalized_parent = self.doi_gen._normalize_code(parent_code)
        report_number = f"{normalized_parent}{section.section_number:02d}"

        return CrossrefMetadata(
            doi=doi,
            title=section.title,
            contributors=section.authors,
            publication_date=pub_date,
            resource_url=section.link,
            publisher_name=self.config['publisher']['name'],
            publisher_place=self.config['publisher']['place'],
            report_number=report_number,
            content_type='report',
            parent_doi=parent_doi,
            is_section=True,
            abstract=section.abstract
        )

    def _parse_date(self, dt: datetime) -> CrossrefDate:
        """Convert datetime to Crossref date structure."""
        return CrossrefDate(
            year=dt.year,
            month=dt.month,
            day=dt.day
        )
