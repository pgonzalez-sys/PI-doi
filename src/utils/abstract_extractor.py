"""Abstract extraction utilities."""

import re
from html.parser import HTMLParser
from typing import Optional


class HTMLTextExtractor(HTMLParser):
    """Extract plain text from HTML."""

    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.current_tag = None

    def handle_data(self, data):
        """Handle text data."""
        text = data.strip()
        if text:
            self.text_parts.append(text)

    def handle_starttag(self, tag, attrs):
        """Handle opening tags."""
        self.current_tag = tag
        # Add space before block elements
        if tag in ['p', 'div', 'li', 'br']:
            self.text_parts.append(' ')

    def get_text(self) -> str:
        """Get extracted text."""
        text = ' '.join(self.text_parts)
        # Clean up multiple spaces
        text = re.sub(r'\s+', ' ', text)
        return text.strip()


def extract_key_points(html_content: str) -> str:
    """Extract key points from HTML bullet list.

    Args:
        html_content: HTML content with bullet points

    Returns:
        Plain text with bullet points formatted
    """
    if not html_content:
        return ''

    # Parse HTML to extract list items
    extractor = HTMLTextExtractor()
    extractor.feed(html_content)
    text = extractor.get_text()

    # Format as paragraph (Crossref prefers plain text abstracts)
    return text


def extract_abstract_from_content(html_content: str, max_words: int = 250) -> str:
    """Extract abstract from HTML content.

    Takes the first few sentences up to max_words.
    Crossref recommends abstracts of 200-300 words.

    Args:
        html_content: HTML content to extract from
        max_words: Maximum number of words

    Returns:
        Plain text abstract
    """
    if not html_content:
        return ''

    # Remove HTML tags
    extractor = HTMLTextExtractor()
    extractor.feed(html_content)
    text = extractor.get_text()

    # Split into sentences (basic sentence detection)
    sentences = re.split(r'(?<=[.!?])\s+', text)

    # Build abstract up to max_words
    abstract_parts = []
    word_count = 0

    for sentence in sentences:
        sentence_words = sentence.split()
        if word_count + len(sentence_words) <= max_words:
            abstract_parts.append(sentence)
            word_count += len(sentence_words)
        else:
            # Add partial sentence if needed
            remaining_words = max_words - word_count
            if remaining_words > 0:
                partial = ' '.join(sentence_words[:remaining_words]) + '...'
                abstract_parts.append(partial)
            break

    return ' '.join(abstract_parts)


def get_abstract(
    key_points: Optional[str],
    content: Optional[str],
    has_sections: bool = False
) -> str:
    """Get abstract using priority logic.

    Priority:
    1. Key points (if available) - preferred for all content
    2. Extract from content (fallback)

    Args:
        key_points: HTML key points field
        content: HTML content field
        has_sections: Whether this is a publication with sections

    Returns:
        Abstract text
    """
    # Try key points first
    if key_points:
        abstract = extract_key_points(key_points)
        if abstract:
            return abstract

    # Fallback to content extraction
    if content:
        return extract_abstract_from_content(content, max_words=250)

    return ''
