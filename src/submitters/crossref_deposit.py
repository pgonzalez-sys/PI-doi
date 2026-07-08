"""Submit a Crossref batch XML via the official HTTPS POST deposit API.

Docs: https://www.crossref.org/documentation/register-maintain-records/direct-deposit-xml/https-post/

This replaces manually logging into the Crossref admin portal and uploading the
file by hand. It requires depositor credentials (CROSSREF_LOGIN_ID /
CROSSREF_LOGIN_PASSWORD in .env) -- these are Crossref account credentials, not
your WordPress or GitHub login. Get them from your Crossref account settings if
you don't have them handy.

Crossref processes submissions asynchronously: this call only returns an
immediate acknowledgment that the file was received, NOT whether each DOI
succeeded. The full diagnostic report (per-DOI success/failure) arrives later
via email or the admin portal's submission log -- see diagnostic_parser.py.
"""

import os
import logging
import requests

logger = logging.getLogger(__name__)

DEPOSIT_URL = "https://doi.crossref.org/servlet/deposit"
TEST_DEPOSIT_URL = "https://test.crossref.org/servlet/deposit"


def submit_batch(xml_path, login_id=None, login_passwd=None, use_test=False, timeout=60):
    """POST a batch XML file to Crossref for deposit.

    Args:
        xml_path: path to the Crossref-format batch XML file
        login_id: Crossref depositor login ID (falls back to CROSSREF_LOGIN_ID env var)
        login_passwd: Crossref depositor password (falls back to CROSSREF_LOGIN_PASSWORD env var)
        use_test: submit to Crossref's TEST system instead of production (for a dry run
            that doesn't actually register real DOIs)
        timeout: request timeout in seconds

    Returns:
        Crossref's immediate acknowledgment text (a simple receipt, not the diagnostic).

    Raises:
        ValueError: if credentials aren't provided or set in the environment.
    """
    login_id = login_id or os.getenv('CROSSREF_LOGIN_ID')
    login_passwd = login_passwd or os.getenv('CROSSREF_LOGIN_PASSWORD')
    if not login_id or not login_passwd:
        raise ValueError(
            "Missing Crossref credentials. Set CROSSREF_LOGIN_ID and "
            "CROSSREF_LOGIN_PASSWORD in .env -- see DOI_GENERATION_INSTRUCTIONS.md "
            "for where to find these in your Crossref account."
        )

    url = TEST_DEPOSIT_URL if use_test else DEPOSIT_URL
    with open(xml_path, 'rb') as f:
        files = {'fname': (os.path.basename(str(xml_path)), f, 'application/xml')}
        data = {
            'operation': 'doMDUpload',
            'login_id': login_id,
            'login_passwd': login_passwd,
        }
        logger.info(f"Submitting {xml_path} to Crossref ({'TEST' if use_test else 'PRODUCTION'} system)")
        resp = requests.post(url, data=data, files=files, timeout=timeout)
        resp.raise_for_status()
        return resp.text
