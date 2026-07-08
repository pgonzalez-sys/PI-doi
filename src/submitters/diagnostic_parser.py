"""Parse a Crossref doi_batch_diagnostic XML report into a plain list of results.

This is the report Crossref sends confirming which DOIs in a submitted batch
actually succeeded (e.g. the one Pamela pastes in from her email after each
submission). Works whether the XML came from the diagnostic-fetch attempt in
cli_full_pipeline.py or was pasted in manually -- same format either way.
"""

from lxml import etree


def parse_diagnostic(xml_text):
    """Parse a <doi_batch_diagnostic> document.

    Args:
        xml_text: the diagnostic XML, as str or bytes.

    Returns:
        dict with submission_id, batch_id, overall status, batch_data summary
        counts, and a list of per-record {doi, status, message} dicts.
    """
    if isinstance(xml_text, str):
        xml_text = xml_text.encode('utf-8')
    root = etree.fromstring(xml_text)

    records = []
    for rec in root.findall('.//record_diagnostic'):
        doi_el = rec.find('doi')
        msg_el = rec.find('msg')
        records.append({
            'doi': doi_el.text.strip() if doi_el is not None and doi_el.text else None,
            'status': rec.get('status'),
            'message': msg_el.text.strip() if msg_el is not None and msg_el.text else None,
        })

    summary = {}
    batch_data = root.find('batch_data')
    if batch_data is not None:
        for child in batch_data:
            summary[child.tag] = child.text

    submission_id_el = root.find('submission_id')
    batch_id_el = root.find('batch_id')

    return {
        'submission_id': submission_id_el.text if submission_id_el is not None else None,
        'batch_id': batch_id_el.text if batch_id_el is not None else None,
        'status': root.get('status'),
        'summary': summary,
        'records': records,
    }
