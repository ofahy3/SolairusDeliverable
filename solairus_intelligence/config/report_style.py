"""
Solairus Intelligence Report Style Configuration

This module contains the editorial standards and formatting requirements
for generating monthly intelligence reports. These rules ensure output
matches the quality standards expected by the client.
"""

# Style guide version - update when making significant changes
STYLE_GUIDE_VERSION = "1.0.0"

# ============================================================================
# SECTION FORMATTING
# ============================================================================

SECTION_HEADERS = {
    "format": "bold",  # All major section headers must be bold
    "case": "title",  # Subsection titles use Title Case
    "examples": {
        "good": [
            "**EXECUTIVE SUMMARY**",
            "**ECONOMIC INDICATORS FOR BUSINESS AVIATION**",
            "**Taiwan Strait Escalation Risk**",
            "**Middle East Airspace Volatility**",
        ],
        "bad": [
            "EXECUTIVE SUMMARY",  # unbolded
            "**Taiwan Strait escalation risk**",  # sentence case
        ],
    },
}

# ============================================================================
# BOTTOM LINE STRUCTURE
# ============================================================================

BOTTOM_LINE_RULES = {
    "structure": "single_unified_paragraph",
    "lead_sentence": {
        "format": "bold",
        "end_at": "natural_break",  # comma or period
    },
    "content_rules": [
        "Synthesize all regional themes into one cohesive statement",
        "Remove tangential topics not directly relevant to aviation operations",
        "Every topic mentioned MUST have a corresponding Key Findings section",
    ],
    "avoid": [
        "Multiple paragraphs covering unrelated topics",
        'Generic "high-end coercive scenario" language',
        "Topics without corresponding Key Findings sections",
    ],
    "example": (
        "**Ergo assesses that a Taiwan Strait blockade would trigger immediate "
        "closure of Taiwan FIR and adjacent corridors,** forcing rapid rerouting "
        "of Northeast Asia-Southeast Asia and Asia-Australia traffic, while Middle "
        "East and European operations face persistent flight planning friction from "
        "tactical airspace adjustments and rising regulatory overhead."
    ),
}

# ============================================================================
# KEY FINDINGS STRUCTURE
# ============================================================================

KEY_FINDINGS_RULES = {
    "opening_paragraph": {
        "lead_sentence_format": "bold",
        "remove_prefix": True,  # Remove "Ergo assesses that" from bold start
        "end_bold_at": "natural_break",
        "transition_required": True,  # Must include client-specific transition
    },
    "transition_examples": {
        "good": [
            "Ergo assesses three implications for Solairus:",
            "Two trends Ergo is monitoring for Solairus:",
        ],
        "bad": [
            "Jumping directly into bullets without context",
        ],
    },
    "bullet_format": {
        "style": "dash",  # Use dash bullets, not blockquote
        "lead_phrase": "bold_with_period",
        "punctuation": "periods_not_semicolons",
    },
    "bullet_examples": {
        "good": [
            "-   **Route disruption.** Rerouting via Philippine Sea...",
            "-   **Cyber degradation.** Operators should assume...",
            "-   **EU AI Act compliance overhead.** Flight departments...",
        ],
        "bad": [
            "> • Pacific route disruption would require rerouting...",
            "- Route disruption: operators should...",  # not bold
        ],
    },
}

# ============================================================================
# INTERNAL NAMING - REMOVE
# ============================================================================

REMOVE_INTERNAL_NAMES = {
    "scenario_names": [
        "Strait Jacket",
        "Tinderboxed",
        "Abraham Discords",
        "Fortress EU",
    ],
    "remove_patterns": [
        r'"[A-Z][a-z]+ [A-Z][a-z]+" scenario',
        r"\(\d+% probability as of.*?\)",
    ],
    "replace_with": {
        "scenario reference": "In the event of...",
        "unlikely scenario": "While unlikely...",
    },
}

# ============================================================================
# WORD CHOICE
# ============================================================================

PREFERRED_TERMINOLOGY = {
    "elevated security thresholds": "higher security thresholds",
    "ceasing Taiwan Strait traffic entirely": "causing Taiwan Strait traffic to cease entirely",
    "US-UK strikes have failed to eliminate": "prove resilient to US-UK strikes",
    "sustaining threats to": "maintaining threats to",
    "hardening internal travel restrictions": "harden internal rules against non-essential trips",
}

