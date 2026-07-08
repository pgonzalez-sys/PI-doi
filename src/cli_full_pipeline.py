"""End-to-end DOI pipeline: generate a new batch, review it, submit to Crossref,
then write the confirmed DOIs back into WordPress.

This automates everything EXCEPT the moment of submitting to Crossref itself --
by default it always stops and asks for confirmation before that step, because
DOI registration is meant to be permanent and each batch should get a human
look before it goes out. Pass --yes to skip the prompt once you trust it.

Usage:

  # Normal run: generates, shows you what it found, asks before submitting
  python -m src.cli_full_pipeline

  # Skip the confirmation prompt (still prints the summary first)
  python -m src.cli_full_pipeline --yes

  # Dry run against Crossref's TEST system instead of production (doesn't
  # register real DOIs -- use this to sanity-check credentials/format)
  python -m src.cli_full_pipeline --test

  # Second half only: you already submitted and have a diagnostic XML
  # (e.g. pasted from Crossref's confirmation email) -- parse it and write
  # the confirmed DOIs back to WordPress without regenerating/resubmitting
  python -m src.cli_full_pipeline --diagnostic-file path/to/diagnostic.xml --skip-submit --batch-number 8 --doi-report path/to/doi_report.csv
"""

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path

from lxml import etree

from .fetchers.base import WordPressClient
from .fetchers.publications import PublicationFetcher
from .transformers.wp_to_crossref import CrossrefTransformer
from .generators.xml_builder import CrossrefXMLBuilder
from .cli import _write_doi_report
from .submitters.crossref_deposit import submit_batch
from .submitters.diagnostic_parser import parse_diagnostic
from .writeback.wordpress_writeback import load_doi_report, write_dois_to_wordpress

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BATCH_STATE_PATH = Path('config/batch_state.json')
EXPORT_DIR = Path('output/production')


def next_batch_number():
    if BATCH_STATE_PATH.exists():
        state = json.loads(BATCH_STATE_PATH.read_text())
        return state.get('last_batch_number', 0) + 1
    return 1


def save_batch_number(n):
    BATCH_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    BATCH_STATE_PATH.write_text(json.dumps({'last_batch_number': n}, indent=2))


def print_diagnostic_result(diagnostic):
    successful = {r['doi'] for r in diagnostic['records'] if r['status'] == 'Success'}
    failed = [r for r in diagnostic['records'] if r['status'] != 'Success']
    print(f"Diagnostic ({diagnostic.get('submission_id')}): "
          f"{len(successful)} succeeded, {len(failed)} failed/other")
    if failed:
        print("FAILURES / WARNINGS (not written to WordPress):")
        for r in failed:
            print(f"  {r['doi']}: {r['status']} - {r['message']}")
    return successful


