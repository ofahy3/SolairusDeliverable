"""
Content blocklist to prevent Solairus contamination in Grainger deliverables.
These terms should NEVER appear in any generated output.
"""

import re
from typing import List

BLOCKED_TERMS = [
    # Client names
    "solairus",
    "solairus aviation",

    # Aviation industry
    "business aviation",
    "private aviation",
    "charter",
    "aircraft management",
    "flight operations",
    "fbo",
    "fixed base operator",
    "part 135",
    "part 91",
    "tail number",
    "n-number",
    "pilot",
    "crew scheduling",
    "hangar",
    "jet fuel",
    "avgas",
    "flight planning",
    "aircraft",
    "aviation",

    # Solairus client sectors
    "high net worth",
    "hnw",
    "uhnw",
    "ultra high net worth",
    "talent mobility",
    "entertainment sector",  # in Solairus context

    # Solairus-specific framing
    "silicon valley dynamics",
    "celebrity travel",
    "executive travel",
    "vip transport",

    # Aviation-specific FRED indicators
    "wjfuelusgulf",
    "kerosene-type jet fuel",
]

BLOCKED_PATTERNS = [
    r"N\d{3,5}[A-Z]{0,2}",  # Aircraft N-numbers like N12345 or N123AB
    r"(?i)solairus",
    r"(?i)aviation\s+client",
    r"(?i)business\s+aviation",
    r"(?i)private\s+aviation",
    r"(?i)charter\s+(flight|service|operator)",
    r"(?i)flight\s+department",
    r"(?i)high[\-\s]net[\-\s]worth",
]


def check_content(text: str) -> List[str]:
    """
    Check text for blocked terms. Returns list of violations found.

    Args:
        text: The text content to check

    Returns:
        List of violation messages, empty if no violations found
    """
    violations = []
    text_lower = text.lower()

    for term in BLOCKED_TERMS:
        if term in text_lower:
            violations.append(f"Blocked term found: '{term}'")

    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, text):
            violations.append(f"Blocked pattern found: '{pattern}'")

    return violations


def is_content_clean(text: str) -> bool:
    """
    Check if text is free from blocked content.

    Args:
        text: The text content to check

    Returns:
        True if no blocked content found, False otherwise
    """
    return len(check_content(text)) == 0


def sanitize_content(text: str) -> str:
    """
    Remove or replace blocked terms in text.
    Note: This is a fallback - content should be clean at source.

    Args:
        text: The text content to sanitize

    Returns:
        Sanitized text with blocked terms removed/replaced
    """
    result = text

    # Replace common aviation terms with MRO equivalents
    replacements = {
        "aviation": "industrial",
        "aircraft": "equipment",
        "flight": "operations",
        "pilot": "operator",
        "charter": "service",
        "jet fuel": "energy costs",
        "fbo": "distributor",
        "solairus": "[CLIENT]",
    }

    for old, new in replacements.items():
        result = re.sub(re.escape(old), new, result, flags=re.IGNORECASE)

    return result
