"""
AI Content Generation Layer
Provides AI-enhanced writing for Executive Summaries and "So What" statements
with security, validation, and graceful degradation
"""

import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from mro_intelligence.ai.fact_validator import FactValidator
from mro_intelligence.ai.pii_sanitizer import PIISanitizer
from mro_intelligence.config.report_style import REPORT_STYLE_SYSTEM_MESSAGE
from mro_intelligence.core.processor import IntelligenceItem

logger = logging.getLogger(__name__)


@dataclass
class AIConfig:
    """Configuration for AI generation"""

    api_key: str
    model: str = "claude-opus-4-5-20251101"
    enabled: bool = True
    max_tokens: int = 4000
    temperature: float = 0.3  # Lower temperature for more consistent, factual output
    timeout: int = 60  # seconds
    max_retries: int = 2


class AIUsageTracker:
    """Track AI API usage and costs"""

    def __init__(self):
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_requests = 0
        self.total_cost = 0.0
        self.failed_requests = 0

    def log_request(self, input_tokens: int, output_tokens: int, success: bool = True):
        """Log an API request"""
        self.total_requests += 1

        if success:
            self.total_input_tokens += input_tokens
            self.total_output_tokens += output_tokens

            # Claude Opus 4 pricing: $15/MTok input, $75/MTok output
            self.total_cost += input_tokens / 1_000_000 * 15.0 + output_tokens / 1_000_000 * 75.0
        else:
            self.failed_requests += 1

    def get_summary(self) -> Dict:
        """Get usage summary"""
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.total_requests - self.failed_requests,
            "failed_requests": self.failed_requests,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cost_usd": round(self.total_cost, 4),
            "avg_input_tokens": self.total_input_tokens
            // max(1, self.total_requests - self.failed_requests),
            "avg_output_tokens": self.total_output_tokens
            // max(1, self.total_requests - self.failed_requests),
        }