def do_writeback(doi_report_path, successful_dois, client):
    doi_report_rows = load_doi_report(doi_report_path)
    results = write_dois_to_wordpress(doi_report_rows, successful_dois, client=client)
    ok_count = sum(1 for r in results if r['ok'])
    print(f"WordPress write-back: {ok_count}/{len(results)} succeeded")
    for r in results:
        if not r['ok']:
            print(f"  FAILED: {r['doi']} (WP id {r['wp_id']}): {r.get('error', 'mismatch after write')}")
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--test', action='store_true', help="Submit to Crossref's TEST system, not production")
    parser.add_argument('--yes', action='store_true', help='Skip the pre-submission confirmation prompt')
    parser.add_argument('--skip-submit', action='store_true', help='Skip generation+submission; only parse a diagnostic and write back to WordPress')
    parser.add_argument('--diagnostic-file', type=Path, help='Path to a diagnostic XML to parse (required with --skip-submit; optional otherwise for testing)')
    parser.add_argument('--batch-number', type=int, help='Required with --skip-submit: which batch this diagnostic belongs to')
    parser.add_argument('--doi-report', type=Path, help='Required with --skip-submit: path to that batch\'s doi_report.csv')
    args = parser.parse_args()

    client = WordPressClient()

    if args.skip_submit:
        if not (args.diagnostic_file and args.doi_report):
            parser.error('--skip-submit requires both --diagnostic-file and --doi-report')
        diagnostic = parse_diagnostic(args.diagnostic_file.read_text())
        successful = print_diagnostic_result(diagnostic)
        do_writeback(args.doi_report, successful, client)
        return 0

    # Step 1: generate
    fetcher = PublicationFetcher(client)
    publications = fetcher.fetch_all()
    if not publications:
        logger.info("Nothing new to submit -- every valid publication is already registered at Crossref.")
        return 0

    transformer = CrossrefTransformer()
    metadata_list = transformer.transform_batch(publications)
    builder = CrossrefXMLBuilder()
    xml_element = builder.build_batch(metadata_list)

    batch_num = next_batch_number()
    date_str = datetime.now().strftime('%m%d%y')
    filename = f"Psychopharmacology Institute-{batch_num:03d}-{date_str}.xml"
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    xml_path = EXPORT_DIR / filename
    xml_path.write_bytes(etree.tostring(xml_element, pretty_print=True, xml_declaration=True, encoding='UTF-8'))

    doi_report_path = EXPORT_DIR / f"{xml_path.stem}-doi_report.csv"
    _write_doi_report(publications, metadata_list, doi_report_path)

    pub_count = sum(1 for m in metadata_list if not m.is_section)
    section_count = sum(1 for m in metadata_list if m.is_section)

    print()
    print("=" * 70)
    print(f"BATCH {batch_num:03d} READY -- {filename}")
    print("=" * 70)
    print(f"Publications: {pub_count}  |  Sections: {section_count}  |  Total DOIs: {len(metadata_list)}")
    print()
    for m in metadata_list:
        if not m.is_section:
            print(f"  {m.doi:28s} {m.title}")
    print()
    print(f"Saved: {xml_path}")
    print(f"DOI report: {doi_report_path}")
    print()

    if not args.yes:
        answer = input("Submit this batch to Crossref? [y/N] ").strip().lower()
        if answer != 'y':
            print("Not submitted -- file is saved locally for review. Re-run with --yes when ready,")
            print(f"or run: python -m src.cli_full_pipeline --skip-submit --batch-number {batch_num} "
                  f"--doi-report \"{doi_report_path}\" --diagnostic-file <path> once you have a diagnostic.")
            return 0

    # Step 2: submit
    ack = submit_batch(xml_path, use_test=args.test)
    print("Crossref acknowledgment:")
    print(ack)
    save_batch_number(batch_num)

    # Step 3: get the diagnostic
    if args.diagnostic_file:
        diagnostic_xml = args.diagnostic_file.read_text()
    else:
        print()
        print("Crossref processes submissions asynchronously -- the diagnostic report")
        print("(confirming which DOIs actually succeeded) isn't available immediately.")
        print("Check your email or the Crossref admin portal for it, then run:")
        print(f'  python -m src.cli_full_pipeline --skip-submit --batch-number {batch_num} '
              f'--doi-report "{doi_report_path}" --diagnostic-file <path to diagnostic.xml>')
        print(f"(Batch number {batch_num} is now reserved -- the next run will use {batch_num + 1}.)")
        return 0

    diagnostic = parse_diagnostic(diagnostic_xml)
    successful = print_diagnostic_result(diagnostic)

    # Step 4: write back to WordPress
    do_writeback(doi_report_path, successful, client)

    print()
    print("Add this row to DOI_GENERATION_INSTRUCTIONS.md's Batch History table:")
    print(f"| {batch_num:03d} | `{filename}` | {datetime.now().strftime('%Y-%m-%d')} | "
          f"{diagnostic['submission_id']} | {pub_count} | {section_count} | {len(metadata_list)} | (fill in codes) |")

    return 0


if __name__ == '__main__':
    exit(main())
