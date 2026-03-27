"""Command-line interface for Crossref XML generation."""

import argparse
import logging
from pathlib import Path
from typing import List
from lxml import etree
from datetime import datetime

from .fetchers.base import WordPressClient
from .fetchers.publications import PublicationFetcher
from .transformers.wp_to_crossref import CrossrefTransformer
from .generators.xml_builder import CrossrefXMLBuilder
from .validators.schema_validator import SchemaValidator

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Generate Crossref XML from WordPress publications'
    )
    parser.add_argument(
        '--mode',
        choices=['batch', 'individual', 'both'],
        default='batch',
        help='Output mode: single batch file, individual files, or both'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('output/batches'),
        help='Output directory'
    )
    parser.add_argument(
        '--validate',
        action='store_true',
        default=True,
        help='Validate XML against schema (default: true)'
    )
    parser.add_argument(
        '--no-validate',
        action='store_false',
        dest='validate',
        help='Skip XML validation'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of publications to process'
    )

    args = parser.parse_args()

    try:
        # Step 1: Fetch publications
        logger.info("=" * 60)
        logger.info("STEP 1: Fetching publications from WordPress")
        logger.info("=" * 60)
        client = WordPressClient()
        fetcher = PublicationFetcher(client)
        publications = fetcher.fetch_all(limit=args.limit)

        if not publications:
            logger.error("No publications found!")
            return 1

        logger.info(f"Processing {len(publications)} publications")

        # Step 2: Transform to Crossref metadata
        logger.info("")
        logger.info("=" * 60)
        logger.info("STEP 2: Transforming to Crossref metadata")
        logger.info("=" * 60)
        transformer = CrossrefTransformer()
        metadata_list = transformer.transform_batch(publications)

        if not metadata_list:
            logger.error("No metadata generated!")
            return 1

        # Step 3: Generate XML
        logger.info("")
        logger.info("=" * 60)
        logger.info("STEP 3: Generating XML")
        logger.info("=" * 60)
        builder = CrossrefXMLBuilder()
        xml_element = builder.build_batch(metadata_list)

        # Step 4: Validate
        if args.validate:
            logger.info("")
            logger.info("=" * 60)
            logger.info("STEP 4: Validating XML")
            logger.info("=" * 60)
            try:
                validator = SchemaValidator()
                is_valid, errors = validator.validate(xml_element)
                if not is_valid:
                    logger.error("Validation failed! Errors:")
                    for error in errors:
                        logger.error(f"  {error}")
                    return 1
            except FileNotFoundError as e:
                logger.warning(f"Schema validation skipped: {e}")
        else:
            logger.info("Validation skipped (--no-validate)")

        # Step 5: Write output
        logger.info("")
        logger.info("=" * 60)
        logger.info("STEP 5: Writing output files")
        logger.info("=" * 60)
        args.output.mkdir(parents=True, exist_ok=True)

        if args.mode in ['batch', 'both']:
            output_file = args.output / f"crossref_batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
            with open(output_file, 'wb') as f:
                f.write(etree.tostring(
                    xml_element,
                    pretty_print=True,
                    xml_declaration=True,
                    encoding='UTF-8'
                ))
            logger.info(f"✓ Wrote batch file: {output_file}")
            logger.info(f"  Size: {output_file.stat().st_size / 1024:.1f} KB")

        if args.mode in ['individual', 'both']:
            individual_dir = Path('output/individual')
            individual_dir.mkdir(parents=True, exist_ok=True)

            for metadata in metadata_list:
                single_xml = builder.build_batch([metadata])
                filename = metadata.doi.replace('/', '_').replace('.', '_') + '.xml'
                filepath = individual_dir / filename

                with open(filepath, 'wb') as f:
                    f.write(etree.tostring(
                        single_xml,
                        pretty_print=True,
                        xml_declaration=True,
                        encoding='UTF-8'
                    ))

            logger.info(f"✓ Wrote {len(metadata_list)} individual files to {individual_dir}")

        # Generate DOI report
        doi_report_path = args.output / "doi_report.csv"
        _write_doi_report(publications, metadata_list, doi_report_path)
        logger.info(f"✓ Wrote DOI report: {doi_report_path}")

        # Summary
        logger.info("")
        logger.info("=" * 60)
        logger.info("SUMMARY")
        logger.info("=" * 60)

        # Count publications and sections
        pub_count = sum(1 for m in metadata_list if not m.is_section)
        section_count = sum(1 for m in metadata_list if m.is_section)
        total_sections_in_pubs = sum(len(p.sections) for p in publications)

        logger.info(f"Publications processed: {len(publications)}")
        logger.info(f"Publication DOIs generated: {pub_count}")
        logger.info(f"Section DOIs generated: {section_count}")
        logger.info(f"Total DOIs: {len(metadata_list)}")
        logger.info(f"Output mode: {args.mode}")
        logger.info(f"Validation: {'PASSED' if args.validate else 'SKIPPED'}")
        logger.info("")
        logger.info(f"📋 DOI Report: {doi_report_path}")
        logger.info("")
        logger.info("✅ Done!")

        return 0

    except Exception as e:
        logger.exception("Fatal error:")
        return 1


def _write_doi_report(publications: List, metadata_list: List, output_path: Path):
    """Write a CSV report of all generated DOIs.

    Args:
        publications: List of Publication objects
        metadata_list: List of CrossrefMetadata objects
        output_path: Path to output CSV file
    """
    import csv
    from .transformers.doi_generator import DOIGenerator
    import yaml

    # Load config for DOI generator
    with open('config/crossref_config.yml') as f:
        config = yaml.safe_load(f)
    doi_gen = DOIGenerator(config)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Type',
            'DOI',
            'Title',
            'Report Number',
            'URL',
            'Parent DOI',
            'WordPress ID',
            'Sections'
        ])

        for pub in publications:
            # Find publication metadata by matching normalized report number
            normalized_code = doi_gen._normalize_code(pub.publication_code) if pub.publication_code else str(pub.id)
            pub_metadata = next((m for m in metadata_list if not m.is_section and m.report_number == normalized_code), None)

            if pub_metadata:
                # Write publication row
                writer.writerow([
                    'Publication',
                    pub_metadata.doi,
                    pub_metadata.title,
                    pub_metadata.report_number,
                    pub_metadata.resource_url,
                    '',
                    pub.id,
                    len(pub.sections)
                ])

                # Write sections - match metadata to original section objects for WordPress IDs
                section_metadatas = [m for m in metadata_list if m.is_section and m.parent_doi == pub_metadata.doi]
                for section_metadata in section_metadatas:
                    # Find the original section object by matching URL
                    section_wp_id = ''
                    for section in pub.sections:
                        if section.link == section_metadata.resource_url:
                            section_wp_id = section.id
                            break

                    writer.writerow([
                        'Section',
                        section_metadata.doi,
                        section_metadata.title,
                        section_metadata.report_number,
                        section_metadata.resource_url,
                        pub_metadata.doi,
                        section_wp_id,
                        ''
                    ])


if __name__ == '__main__':
    exit(main())