class SecureAIGenerator:
    """
    AI content generator with security, validation, and graceful degradation

    Features:
    - PII sanitization before external API calls
    - Fact validation to detect hallucinations
    - Graceful fallback to template system on failure
    - Usage tracking and cost monitoring
    - Rate limiting
    """

    def __init__(self, config: Optional[AIConfig] = None):
        """
        Initialize AI generator

        Args:
            config: AI configuration (uses environment variables if not provided)
        """
        self.config = config or self._load_config_from_env()
        self.sanitizer = PIISanitizer()
        self.validator = FactValidator()
        self.usage_tracker = AIUsageTracker()

        # Initialize Anthropic client if enabled
        self.client = None
        if self.config.enabled:
            try:
                from anthropic import AsyncAnthropic

                self.client = AsyncAnthropic(api_key=self.config.api_key)
                logger.info(f"✓ AI generation enabled with model: {self.config.model}")
            except ImportError:
                logger.error("anthropic package not installed - AI generation disabled")
                self.config.enabled = False
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic client: {e}")
                self.config.enabled = False

    def _load_config_from_env(self) -> AIConfig:
        """Load AI configuration from environment variables"""
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        enabled = os.getenv("AI_ENABLED", "true").lower() == "true"
        model = os.getenv("AI_MODEL", "claude-opus-4-5-20251101")

        if not api_key and enabled:
            logger.warning("ANTHROPIC_API_KEY not set - AI generation disabled")
            enabled = False

        return AIConfig(api_key=api_key, model=model, enabled=enabled)

    async def generate_executive_summary(
        self, items: List[IntelligenceItem], fallback_generator=None
    ) -> Dict[str, List[str]]:
        """
        Generate Executive Summary using AI with validation and fallback

        Args:
            items: Intelligence items to synthesize
            fallback_generator: Function to call if AI generation fails

        Returns:
            Dictionary with 'bottom_line', 'key_findings', 'watch_factors'
        """
        if not self.config.enabled or not self.client:
            logger.info("AI generation disabled - using template fallback")
            return fallback_generator(items) if fallback_generator else {}

        logger.info("Generating Executive Summary with AI...")

        # Step 1: Sanitize intelligence items
        sanitized_items = self.sanitizer.sanitize_intelligence_items(items)

        # Step 2: Prepare prompt
        prompt = self._build_executive_summary_prompt(sanitized_items)

        # Step 3: Call AI
        try:
            ai_response = await self._call_claude_api(prompt)

            if not ai_response:
                logger.warning("AI returned empty response - using template fallback")
                return fallback_generator(items) if fallback_generator else {}

            # Step 4: Parse response
            summary_dict = self._parse_executive_summary_response(ai_response)

            # Step 5: Validate for hallucinations
            is_valid, validation_report = self.validator.validate_executive_summary(
                summary_dict, items  # Validate against ORIGINAL items (not sanitized)
            )

            if not is_valid:
                logger.error("AI output failed validation - using template fallback")
                logger.error(f"Validation report: {validation_report}")
                return fallback_generator(items) if fallback_generator else {}

            logger.info("✓ AI-generated Executive Summary validated successfully")
            return summary_dict

        except Exception as e:
            logger.error(f"AI generation failed: {e}")
            return fallback_generator(items) if fallback_generator else {}

    async def generate_so_what_statement(
        self, item: IntelligenceItem, fallback_generator=None
    ) -> str:
        """
        Generate "So What" statement using AI with validation

        Args:
            item: Intelligence item
            fallback_generator: Function to call if AI generation fails

        Returns:
            Generated "So What" statement
        """
        if not self.config.enabled or not self.client:
            return fallback_generator(item) if fallback_generator else ""

        # Sanitize
        sanitized_item = self.sanitizer.sanitize_intelligence_item(item)

        # Build prompt
        prompt = self._build_so_what_prompt(sanitized_item)

        # Call AI
        try:
            ai_response = await self._call_claude_api(prompt, max_tokens=500)

            if not ai_response:
                return fallback_generator(item) if fallback_generator else ""

            # Validate
            is_valid, unsupported = self.validator.validate_ai_output(
                ai_response, [item], strict=False  # Lenient for "So What"
            )

            if not is_valid:
                logger.warning("'So What' statement validation failed - using fallback")
                return fallback_generator(item) if fallback_generator else ""

            return ai_response.strip()

        except Exception as e:
            logger.error(f"AI 'So What' generation failed: {e}")
            return fallback_generator(item) if fallback_generator else ""

    async def _call_claude_api(
        self, prompt: str, max_tokens: Optional[int] = None
    ) -> Optional[str]:
        """
        Call Claude API with error handling and retries

        Args:
            prompt: The prompt to send
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text or None on failure
        """
        if not self.client:
            return None

        max_tokens = max_tokens or self.config.max_tokens
        retries = 0

        while retries <= self.config.max_retries:
            try:
                logger.debug(
                    f"Calling Claude API (attempt {retries + 1}/{self.config.max_retries + 1})"
                )

                response = await asyncio.wait_for(
                    self.client.messages.create(
                        model=self.config.model,
                        max_tokens=max_tokens,
                        temperature=self.config.temperature,
                        messages=[{"role": "user", "content": prompt}],
                    ),
                    timeout=self.config.timeout,
                )

                # Extract text from response - only TextBlocks have .text
                first_block = response.content[0]
                text = first_block.text if hasattr(first_block, "text") else str(first_block)

                # Log usage
                self.usage_tracker.log_request(
                    input_tokens=response.usage.input_tokens,
                    output_tokens=response.usage.output_tokens,
                    success=True,
                )

                logger.debug(
                    f"AI API call successful: {response.usage.input_tokens} in, {response.usage.output_tokens} out"
                )

                return text

            except asyncio.TimeoutError:
                logger.warning(f"AI API timeout (attempt {retries + 1})")
                retries += 1

            except Exception as e:
                logger.error(f"AI API error: {type(e).__name__}: {str(e)}")
                self.usage_tracker.log_request(0, 0, success=False)
                retries += 1

            if retries <= self.config.max_retries:
                await asyncio.sleep(2**retries)  # Exponential backoff

        return None

    def _build_executive_summary_prompt(self, items: List[IntelligenceItem]) -> str:
        """Build prompt for Executive Summary generation"""

        # Select top 20 items by composite score
        top_items = sorted(items, key=lambda x: x.relevance_score * x.confidence, reverse=True)[:20]

        # Format intelligence items
        items_text = []
        for i, item in enumerate(top_items, 1):
            # Handle sectors that may be ClientSector enums or strings/dicts
            sectors = []
            for s in item.affected_sectors:
                if hasattr(s, "value"):
                    sectors.append(s.value)
                elif isinstance(s, dict):
                    sectors.append(s.get("name", str(s)))
                else:
                    sectors.append(str(s))

            items_text.append(
                f"[ITEM {i}]\n"
                f"Content: {item.processed_content}\n"
                f"Source Type: {item.source_type}\n"
                f"Relevance: {item.relevance_score:.2f}\n"
                f"Sectors: {', '.join(sectors)}\n"
            )

        intelligence_block = "\n".join(items_text)

        prompt = f"""{REPORT_STYLE_SYSTEM_MESSAGE}

You are writing the Executive Summary for a monthly intelligence report for Grainger, a leading distributor of MRO (Maintenance, Repair & Operations) supplies serving manufacturing, construction, energy, and facilities management sectors.

INTELLIGENCE ITEMS (Top 20 by relevance):
{intelligence_block}

TASK: Generate an Executive Summary with these three sections:

1. BOTTOM LINE: A SINGLE UNIFIED PARAGRAPH (not bullet points)
   - Lead with bold assessment ending at natural break: **Ergo assesses that X,** followed by synthesis
   - Synthesize ALL major sector themes (Manufacturing, Construction, Energy) into ONE cohesive paragraph
   - CRITICAL: Only include topics that will have corresponding Key Findings sections
   - Do NOT include tangential topics unless directly MRO-relevant

2. KEY FINDINGS (3-5 sections): Each finding needs proper structure
   - SUBHEADER: Title Case theme title (e.g., **Manufacturing Sector Outlook**)
   - LEAD SENTENCE: Bold the core assessment WITHOUT "Ergo assesses that" prefix
   - TRANSITION: Include "Ergo assesses X implications for Grainger:" before bullets
   - BULLETS: Use dash format with bold lead phrase + period:
     -   **Supply disruption.** Description of impact...

3. WATCH FACTORS (at least 3 items): Forward-looking indicators
   - INDICATOR: Short name with units where applicable
   - WHAT TO WATCH: Specific metric or event
   - WHY IT MATTERS: MRO demand impact

RISK CALIBRATION (CRITICAL):
- Lead with MOST PROBABLE trajectory, not worst case
- Explicitly flag unlikely scenarios: "While unlikely...", "In the unlikely event..."
- Use conditional framing for tail risks: "would result in" not "requires preparation for"
- Reserve "prepare for" and "require" language for LIKELY scenarios only
- Do NOT present worst-case scenarios as baseline planning assumptions

STRICT RULES:
- Only use facts from the intelligence items provided above
- Do not invent data, predictions, dates, or percentages not in source items
- Remove internal scenario names or codenames
- Remove probability percentages like "(55% probability as of...)"
- Use periods within bullets, not semicolons
- Vary sentence structure - don't start every sentence with "Ergo assesses"

FORMAT YOUR RESPONSE EXACTLY AS:

BOTTOM LINE:
**[Bold lead assessment ending at comma or period,]** followed by synthesized paragraph covering all themes that will appear in Key Findings below.

KEY FINDINGS:

[SUBHEADER: Theme Title In Title Case]
**[Bold lead assessment without "Ergo assesses that" prefix.]** Supporting analysis with evidence. Ergo assesses X implications for Grainger:
[BULLET: **Lead phrase.** Supporting detail with periods not semicolons.]
[BULLET: **Lead phrase.** Supporting detail.]

[SUBHEADER: Second Theme Title]
**[Bold lead assessment.]** Supporting analysis. Two trends Ergo is monitoring for Grainger:
[BULLET: **Lead phrase.** Supporting detail.]
[BULLET: **Lead phrase.** Supporting detail.]

[SUBHEADER: Third Theme Title]
**[Bold lead assessment.]** Supporting analysis. Ergo assesses X implications:
[BULLET: **Lead phrase.** Supporting detail.]
[BULLET: **Lead phrase.** Supporting detail.]

WATCH FACTORS:

[INDICATOR: Short indicator name with units]
[WHAT: What to watch - specific metric or event]
[WHY: Why it matters for MRO demand]

[INDICATOR: Second indicator]
[WHAT: What to watch]
[WHY: Why it matters]

[INDICATOR: Third indicator]
[WHAT: What to watch]
[WHY: Why it matters]
"""

        return prompt

    def _build_so_what_prompt(self, item: IntelligenceItem) -> str:
        """Build prompt for 'So What' statement generation"""

        # Handle sectors that may be ClientSector enums or strings/dicts
        if item.affected_sectors:
            sectors = []
            for s in item.affected_sectors:
                if hasattr(s, "value"):
                    sectors.append(s.value)
                elif isinstance(s, dict):
                    sectors.append(s.get("name", str(s)))
                else:
                    sectors.append(str(s))
            sectors_text = ", ".join(sectors)
        else:
            sectors_text = "general"

        prompt = f"""Generate a concise "So What" statement explaining the MRO market impact of this intelligence item for Grainger.

INTELLIGENCE ITEM:
Category: {item.category}
Content: {item.processed_content}
Affected Sectors: {sectors_text}
Source: {item.source_type}

TASK: Write a 1-2 sentence "So What" statement that explains:
- Why this matters for MRO supply and demand
- Specific impact on affected client sectors (manufacturing, construction, energy, facilities)
- Operational or financial implications for industrial customers

STYLE:
- Actionable and specific (not vague)
- Focus on MRO distributor and industrial customer perspective
- Professional, analytical tone
- Example: "Rising steel prices will increase maintenance costs for manufacturing equipment by 10-15%, requiring procurement adjustments for spare parts."

STRICT RULES:
- Only use information from the content above
- Do not invent statistics or specific numbers not mentioned
- If no specific impact can be determined, describe general implications

Generate ONLY the "So What" statement (no labels, no extra text):
"""

        return prompt

    def _parse_executive_summary_response(self, ai_response: str) -> Dict[str, List[Any]]:
        """Parse AI response into structured executive summary with new format support"""

        result: Dict[str, List[Any]] = {"bottom_line": [], "key_findings": [], "watch_factors": []}

        current_section = None
        lines = ai_response.strip().split("\n")

        # For structured key findings
        current_finding = None

        # For structured watch factors
        current_watch_factor = None

        for line in lines:
            line = line.strip()

            if not line:
                continue

            # Detect section headers
            if "BOTTOM LINE" in line.upper():
                current_section = "bottom_line"
                current_finding = None
                current_watch_factor = None
                continue
            elif "KEY FINDING" in line.upper():
                current_section = "key_findings"
                current_finding = None
                current_watch_factor = None
                continue
            elif "WATCH FACTOR" in line.upper():
                current_section = "watch_factors"
                current_finding = None
                current_watch_factor = None
                continue

            # Parse structured Key Findings
            if current_section == "key_findings":
                if line.startswith("[SUBHEADER:"):
                    # Save previous finding if exists
                    if current_finding and current_finding.get("content"):
                        result["key_findings"].append(current_finding)
                    # Start new finding
                    subheader = line.replace("[SUBHEADER:", "").rstrip("]").strip()
                    bullets_list: List[str] = []
                    current_finding = {
                        "subheader": subheader,
                        "content": "",
                        "bullets": bullets_list,
                    }
                elif line.startswith("[CONTENT:") and current_finding:
                    content = line.replace("[CONTENT:", "").rstrip("]").strip()
                    current_finding["content"] = content
                elif line.startswith("[BULLET:") and current_finding:
                    bullet = line.replace("[BULLET:", "").rstrip("]").strip()
                    bullets = current_finding.get("bullets")
                    if isinstance(bullets, list):
                        bullets.append(bullet)
                elif line.startswith("-") or line.startswith("•"):
                    # Legacy format bullet
                    statement = line.lstrip("- •").strip()
                    if statement:
                        if current_finding:
                            bullets = current_finding.get("bullets")
                            if isinstance(bullets, list):
                                bullets.append(statement)
                        else:
                            # Legacy format - just a string
                            result["key_findings"].append(statement)
                continue

            # Parse structured Watch Factors
            if current_section == "watch_factors":
                if line.startswith("[INDICATOR:"):
                    # Save previous factor if exists
                    if current_watch_factor and current_watch_factor.get("indicator"):
                        result["watch_factors"].append(current_watch_factor)
                    # Start new factor
                    indicator = line.replace("[INDICATOR:", "").rstrip("]").strip()
                    current_watch_factor = {
                        "indicator": indicator,
                        "what_to_watch": "",
                        "why_it_matters": "",
                    }
                elif line.startswith("[WHAT:") and current_watch_factor:
                    what = line.replace("[WHAT:", "").rstrip("]").strip()
                    current_watch_factor["what_to_watch"] = what
                elif line.startswith("[WHY:") and current_watch_factor:
                    why = line.replace("[WHY:", "").rstrip("]").strip()
                    current_watch_factor["why_it_matters"] = why
                elif line.startswith("-") or line.startswith("•"):
                    # Legacy format
                    statement = line.lstrip("- •").strip()
                    if statement:
                        result["watch_factors"].append(statement)
                continue

            # Parse Bottom Line (simple bullet format)
            if current_section == "bottom_line":
                if line.startswith("-") or line.startswith("•"):
                    statement = line.lstrip("- •").strip()
                    if statement:
                        result["bottom_line"].append(statement)

        # Save final finding and watch factor if they exist
        if current_finding and current_finding.get("content"):
            result["key_findings"].append(current_finding)
        if current_watch_factor and current_watch_factor.get("indicator"):
            result["watch_factors"].append(current_watch_factor)

        return result

    def get_usage_summary(self) -> Dict:
        """Get AI usage summary"""
        return self.usage_tracker.get_summary()
