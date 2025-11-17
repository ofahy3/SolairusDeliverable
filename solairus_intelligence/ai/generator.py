"""
AI Content Generation Layer
Provides AI-enhanced writing for Executive Summaries and "So What" statements
with security, validation, and graceful degradation
"""

import logging
import os
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import asyncio

from solairus_intelligence.core.processor import IntelligenceItem, ClientSector
from solairus_intelligence.ai.pii_sanitizer import PIISanitizer
from solairus_intelligence.ai.fact_validator import FactValidator

logger = logging.getLogger(__name__)

@dataclass
class AIConfig:
    """Configuration for AI generation"""
    api_key: str
    model: str = "claude-opus-4-1-20250805"
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
            self.total_cost += (
                input_tokens / 1_000_000 * 15.0 +
                output_tokens / 1_000_000 * 75.0
            )
        else:
            self.failed_requests += 1

    def get_summary(self) -> Dict:
        """Get usage summary"""
        return {
            'total_requests': self.total_requests,
            'successful_requests': self.total_requests - self.failed_requests,
            'failed_requests': self.failed_requests,
            'total_input_tokens': self.total_input_tokens,
            'total_output_tokens': self.total_output_tokens,
            'total_cost_usd': round(self.total_cost, 4),
            'avg_input_tokens': self.total_input_tokens // max(1, self.total_requests - self.failed_requests),
            'avg_output_tokens': self.total_output_tokens // max(1, self.total_requests - self.failed_requests),
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
        api_key = os.getenv('ANTHROPIC_API_KEY', '')
        enabled = os.getenv('AI_ENABLED', 'true').lower() == 'true'
        model = os.getenv('AI_MODEL', 'claude-opus-4-1-20250805')

        if not api_key and enabled:
            logger.warning("ANTHROPIC_API_KEY not set - AI generation disabled")
            enabled = False

        return AIConfig(
            api_key=api_key,
            model=model,
            enabled=enabled
        )

    async def generate_executive_summary(
        self,
        items: List[IntelligenceItem],
        fallback_generator=None
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
        self,
        item: IntelligenceItem,
        fallback_generator=None
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
                logger.warning(f"'So What' statement validation failed - using fallback")
                return fallback_generator(item) if fallback_generator else ""

            return ai_response.strip()

        except Exception as e:
            logger.error(f"AI 'So What' generation failed: {e}")
            return fallback_generator(item) if fallback_generator else ""

    async def _call_claude_api(
        self,
        prompt: str,
        max_tokens: Optional[int] = None
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
                logger.debug(f"Calling Claude API (attempt {retries + 1}/{self.config.max_retries + 1})")

                response = await asyncio.wait_for(
                    self.client.messages.create(
                        model=self.config.model,
                        max_tokens=max_tokens,
                        temperature=self.config.temperature,
                        messages=[{
                            "role": "user",
                            "content": prompt
                        }]
                    ),
                    timeout=self.config.timeout
                )

                # Extract text from response
                text = response.content[0].text

                # Log usage
                self.usage_tracker.log_request(
                    input_tokens=response.usage.input_tokens,
                    output_tokens=response.usage.output_tokens,
                    success=True
                )

                logger.debug(f"AI API call successful: {response.usage.input_tokens} in, {response.usage.output_tokens} out")

                return text

            except asyncio.TimeoutError:
                logger.warning(f"AI API timeout (attempt {retries + 1})")
                retries += 1

            except Exception as e:
                logger.error(f"AI API error: {type(e).__name__}: {str(e)}")
                self.usage_tracker.log_request(0, 0, success=False)
                retries += 1

            if retries <= self.config.max_retries:
                await asyncio.sleep(2 ** retries)  # Exponential backoff

        return None

    def _build_executive_summary_prompt(self, items: List[IntelligenceItem]) -> str:
        """Build prompt for Executive Summary generation"""

        # Select top 20 items by composite score
        top_items = sorted(
            items,
            key=lambda x: x.relevance_score * x.confidence,
            reverse=True
        )[:20]

        # Format intelligence items
        items_text = []
        for i, item in enumerate(top_items, 1):
            items_text.append(
                f"[ITEM {i}]\n"
                f"Content: {item.processed_content}\n"
                f"Source Type: {item.source_type}\n"
                f"Relevance: {item.relevance_score:.2f}\n"
                f"Sectors: {', '.join([s.value for s in item.affected_sectors])}\n"
            )

        intelligence_block = '\n'.join(items_text)

        prompt = f"""You are writing the Executive Summary for a monthly intelligence report for Solairus Aviation, a business aviation operator serving high-net-worth clients in technology, finance, real estate, and entertainment sectors.

INTELLIGENCE ITEMS (Top 20 by relevance):
{intelligence_block}

TASK: Generate an Executive Summary with these three sections:

1. BOTTOM LINE (2 items max): Immediate threats or critical developments requiring urgent action
   - Focus on sanctions, export controls, airspace restrictions, compliance risks
   - Lead with analytical judgment, support with evidence
   - Example: "Ergo assesses that [specific development] creates [specific risk] for [affected clients]."

2. KEY FINDINGS (3-5 items): Specific, actionable intelligence judgments
   - Geopolitical developments, economic indicators, regulatory changes
   - Include probability language: "likely", "probable", "expects"
   - Example: "Ergo believes [event] will [outcome] through [timeframe], affecting [sector] clients."

3. WATCH FACTORS (2-3 items): Forward-looking indicators to monitor
   - Emerging trends, signals requiring monitoring
   - Example: "Monitor [indicator] - [reason why it matters for aviation]."

STYLE REQUIREMENTS (Ergo Analytical Voice):
- Lead with judgment, support with evidence
- Use authoritative analytical language: "Ergo assesses...", "Ergo expects...", "Ergo believes..."
- Include specific numbers, dates, timeframes from the intelligence items
- Focus on business aviation operational implications
- Active voice, declarative statements
- Professional, analytical tone (not casual)

STRICT RULES:
- Only use facts from the intelligence items provided above
- Do not invent data, predictions, dates, or percentages not in the source items
- If specific information is missing, use general analytical language without fabricating details
- Do not use first-person language ("I think", "I believe")
- Maintain professional aviation industry terminology

FORMAT YOUR RESPONSE AS:
BOTTOM LINE:
- [Statement 1]
- [Statement 2]

KEY FINDINGS:
- [Finding 1]
- [Finding 2]
- [Finding 3]
- [Finding 4]
- [Finding 5]

WATCH FACTORS:
- [Factor 1]
- [Factor 2]
- [Factor 3]
"""

        return prompt

    def _build_so_what_prompt(self, item: IntelligenceItem) -> str:
        """Build prompt for 'So What' statement generation"""

        sectors_text = ', '.join([s.value for s in item.affected_sectors]) if item.affected_sectors else 'general'

        prompt = f"""Generate a concise "So What" statement explaining the business aviation impact of this intelligence item.

INTELLIGENCE ITEM:
Category: {item.category}
Content: {item.processed_content}
Affected Sectors: {sectors_text}
Source: {item.source_type}

TASK: Write a 1-2 sentence "So What" statement that explains:
- Why this matters for business aviation operations
- Specific impact on affected client sectors
- Operational or financial implications

STYLE:
- Actionable and specific (not vague)
- Focus on aviation operator perspective
- Professional, analytical tone
- Example: "Rising fuel costs will increase operational expenses by 10-15%, requiring pricing adjustments for charter services."

STRICT RULES:
- Only use information from the content above
- Do not invent statistics or specific numbers not mentioned
- If no specific impact can be determined, describe general implications

Generate ONLY the "So What" statement (no labels, no extra text):
"""

        return prompt

    def _parse_executive_summary_response(self, ai_response: str) -> Dict[str, List[str]]:
        """Parse AI response into structured executive summary"""

        result = {
            'bottom_line': [],
            'key_findings': [],
            'watch_factors': []
        }

        current_section = None
        lines = ai_response.strip().split('\n')

        for line in lines:
            line = line.strip()

            if not line:
                continue

            # Detect section headers
            if 'BOTTOM LINE' in line.upper():
                current_section = 'bottom_line'
                continue
            elif 'KEY FINDING' in line.upper():
                current_section = 'key_findings'
                continue
            elif 'WATCH FACTOR' in line.upper():
                current_section = 'watch_factors'
                continue

            # Extract bullet points
            if line.startswith('-') or line.startswith('•'):
                statement = line.lstrip('- •').strip()
                if statement and current_section:
                    result[current_section].append(statement)

        return result

    def get_usage_summary(self) -> Dict:
        """Get AI usage summary"""
        return self.usage_tracker.get_summary()


def test_ai_generator():
    """Test AI generator functionality"""
    print("=" * 60)
    print("AI GENERATOR TEST")
    print("=" * 60)

    # Check if API key is set
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("\n⚠️  ANTHROPIC_API_KEY not set - skipping AI tests")
        print("Set environment variable: export ANTHROPIC_API_KEY=your_key_here")
        print("=" * 60)
        return

    print(f"\n✓ API key configured")

    # Create test intelligence items
    test_items = [
        IntelligenceItem(
            raw_content="US inflation 3.5% Q4",
            processed_content="US inflation rose to 3.5% in Q4 2025, driven by energy costs and supply chain pressures",
            category="economic",
            relevance_score=0.9,
            confidence=0.85,
            so_what_statement="Higher operating costs for aviation",
            affected_sectors=[ClientSector.GENERAL],
            source_type="fred"
        ),
        IntelligenceItem(
            raw_content="China export controls semiconductors",
            processed_content="China imposed new export controls on semiconductor manufacturing equipment, affecting US technology companies",
            category="geopolitical",
            relevance_score=0.88,
            confidence=0.9,
            so_what_statement="Supply chain risks for tech sector clients",
            affected_sectors=[ClientSector.TECHNOLOGY],
            source_type="ergomind"
        )
    ]

    async def run_tests():
        generator = SecureAIGenerator()

        if not generator.config.enabled:
            print("\n✗ AI generation disabled")
            return

        # Test 1: Executive Summary generation
        print("\nTest 1: Executive Summary Generation")
        print("-" * 60)

        def template_fallback(items):
            return {
                'bottom_line': ["Template fallback bottom line"],
                'key_findings': ["Template fallback finding"],
                'watch_factors': ["Template fallback factor"]
            }

        summary = await generator.generate_executive_summary(test_items, template_fallback)

        print("Generated Executive Summary:")
        for section, items in summary.items():
            print(f"\n{section.upper().replace('_', ' ')}:")
            for item in items:
                print(f"  - {item[:100]}...")

        # Test 2: "So What" statement generation
        print("\n\nTest 2: 'So What' Statement Generation")
        print("-" * 60)

        def so_what_fallback(item):
            return "Template fallback so what statement"

        so_what = await generator.generate_so_what_statement(test_items[0], so_what_fallback)
        print(f"Generated 'So What': {so_what}")

        # Test 3: Usage summary
        print("\n\nTest 3: Usage Summary")
        print("-" * 60)
        usage = generator.get_usage_summary()
        for key, value in usage.items():
            print(f"  {key}: {value}")

    # Run async tests
    asyncio.run(run_tests())

    print("\n" + "=" * 60)
    print("✓ AI Generator test complete")
    print("=" * 60)


if __name__ == "__main__":
    test_ai_generator()
