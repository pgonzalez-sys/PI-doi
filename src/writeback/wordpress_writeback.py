"""Write confirmed Crossref DOIs back into WordPress's pi_doi ACF field.

This is the step that makes a registered DOI actually show up on the site --
Crossref registration alone does not touch WordPress. Only writes a DOI for
rows Crossref has explicitly confirmed as "Success" in its diagnostic report,
so a partially-failed batch never gets its failed items written back as if
they succeeded.
"""

import csv
import logging

from ..fetchers.base import WordPressClient

logger = logging.getLogger(__name__)


def load_doi_report(csv_path):
    """Load a doi_report.csv (Type, DOI, Title, ..., WordPress ID, ...) as a list of dicts."""
    with open(csv_path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def write_dois_to_wordpress(doi_report_rows, successful_dois, client=None):
    """Write pi_doi for every row whose DOI Crossref confirmed as successful.

    Args:
        doi_report_rows: rows from load_doi_report()
        successful_dois: set/list of DOI strings Crossref's diagnostic marked "Success"
        client: an existing WordPressClient to reuse (creates one if not given)

    Returns:
        list of {doi, wp_id, ok, [error]} per row attempted (rows not in
        successful_dois are skipped and not included in the result).
    """
    client = client or WordPressClient()
    successful_dois = set(successful_dois)
    results = []

    for row in doi_report_rows:
        doi = row['DOI']
        if doi not in successful_dois:
            logger.warning(f"Skipping {doi} -- not confirmed 'Success' in the Crossref diagnostic")
            continue

        endpoint_type = 'wp/v2/sfwd-courses' if row['Type'] == 'Publication' else 'wp/v2/sfwd-lessons'
        wp_id = row['WordPress ID']
        try:
            resp = client.post(f"{endpoint_type}/{wp_id}", {'acf': {'pi_doi': doi}})
            actual = resp.get('acf', {}).get('pi_doi')
            ok = actual == doi
            results.append({'doi': doi, 'wp_id': wp_id, 'ok': ok})
            logger.info(f"{'OK  ' if ok else 'FAIL'} wrote {doi} -> WordPress id {wp_id}")
        except Exception as e:
            results.append({'doi': doi, 'wp_id': wp_id, 'ok': False, 'error': str(e)})
            logger.error(f"Failed to write {doi} to WordPress id {wp_id}: {e}")

    return results
