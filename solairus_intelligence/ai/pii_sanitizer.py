"""
PII Sanitization Layer
Removes personally identifiable information and client-specific data before sending to external AI APIs
"""

import logging
import re
from typing import List, Dict
from solairus_intelligence.core.processor import IntelligenceItem, ClientSector

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
        self.client_mapping = client_mapping or self._get_default_client_mapping()
        self.company_patterns = self._build_company_patterns()

    def _get_default_client_mapping(self) -> Dict[ClientSector, Dict]:
        """Get default client mapping from IntelligenceProcessor"""
        from solairus_intelligence.core.processor import IntelligenceProcessor
        processor = IntelligenceProcessor()
        return processor.client_mapping

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


def test_sanitizer():
    """Test the PII sanitization functionality"""
    print("=" * 60)
    print("PII SANITIZER TEST")
    print("=" * 60)

    sanitizer = PIISanitizer()

    # Test 1: Basic text sanitization
    print("\nTest 1: Basic Text Sanitization")
    test_text = "Cisco announced a new data center expansion in partnership with Palantir Technologies."
    sanitized = sanitizer.sanitize_text(test_text)
    print(f"Original:  {test_text}")
    print(f"Sanitized: {sanitized}")

    # Test 2: Case insensitivity
    print("\nTest 2: Case Insensitivity")
    test_text2 = "ICONIQ Capital and iconiq capital both mentioned"
    sanitized2 = sanitizer.sanitize_text(test_text2)
    print(f"Original:  {test_text2}")
    print(f"Sanitized: {sanitized2}")

    # Test 3: Preserve non-client mentions
    print("\nTest 3: Non-Client Companies Preserved")
    test_text3 = "Apple and Microsoft announced new features, while Cisco implemented changes"
    sanitized3 = sanitizer.sanitize_text(test_text3)
    print(f"Original:  {test_text3}")
    print(f"Sanitized: {sanitized3}")

    # Test 4: Intelligence item sanitization
    print("\nTest 4: Intelligence Item Sanitization")
    from solairus_intelligence.core.processor import IntelligenceItem

    test_item = IntelligenceItem(
        raw_content="Cisco technology export restrictions",
        processed_content="US export controls on semiconductor technology impact Palantir's operations",
        category="technology",
        relevance_score=0.85,
        so_what_statement="Technology sector clients like NantWorks face compliance challenges",
        affected_sectors=[ClientSector.TECHNOLOGY]
    )

    sanitized_item = sanitizer.sanitize_intelligence_item(test_item)
    print(f"Original processed_content:  {test_item.processed_content}")
    print(f"Sanitized processed_content: {sanitized_item.processed_content}")
    print(f"Original so_what:            {test_item.so_what_statement}")
    print(f"Sanitized so_what:           {sanitized_item.so_what_statement}")

    print("\n" + "=" * 60)
    print("✓ PII Sanitizer test complete")
    print("=" * 60)


if __name__ == "__main__":
    test_sanitizer()
