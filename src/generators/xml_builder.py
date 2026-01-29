"""Generate Crossref XML using lxml."""

from lxml import etree
from datetime import datetime
from typing import List
import yaml
import logging
from ..models.metadata import CrossrefMetadata

logger = logging.getLogger(__name__)


class CrossrefXMLBuilder:
    """Builds Crossref 5.4.0 compliant XML for reports."""

    NSMAP = {
        None: "http://www.crossref.org/schema/5.4.0",
        'xsi': "http://www.w3.org/2001/XMLSchema-instance",
        'jats': "http://www.ncbi.nlm.nih.gov/JATS1",
        'fr': "http://www.crossref.org/fundref.xsd",
        'rel': "http://www.crossref.org/relations.xsd",
    }

    SCHEMA_LOCATION = (
        "http://www.crossref.org/schema/5.4.0 "
        "https://www.crossref.org/schemas/crossref5.4.0.xsd"
    )

    def __init__(self, config_path: str = 'config/crossref_config.yml'):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)

    def build_batch(self, publications: List[CrossrefMetadata]) -> etree.Element:
        """Build complete doi_batch XML.

        Args:
            publications: List of CrossrefMetadata objects

        Returns:
            lxml Element tree
        """
        logger.info(f"Building XML for {len(publications)} reports")

        root = self._create_root()
        root.append(self._build_head())

        body = etree.SubElement(root, "body")
        for pub in publications:
            try:
                body.append(self._build_report(pub))
            except Exception as e:
                logger.error(f"Failed to build XML for {pub.doi}: {e}")

        return root

    def _create_root(self) -> etree.Element:
        """Create doi_batch root element with namespaces."""
        root = etree.Element(
            "doi_batch",
            nsmap=self.NSMAP,
            version="5.4.0"
        )
        root.set(
            f"{{{self.NSMAP['xsi']}}}schemaLocation",
            self.SCHEMA_LOCATION
        )
        return root

    def _build_head(self) -> etree.Element:
        """Build head section with depositor info."""
        head = etree.Element("head")

        # Batch ID (timestamp-based)
        batch_id = f"pi_batch_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        etree.SubElement(head, "doi_batch_id").text = batch_id

        # Timestamp
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        etree.SubElement(head, "timestamp").text = timestamp

        # Depositor info
        depositor = etree.SubElement(head, "depositor")
        etree.SubElement(depositor, "depositor_name").text = self.config['depositor']['name']
        etree.SubElement(depositor, "email_address").text = self.config['depositor']['email']

        # Registrant
        etree.SubElement(head, "registrant").text = self.config['depositor']['registrant']

        return head

    def _build_report(self, metadata: CrossrefMetadata) -> etree.Element:
        """Build report-paper element.

        Args:
            metadata: CrossrefMetadata object

        Returns:
            report-paper element
        """
        # Root report-paper element
        report = etree.Element("report-paper")

        # report-paper_metadata element
        report_metadata = etree.SubElement(report, "report-paper_metadata", language="en")

        # Contributors
        if metadata.contributors:
            report_metadata.append(self._build_contributors(metadata.contributors))

        # Titles
        titles = etree.SubElement(report_metadata, "titles")
        etree.SubElement(titles, "title").text = metadata.title

        # Publication date
        report_metadata.append(self._build_date(metadata.publication_date, "publication_date", media_type="online"))

        # Publisher
        publisher = etree.SubElement(report_metadata, "publisher")
        etree.SubElement(publisher, "publisher_name").text = metadata.publisher_name
        if metadata.publisher_place:
            etree.SubElement(publisher, "publisher_place").text = metadata.publisher_place

        # Publisher item (report number)
        if metadata.report_number:
            publisher_item = etree.SubElement(report_metadata, "publisher_item")
            identifier = etree.SubElement(publisher_item, "identifier", id_type="report-number")
            identifier.text = metadata.report_number

        # Relations (for sections that have a parent)
        if metadata.is_section and metadata.parent_doi:
            report_metadata.append(self._build_relations(metadata.parent_doi))

        # Abstract (JATS format)
        if metadata.abstract:
            report_metadata.append(self._build_abstract(metadata.abstract))

        # DOI data
        report_metadata.append(self._build_doi_data(metadata.doi, metadata.resource_url))

        return report

    def _build_contributors(self, contributors: list) -> etree.Element:
        """Build contributors section.

        Args:
            contributors: List of Author objects

        Returns:
            contributors element
        """
        contrib_elem = etree.Element("contributors")

        for contrib in contributors:
            person = etree.SubElement(
                contrib_elem,
                "person_name",
                sequence=contrib.sequence,
                contributor_role=contrib.role
            )

            if contrib.given_name:
                etree.SubElement(person, "given_name").text = contrib.given_name
            if contrib.surname:
                etree.SubElement(person, "surname").text = contrib.surname

            if contrib.orcid:
                etree.SubElement(
                    person,
                    "ORCID",
                    authenticated="false"
                ).text = contrib.orcid

        return contrib_elem

    def _build_date(self, date: 'CrossrefDate', tag_name: str, media_type: str = None) -> etree.Element:
        """Build date element.

        Args:
            date: CrossrefDate object
            tag_name: Element tag name (e.g., "publication_date")
            media_type: Optional media_type attribute

        Returns:
            Date element
        """
        if media_type:
            date_elem = etree.Element(tag_name, media_type=media_type)
        else:
            date_elem = etree.Element(tag_name)

        etree.SubElement(date_elem, "month").text = f"{date.month:02d}"
        etree.SubElement(date_elem, "day").text = f"{date.day:02d}"
        etree.SubElement(date_elem, "year").text = str(date.year)

        return date_elem

    def _build_relations(self, parent_doi: str) -> etree.Element:
        """Build relations section for sections.

        Args:
            parent_doi: Parent publication DOI

        Returns:
            program element with relations
        """
        # Use relations namespace
        program = etree.Element(
            "{http://www.crossref.org/relations.xsd}program",
            nsmap={'rel': 'http://www.crossref.org/relations.xsd'}
        )

        related_item = etree.SubElement(program, "{http://www.crossref.org/relations.xsd}related_item")

        intra_work_relation = etree.SubElement(
            related_item,
            "{http://www.crossref.org/relations.xsd}intra_work_relation"
        )
        intra_work_relation.set("relationship-type", "isPartOf")
        intra_work_relation.set("identifier-type", "doi")
        intra_work_relation.text = parent_doi

        return program

    def _build_abstract(self, abstract_text: str) -> etree.Element:
        """Build JATS abstract element.

        Args:
            abstract_text: Plain text abstract

        Returns:
            jats:abstract element
        """
        # Create abstract element with JATS namespace
        abstract = etree.Element(
            "{http://www.ncbi.nlm.nih.gov/JATS1}abstract"
        )

        # Add paragraph with abstract text
        paragraph = etree.SubElement(
            abstract,
            "{http://www.ncbi.nlm.nih.gov/JATS1}p"
        )
        paragraph.text = abstract_text

        return abstract

    def _build_doi_data(self, doi: str, resource_url: str) -> etree.Element:
        """Build doi_data section.

        Args:
            doi: DOI string
            resource_url: URL to resource

        Returns:
            doi_data element
        """
        doi_data = etree.Element("doi_data")
        etree.SubElement(doi_data, "doi").text = doi
        etree.SubElement(doi_data, "resource").text = resource_url
        return doi_data

    def to_string(self, element: etree.Element) -> str:
        """Convert XML element to formatted string.

        Args:
            element: lxml Element

        Returns:
            XML string with declaration
        """
        return etree.tostring(
            element,
            pretty_print=True,
            xml_declaration=True,
            encoding='UTF-8'
        ).decode('utf-8')