AVOID_VERBOSE = [
    "Ergo assesses that... at the start of every section",
    "blockade-type scenarios",  # just say "blockade scenarios"
    "the most likely path to episodic airspace disruption rather than sustained regional closure",
]

# ============================================================================
# RISK CALIBRATION
# ============================================================================

PROBABILITY_FRAMING = {
    "base_case": [
        "remains the most probable trajectory",
        "Ergo expects",
    ],
    "plausible_not_expected": [
        "could occur if",
        "in the event of",
        "would result in",
    ],
    "unlikely_but_possible": [
        "While unlikely",
        "In the unlikely event",
        "remote but consequential",
    ],
    "tail_risk": [
        "In an extreme scenario",
        "worst-case contingency",
    ],
}

RISK_RULES = [
    "Lead with the most probable trajectory, not the worst case",
    "Explicitly flag low-probability scenarios as unlikely",
    "Use contingency framing, not preparation imperatives for unlikely events",
    "Reserve 'prepare for' and 'require' language for likely scenarios",
]

# ============================================================================
# ECONOMIC INDICATORS TABLE
# ============================================================================

ECONOMIC_INDICATOR_FORMAT = {
    "include_units": True,
    "examples": {
        "good": [
            "Jet Fuel (USD/gal)",
            "Crude Oil (USD/bbl)",
        ],
        "bad": [
            "Jet Fuel",  # no units
            "Oil/Energy",  # vague
        ],
    },
}

# ============================================================================
# AI PROMPT SYSTEM MESSAGE
# ============================================================================

REPORT_STYLE_SYSTEM_MESSAGE = """You are generating content for a Solairus Intelligence Report.

CRITICAL STYLE REQUIREMENTS:

1. SECTION HEADERS
   - All major headers must be bold: **EXECUTIVE SUMMARY**
   - Subsection titles use Title Case: **Taiwan Strait Escalation Risk**

2. BOTTOM LINE
   - Single unified paragraph (not multiple separate paragraphs)
   - Lead with bold assessment: **Ergo assesses that X,** followed by supporting text
   - Every topic mentioned MUST have a corresponding Key Findings section

3. KEY FINDINGS
   - Bold lead assessment WITHOUT "Ergo assesses that" prefix
   - End bold at natural break (comma or period)
   - Include client transition: "Ergo assesses three implications for Solairus:"
   - Bullets use dash format with bold lead phrase + period:
     -   **Route disruption.** Description here...

4. REMOVE INTERNAL NAMES
   - No scenario codenames: "Strait Jacket", "Tinderboxed", etc.
   - No probability percentages: "(55% probability as of...)"
   - Use: "In the event of...", "While unlikely..."

5. RISK CALIBRATION (CRITICAL)
   - Lead with MOST PROBABLE trajectory, not worst case
   - Explicitly flag unlikely scenarios: "While unlikely..."
   - Use conditional framing for tail risks, not "prepare for" language
   - Reserve "require" and "prepare for" for LIKELY scenarios only

6. WORD CHOICE
   - "elevated security thresholds" not "higher security thresholds"
   - Use periods within bullets, not semicolons
   - Vary sentence structure - don't start every sentence with "Ergo assesses"

7. ECONOMIC INDICATORS
   - Include units: "Jet Fuel (USD/gal)", "Crude Oil (USD/bbl)"
"""

# ============================================================================
# VALIDATION CHECKLIST
# ============================================================================

FINAL_CHECKLIST = [
    "All major section headers are bold",
    "Subsection titles use Title Case",
    "Bottom Line is a single unified paragraph with bold lead sentence",
    "Every topic in Bottom Line has a corresponding Key Findings section",
    "Key Finding lead assessments are bold (without 'Ergo assesses that' prefix)",
    "Client-specific transition sentences precede all bullet lists",
    "Bullets use dash format with bold lead phrases",
    "No internal scenario names or probability percentages",
    "Economic indicators include units (USD/gal, USD/bbl)",
    "No semicolons within bullet points - use periods",
    "All content is directly relevant to business aviation operations",
    "Low-probability scenarios are explicitly flagged as unlikely",
    "'Prepare for'/'require' language reserved for likely scenarios",
]
