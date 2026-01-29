"""XSD schema validation."""

from lxml import etree
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class SchemaValidator:
    """Validates Crossref XML against XSD schema."""

    def __init__(self, schema_path: str = 'docs/cross-ref/schemas/crossref5.4.0.xsd'):
        self.schema_path = schema_path
        self.schema = self._load_schema()

    def _load_schema(self) -> etree.XMLSchema:
        """Load XSD schema.

        Returns:
            XMLSchema object

        Raises:
            FileNotFoundError: If schema file doesn't exist
        """
        schema_file = Path(self.schema_path)
        if not schema_file.exists():
            raise FileNotFoundError(f"Schema file not found: {self.schema_path}")

        with open(schema_file, 'rb') as f:
            schema_doc = etree.parse(f)
        return etree.XMLSchema(schema_doc)

    def validate(self, xml_element: etree.Element) -> tuple:
        """Validate XML against schema.

        Args:
            xml_element: lxml Element to validate

        Returns:
            Tuple of (is_valid: bool, errors: list)
        """
        try:
            self.schema.assertValid(xml_element)
            logger.info("✓ XML validation passed")
            return True, []
        except etree.DocumentInvalid as e:
            errors = [str(err) for err in self.schema.error_log]
            logger.error("✗ XML validation failed:")
            for error in errors:
                logger.error(f"  {error}")
            return False, errors
