"""Base HTTP client with authentication and retry logic."""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)


class WordPressClient:
    """Base client for WordPress REST API."""

    def __init__(self):
        load_dotenv()
        self.base_url = os.getenv('WP_BASE_URL')
        self.username = os.getenv('WP_USERNAME')
        # Strip spaces from Application Password
        password = os.getenv('WP_APP_PASSWORD', '')
        self.password = password.replace(' ', '')

        if not all([self.base_url, self.username, self.password]):
            raise ValueError("Missing WordPress credentials in .env file")

        # Create session with retry strategy
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create session with retry and timeout logic."""
        session = requests.Session()
        session.auth = (self.username, self.password)

        # Retry strategy for transient failures
        retry = Retry(
            total=3,
            backoff_factor=2,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)

        return session

    def get_paginated(self, endpoint: str, params: dict = None) -> list:
        """Fetch all pages of a paginated endpoint.

        Args:
            endpoint: API endpoint path (e.g., 'wp/v2/sfwd-courses')
            params: Query parameters

        Returns:
            List of all items across all pages
        """
        all_items = []
        page = 1

        while True:
            page_params = {**(params or {}), 'page': page, 'per_page': 100}
            url = f"{self.base_url}/wp-json/{endpoint}"

            logger.info(f"Fetching page {page} from {endpoint}")

            try:
                response = self.session.get(
                    url,
                    params=page_params,
                    timeout=30
                )

                # 404 means no more pages
                if response.status_code == 404:
                    logger.info(f"Reached end of pagination at page {page}")
                    break

                response.raise_for_status()
                items = response.json()

                if not items:
                    logger.info("No more items returned")
                    break

                all_items.extend(items)
                logger.info(f"Fetched {len(items)} items from page {page}")

                # Check if more pages exist
                total_pages = int(response.headers.get('X-WP-TotalPages', 1))
                if page >= total_pages:
                    logger.info(f"Reached last page ({total_pages})")
                    break

                page += 1

            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching page {page}: {e}")
                break

        logger.info(f"Total items fetched: {len(all_items)}")
        return all_items

    def get(self, endpoint: str, timeout: int = 30) -> dict:
        """Fetch a single resource.

        Args:
            endpoint: API endpoint path
            timeout: Request timeout in seconds

        Returns:
            JSON response as dictionary
        """
        url = f"{self.base_url}/wp-json/{endpoint}"
        response = self.session.get(url, timeout=timeout)
        response.raise_for_status()
        return response.json()
