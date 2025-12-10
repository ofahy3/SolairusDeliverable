"""
PII Sanitization Layer
Removes personally identifiable information and client-specific data before sending to external AI APIs
"""

import logging
import re
from typing import List, Dict

from solairus_intelligence.config.clients import ClientSector, CLIENT_SECTOR_MAPPING
from solairus_intelligence.core.processor import IntelligenceItem

logger = logging.getLogger(__name__)


class PIISanitizer:
    """
    Sanitizes intelligence items by removing client company names and other PII
    before sending data to external AI services
    """

    def __init__(self, client_mapping: Dict[ClientSector, Dict] = None):
        """
        Initialize sanitizer with client mapping data

        Args:
            client_mapping: Dictionary mapping sectors to client data
        """
        # Use centralized config as single source of truth
        self.client_mapping = client_mapping or CLIENT_SECTOR_MAPPING
        self.company_patterns = self._build_company_patterns()

    def _build_company_patterns(self) -> Dict[str, str]:
        """
        Build regex patterns for company name replacement

        Returns:
            Dictionary mapping company names to replacement tokens
        """
        patterns = {}

        for sector, data in self.client_mapping.items():
            companies = data.get('companies', [])
            sector_token = f"[{sector.value.upper()}_CLIENT]"

            for company in companies:
                # Store both exact match and case-insensitive pattern
                patterns[company] = sector_token

        return patterns

    def sanitize_text(self, text: str, audit_log: bool = True) -> str:
        """
        Remove client company names from text

        Args:
            text: Input text to sanitize
            audit_log: If True, log what was sanitized

        Returns:
            Sanitized text with client names replaced
        """
        if not text:
            return text

        sanitized = text
        replacements_made = []

        # Replace company names (case-insensitive)
        for company, token in self.company_patterns.items():
            # Use word boundaries to avoid partial matches
            pattern = re.compile(r'\b' + re.escape(company) + r'\b', re.IGNORECASE)
            matches = pattern.findall(sanitized)

            if matches:
                sanitized = pattern.sub(token, sanitized)
                replacements_made.append(f"{company} → {token}")

        # Log sanitization if requested
        if audit_log and replacements_made:
            logger.info(f"PII Sanitization: {len(replacements_made)} replacements made")
            for replacement in replacements_made:
                logger.debug(f"  - {replacement}")

        return sanitized

    def sanitize_intelligence_item(self, item: IntelligenceItem) -> IntelligenceItem:
        """
        Create a sanitized copy of an intelligence item

        Args:
            item: Original intelligence item

        Returns:
            New intelligence item with sanitized content
        """
        # Create a copy to avoid modifying original
        from dataclasses import replace

        sanitized_item = replace(
            item,
            raw_content=self.sanitize_text(item.raw_content, audit_log=False),
            processed_content=self.sanitize_text(item.processed_content, audit_log=False),
            so_what_statement=self.sanitize_text(item.so_what_statement, audit_log=False),
            category=item.category  # Category is safe
        )

        return sanitized_item

    def sanitize_intelligence_items(self, items: List[IntelligenceItem]) -> List[IntelligenceItem]:
        """
        Sanitize a list of intelligence items

        Args:
            items: List of intelligence items

        Returns:
            List of sanitized intelligence items
        """
        logger.info(f"Sanitizing {len(items)} intelligence items for AI processing")
        sanitized_items = [self.sanitize_intelligence_item(item) for item in items]

        # Log summary
        total_replacements = sum(
            1 for orig, san in zip(items, sanitized_items)
            if orig.processed_content != san.processed_content
        )

        if total_replacements > 0:
            logger.info(f"✓ Sanitized {total_replacements}/{len(items)} items containing PII")
        else:
            logger.info("✓ No PII detected in intelligence items")

        return sanitized_items

    def sanitize_dict(self, data: Dict) -> Dict:
        """
        Sanitize all string values in a dictionary

        Args:
            data: Dictionary to sanitize

        Returns:
            Dictionary with sanitized string values
        """
        sanitized = {}

        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = self.sanitize_text(value, audit_log=False)
            elif isinstance(value, dict):
                sanitized[key] = self.sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    self.sanitize_text(v, audit_log=False) if isinstance(v, str) else v
                    for v in value
                ]
            else:
                sanitized[key] = value

        return sanitized
