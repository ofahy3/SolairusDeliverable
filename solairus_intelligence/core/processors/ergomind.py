"""
ErgoMind Intelligence Processor
Handles processing of ErgoMind Flashpoints Forum data
"""

import re
import logging
from typing import List, Optional
from dataclasses import replace

from solairus_intelligence.config.clients import ClientSector, CLIENT_SECTOR_MAPPING
from solairus_intelligence.core.processors.base import IntelligenceItem, BaseProcessor

logger = logging.getLogger(__name__)


class ErgoMindProcessor(BaseProcessor):
    """
    Processor for ErgoMind Flashpoints Forum intelligence
    Transforms raw responses into actionable insights with "So What" analysis
    """

    def __init__(self):
        self.client_mapping = CLIENT_SECTOR_MAPPING
        self.ai_generator = None
        self._initialize_ai_generator()

    def _initialize_ai_generator(self):
        """Initialize AI generator if enabled"""
        try:
            from solairus_intelligence.utils.config import ENV_CONFIG

            if ENV_CONFIG.ai_enabled:
                from solairus_intelligence.ai.generator import SecureAIGenerator, AIConfig

                config = AIConfig(
                    api_key=ENV_CONFIG.anthropic_api_key, model=ENV_CONFIG.ai_model, enabled=True
                )
                self.ai_generator = SecureAIGenerator(config)
                logger.info("AI-enhanced 'So What' generation enabled")
        except Exception as e:
            logger.warning(f"AI generator initialization failed: {e}")

    async def process_intelligence_async(
        self, raw_text: str, category: str = "general"
    ) -> IntelligenceItem:
        """Process a single piece of raw intelligence (async version)"""
        processed_content = self._clean_and_structure(raw_text)
        relevance_score = self.calculate_base_relevance(raw_text)
        affected_sectors = self._identify_affected_sectors(raw_text)
        action_items = self._generate_action_items(raw_text, affected_sectors)
        confidence = self._calculate_confidence(processed_content)

        item = IntelligenceItem(
            raw_content=raw_text,
            processed_content=processed_content,
            category=category,
            relevance_score=relevance_score,
            so_what_statement="",
            affected_sectors=affected_sectors,
            action_items=action_items,
            confidence=confidence,
            source_type="ergomind",
        )

        so_what = await self._generate_so_what_async(raw_text, category, item=item)
        item = replace(item, so_what_statement=so_what)

        return item

    def process_intelligence(self, raw_text: str, category: str = "general") -> IntelligenceItem:
        """Process a single piece of raw intelligence (sync version for backwards compat)"""
        processed_content = self._clean_and_structure(raw_text)
        relevance_score = self.calculate_base_relevance(raw_text)
        affected_sectors = self._identify_affected_sectors(raw_text)
        action_items = self._generate_action_items(raw_text, affected_sectors)
        confidence = self._calculate_confidence(processed_content)

        item = IntelligenceItem(
            raw_content=raw_text,
            processed_content=processed_content,
            category=category,
            relevance_score=relevance_score,
            so_what_statement="",
            affected_sectors=affected_sectors,
            action_items=action_items,
            confidence=confidence,
            source_type="ergomind",
        )

        so_what = self._generate_so_what(raw_text, category, item=item)
        item = replace(item, so_what_statement=so_what)

        return item

    def _clean_and_structure(self, text: str) -> str:
        """Clean and structure raw text for presentation"""
        text = re.sub(r"\s+", " ", text).strip()
        text = text.replace("..", ".")
        text = re.sub(r"\.{3,}", "...", text)

        sentences = text.split(". ")
        sentences = [s[0].upper() + s[1:] if s else s for s in sentences]
        text = ". ".join(sentences)

        # Remove hedging language
        hedging_patterns = [
            "has not identified",
            "have not identified",
            "no evidence of",
            "does not appear",
            "not identified",
            "no significant new",
            "no major new",
            "unclear whether",
            "insufficient data",
            "cannot determine",
            "remains unclear",
        ]

        sentences = text.split(". ")
        filtered_sentences = []
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if not any(pattern in sentence_lower for pattern in hedging_patterns):
                filtered_sentences.append(sentence)

        if filtered_sentences:
            text = ". ".join(filtered_sentences)
            text = re.sub(r"\.{2,}", ".", text)

        if len(text) > 500 and "•" not in text:
            sentences = text.split(". ")
            if len(sentences) > 3:
                key_sentences = self._extract_key_sentences(sentences)
                if key_sentences:
                    return " ".join([f"{sentence}." for sentence in key_sentences])

        return text

    def _extract_key_sentences(self, sentences: List[str]) -> List[str]:
        """Extract the most important sentences from a list"""
        priority_indicators = [
            "significant",
            "major",
            "critical",
            "important",
            "key",
            "forecast",
            "expect",
            "likely",
            "will",
            "could",
            "increase",
            "decrease",
            "rise",
            "fall",
            "growth",
        ]

        key_sentences = []
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(indicator in sentence_lower for indicator in priority_indicators):
                key_sentences.append(sentence)

        return key_sentences[:5] if len(key_sentences) > 5 else key_sentences

    def _identify_affected_sectors(self, text: str) -> List[ClientSector]:
        """Identify which client sectors are affected by this intelligence"""
        affected = []
        text_lower = text.lower()

        for sector, mapping in self.client_mapping.items():
            if sector == ClientSector.GENERAL:
                continue

            sector_score = 0
            keywords = mapping.get("keywords", [])
            triggers = mapping.get("geopolitical_triggers", [])

            for keyword in keywords:
                if keyword in text_lower:
                    sector_score += 1

            for trigger in triggers:
                if trigger.lower() in text_lower:
                    sector_score += 2

            if sector_score >= 2:
                affected.append(sector)

        if not affected and self.calculate_base_relevance(text) > 0.5:
            affected.append(ClientSector.GENERAL)

        return affected

    def _generate_action_items(self, text: str, sectors: List[ClientSector]) -> List[str]:
        """Generate sector-specific and context-aware action items"""
        action_items = []
        text_lower = text.lower()

        if any(kw in text_lower for kw in ["sanction", "restriction", "ban"]):
            action_items.append(
                "Conduct immediate review of affected routes and file alternative flight plans"
            )
            action_items.append("Audit client list for exposure to sanctioned entities or regions")

        if any(kw in text_lower for kw in ["fuel", "oil price", "energy cost", "saf"]):
            action_items.append("Revise fuel hedging strategy with finance team by end of quarter")
            action_items.append("Update client proposals to reflect current fuel cost projections")

        if any(kw in text_lower for kw in ["regulation", "compliance", "faa", "easa"]):
            action_items.append(
                "Schedule regulatory compliance meeting with operations and legal teams"
            )
            action_items.append(
                "Update crew training modules to incorporate new regulatory requirements"
            )

        if any(kw in text_lower for kw in ["safety", "security", "risk"]):
            action_items.append("Convene safety committee to assess threat and update protocols")
            action_items.append(
                "Brief flight crews on enhanced security procedures for affected regions"
            )

        if ClientSector.TECHNOLOGY in sectors:
            if "export" in text_lower or "restriction" in text_lower:
                action_items.append(
                    "Proactively contact technology sector clients to discuss international travel implications"
                )
            elif "cyber" in text_lower:
                action_items.append(
                    "Review and enhance cybersecurity protocols for technology executive flights"
                )
            else:
                action_items.append(
                    "Prepare briefing for technology sector clients on industry-specific developments"
                )

        if ClientSector.FINANCE in sectors:
            if "market" in text_lower or "volatility" in text_lower:
                action_items.append(
                    "Monitor financial sector client booking patterns for early demand signals"
                )
            else:
                action_items.append(
                    "Schedule check-ins with financial sector clients to discuss market impact on travel needs"
                )

        # Remove duplicates while preserving order
        seen = set()
        unique_items = []
        for item in action_items:
            if item not in seen:
                seen.add(item)
                unique_items.append(item)

        return unique_items[:3]

    def _calculate_confidence(self, processed_content: str) -> float:
        """Calculate confidence in the processed intelligence"""
        confidence = 0.7

        if "•" in processed_content or "\n" in processed_content:
            confidence += 0.1

        if any(char.isdigit() for char in processed_content):
            confidence += 0.1

        if 100 < len(processed_content) < 1000:
            confidence += 0.1
        elif len(processed_content) >= 1000:
            confidence += 0.05

        return min(confidence, 1.0)

    async def _generate_so_what_async(
        self, text: str, category: str, item: Optional[IntelligenceItem] = None
    ) -> str:
        """Generate 'So What' statement with AI if available (async version)"""
        if self.ai_generator and item:
            try:
                ai_so_what = await self.ai_generator.generate_so_what_statement(
                    item,
                    fallback_generator=lambda x: self._generate_so_what_template(
                        x.processed_content, x.category
                    ),
                )
                if ai_so_what and len(ai_so_what) > 20:
                    return str(ai_so_what)
            except Exception as e:
                logger.debug(f"AI 'So What' generation failed, using template: {e}")

        return self._generate_so_what_template(text, category)

    def _generate_so_what(
        self, text: str, category: str, item: Optional[IntelligenceItem] = None
    ) -> str:
        """Generate 'So What' statement with AI if available (sync wrapper for backwards compat)"""
        if self.ai_generator and item:
            try:
                import asyncio

                try:
                    loop = asyncio.get_running_loop()
                    # We're in an async context, create a task
                    import concurrent.futures

                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            asyncio.run, self._generate_so_what_async(text, category, item)
                        )
                        return future.result(timeout=30)
                except RuntimeError:
                    # No event loop running, safe to use asyncio.run
                    return asyncio.run(self._generate_so_what_async(text, category, item))
            except Exception as e:
                logger.debug(f"AI 'So What' generation failed, using template: {e}")

        return self._generate_so_what_template(text, category)

    def _generate_so_what_template(self, text: str, category: str) -> str:
        """Template-based 'So What' generator"""
        text_lower = text.lower()

        if "economic" in category or "inflation" in text_lower:
            if "inflation" in text_lower:
                return "Higher operating costs will impact charter pricing and may require contract adjustments with key clients."
            elif "interest rate" in text_lower:
                return "Aircraft financing costs will adjust, affecting acquisition timing and lease rate negotiations."
            elif "gdp" in text_lower or "growth" in text_lower:
                return "Market demand shifts expected - strengthen presence in growth regions while monitoring declining markets."
            else:
                return "Economic volatility requires dynamic pricing strategies and flexible capacity planning."

        elif "geopolitical" in category or "sanctions" in text_lower or "political" in text_lower:
            if "sanctions" in text_lower:
                return "Immediate review of client exposure to sanctioned entities and route adjustments may be necessary."
            elif "china" in text_lower or "asia" in text_lower:
                return "Asia-Pacific travel patterns may shift - coordinate with clients on alternative routing and destinations."
            elif "russia" in text_lower or "ukraine" in text_lower:
                return "European airspace constraints continue - flight planning complexity increases for transatlantic operations."
            elif "middle east" in text_lower:
                return "Regional security protocols require updating - brief crews and clients on enhanced procedures."
            else:
                return "Geopolitical shifts demand proactive client communication and operational contingency planning."

        elif "regulation" in category or "compliance" in text_lower:
            if "europe" in text_lower or "eu" in text_lower:
                return "EU regulatory changes require operational procedure updates and potential crew retraining."
            elif "faa" in text_lower or "united states" in text_lower:
                return "FAA compliance adjustments needed - schedule regulatory review and update SOPs accordingly."
            elif "sustainability" in text_lower or "environmental" in text_lower:
                return "Environmental compliance costs rising - evaluate SAF adoption timeline and carbon offset strategies."
            else:
                return "New compliance requirements necessitate legal review and operational procedure modifications."

        elif "aviation" in text_lower or "aircraft" in text_lower:
            if "fuel" in text_lower or "saf" in text_lower:
                return "Fuel strategy requires reassessment - balance cost management with sustainability commitments."
            elif "airport" in text_lower or "fbo" in text_lower:
                return "Ground services landscape changing - review preferred vendor agreements and service levels."
            elif "safety" in text_lower:
                return "Safety protocols demand immediate attention - convene safety committee and update procedures."
            else:
                return "Industry dynamics shifting - competitive positioning and service differentiation become critical."

        elif "technology" in text_lower or "cyber" in text_lower:
            if "restriction" in text_lower or "export" in text_lower:
                return "Technology sector clients face new travel constraints - proactive coordination on international itineraries essential."
            elif "cyber" in text_lower or "security" in text_lower:
                return "Cybersecurity concerns escalating - evaluate onboard connectivity security and client data protection."
            else:
                return "Tech industry disruption affects executive travel patterns - maintain flexibility in service offerings."

        elif "financial" in text_lower or "market" in text_lower or "investment" in text_lower:
            if "market volatility" in text_lower or "stock" in text_lower:
                return "Market turbulence may compress private aviation budgets - emphasize value proposition to financial clients."
            elif "banking" in text_lower:
                return "Banking sector dynamics shift executive travel priorities - position for relationship-critical trips."
            else:
                return "Financial sector developments influence client liquidity - monitor closely for demand signals."

        elif "supply chain" in text_lower:
            return "Parts availability concerns require proactive inventory management and vendor diversification strategies."

        else:
            if "security" in category:
                return "Security posture requires updating - assess threat levels and adjust protocols for affected destinations."
            elif "economic" in category:
                return "Economic indicators suggest demand pattern changes - adjust capacity and marketing focus accordingly."
            else:
                return "Situation warrants monitoring - prepare contingency plans and maintain client communication readiness."
