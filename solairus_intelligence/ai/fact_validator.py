"""
Fact Validation Layer
Detects hallucinations and unsupported claims in AI-generated content
"""

import logging
import re
from typing import List, Set, Tuple

from solairus_intelligence.core.processor import IntelligenceItem

logger = logging.getLogger(__name__)


class FactValidator:
    """
    Validates that AI-generated content is grounded in source intelligence items
    Detects potential hallucinations and fabricated data
    """

    def __init__(self):
        self.factual_patterns = self._build_factual_patterns()

    def _build_factual_patterns(self) -> dict:
        """
        Build regex patterns for extracting factual claims

        Returns:
            Dictionary of pattern types and their regexes
        """
        return {
            "percentages": re.compile(r"\d+(\.\d+)?%"),
            "dollar_amounts": re.compile(
                r"\$\d+(\.\d+)?\s*(billion|million|trillion)?", re.IGNORECASE
            ),
            "dates": re.compile(
                r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b|\b\d{1,2}/\d{1,2}/\d{2,4}\b|\bQ[1-4]\s+\d{4}\b"
            ),
            "numbers": re.compile(r"\b\d{1,3}(,\d{3})*(\.\d+)?\b"),
            "specific_countries": re.compile(
                r"\b(United States|China|Russia|EU|European Union|Japan|India|Saudi Arabia|Iran|Israel)\b",
                re.IGNORECASE,
            ),
            "specific_companies": re.compile(
                r"\b[A-Z][a-z]+\s+(Technologies|Corporation|Inc\.|Ltd\.|Capital|Group|Partners)\b"
            ),
        }

    def extract_factual_claims(self, text: str) -> Set[str]:
        """
        Extract factual claims from AI-generated text

        Args:
            text: AI-generated text to analyze

        Returns:
            Set of extracted factual claims
        """
        claims = set()

        # Extract all factual elements
        for claim_type, pattern in self.factual_patterns.items():
            matches = pattern.findall(text)
            if matches:
                # Flatten tuples from regex groups
                for match in matches:
                    if isinstance(match, tuple):
                        claim = " ".join(str(m) for m in match if m).strip()
                    else:
                        claim = str(match).strip()

                    if claim:
                        claims.add(f"{claim_type}:{claim}")

        return claims

    def validate_ai_output(
        self, ai_text: str, source_items: List[IntelligenceItem], strict: bool = True
    ) -> Tuple[bool, List[str]]:
        """
        Validate that AI output is supported by source intelligence items

        Args:
            ai_text: AI-generated text to validate
            source_items: Source intelligence items that AI should be based on
            strict: If True, require all specific claims to be supported

        Returns:
            Tuple of (is_valid, list_of_unsupported_claims)
        """
        # Extract claims from AI output
        ai_claims = self.extract_factual_claims(ai_text)

        if not ai_claims:
            # No specific factual claims - generally safe analytical text
            logger.debug("No specific factual claims detected in AI output")
            return True, []

        # Build corpus of source content
        source_corpus = " ".join(
            [
                item.processed_content + " " + item.raw_content + " " + item.so_what_statement
                for item in source_items
            ]
        ).lower()

        # Check each claim
        unsupported_claims = []

        for claim in ai_claims:
            claim_type, claim_value = claim.split(":", 1)
            claim_lower = claim_value.lower()

            # Skip very common numbers that might appear in general language
            if claim_type == "numbers" and len(claim_value) <= 2:
                continue

            # Check if claim appears in source corpus
            if claim_lower not in source_corpus:
                unsupported_claims.append(claim)
                logger.warning(f"Unsupported claim detected: {claim_type} = {claim_value}")

        # Determine validity
        if strict:
            is_valid = len(unsupported_claims) == 0
        else:
            # Allow up to 20% unsupported claims in lenient mode
            threshold = len(ai_claims) * 0.2
            is_valid = len(unsupported_claims) <= threshold

        if not is_valid:
            logger.warning(
                f"AI output validation FAILED: {len(unsupported_claims)} unsupported claims"
            )
        else:
            logger.info(f"AI output validation PASSED: All {len(ai_claims)} claims supported")

        return is_valid, unsupported_claims

    def validate_executive_summary(
        self, summary_dict: dict, source_items: List[IntelligenceItem]
    ) -> Tuple[bool, dict]:
        """
        Validate an executive summary dictionary structure

        Args:
            summary_dict: Dictionary with 'bottom_line', 'key_findings', 'watch_factors'
            source_items: Source intelligence items

        Returns:
            Tuple of (is_valid, validation_report)
        """
        validation_report = {
            "bottom_line": {"valid": True, "unsupported_claims": []},
            "key_findings": {"valid": True, "unsupported_claims": []},
            "watch_factors": {"valid": True, "unsupported_claims": []},
            "overall_valid": True,
        }

        for section_name in ["bottom_line", "key_findings", "watch_factors"]:
            section_items = summary_dict.get(section_name, [])

            if not section_items:
                continue

            # Combine all items in section - handle both string items and structured dicts
            text_parts = []
            for item in section_items:
                if isinstance(item, str):
                    text_parts.append(item)
                elif isinstance(item, dict):
                    # Handle structured key findings with subheader, content, bullets
                    if "content" in item:
                        text_parts.append(item.get("subheader", ""))
                        text_parts.append(item.get("content", ""))
                        text_parts.extend(item.get("bullets", []))
                    # Handle structured watch factors with indicator, what, why
                    elif "indicator" in item:
                        text_parts.append(item.get("indicator", ""))
                        text_parts.append(item.get("what_to_watch", ""))
                        text_parts.append(item.get("why_it_matters", ""))
            section_text = " ".join(text_parts)

            # Validate
            is_valid, unsupported = self.validate_ai_output(section_text, source_items, strict=True)

            validation_report[section_name]["valid"] = is_valid
            validation_report[section_name]["unsupported_claims"] = unsupported

            if not is_valid:
                validation_report["overall_valid"] = False
                logger.error(f"Executive Summary {section_name} validation FAILED")

        return validation_report["overall_valid"], validation_report

    def check_for_prohibited_content(self, text: str) -> Tuple[bool, List[str]]:
        """
        Check for prohibited content patterns that indicate hallucination

        Args:
            text: Text to check

        Returns:
            Tuple of (is_safe, list_of_violations)
        """
        violations = []

        # Prohibited patterns indicating fabrication
        prohibited_patterns = [
            (
                r"I believe|I think|In my opinion|From my perspective",
                "First-person language detected",
            ),
            (r"Based on my analysis of|My assessment shows", "Personal assessment language"),
            (
                r"According to sources not provided|External research indicates",
                "Reference to unavailable sources",
            ),
            (
                r"It is unclear|Information not available|Data missing",
                "Acknowledgment of missing data (acceptable)",
            ),
        ]

        for pattern, violation_type in prohibited_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                # Exception: "Information not available" is actually good (honest)
                if "Information not available" in violation_type:
                    continue

                violations.append(violation_type)
                logger.warning(f"Prohibited content detected: {violation_type}")

        is_safe = len(violations) == 0
        return is_safe, violations
