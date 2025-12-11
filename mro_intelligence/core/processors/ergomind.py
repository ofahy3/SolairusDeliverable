"""
ErgoMind Intelligence Processor
Handles processing of ErgoMind Flashpoints Forum data

Integrates Grainger-specific configuration for:
- Relevance scoring based on MRO market priorities
- Geographic focus on US/USMCA region
- Sector prioritization for Grainger customer base
"""

import logging
import re
from dataclasses import replace
from typing import List, Optional

from mro_intelligence.config.content_blocklist import check_content
from mro_intelligence.config.grainger_profile import (
    GEOGRAPHIC_FOCUS,
    SECTOR_PRIORITIES,
    get_grainger_config,
)
from mro_intelligence.config.clients import CLIENT_SECTOR_MAPPING, ClientSector
from mro_intelligence.core.processors.base import BaseProcessor, IntelligenceItem

logger = logging.getLogger(__name__)


class ErgoMindProcessor(BaseProcessor):
    """
    Processor for ErgoMind Flashpoints Forum intelligence
    Transforms raw responses into actionable insights with "So What" analysis

    Integrates Grainger configuration for:
    - Geographic relevance boost (US/USMCA content scores higher)
    - Sector prioritization (manufacturing, construction score higher)
    - Keyword-based relevance filtering
    """

    def __init__(self):
        self.client_mapping = CLIENT_SECTOR_MAPPING
        self.ai_generator = None
        self.grainger_config = get_grainger_config()
        self._initialize_ai_generator()

    def _initialize_ai_generator(self):
        """Initialize AI generator if enabled"""
        try:
            from mro_intelligence.utils.config import ENV_CONFIG

            if ENV_CONFIG.ai_enabled:
                from mro_intelligence.ai.generator import AIConfig, SecureAIGenerator

                config = AIConfig(
                    api_key=ENV_CONFIG.anthropic_api_key, model=ENV_CONFIG.ai_model, enabled=True
                )
                self.ai_generator = SecureAIGenerator(config)
                logger.info("AI-enhanced 'So What' generation enabled")
        except Exception as e:
            logger.warning(f"AI generator initialization failed: {e}")

    def validate_response(self, response: str) -> Optional[str]:
        """
        Process and validate ErgoMind response.
        Returns None if blocked content is found.

        Args:
            response: Raw response text from ErgoMind

        Returns:
            Validated response or None if contamination detected
        """
        violations = check_content(response)
        if violations:
            logger.warning(f"Filtered response due to blocked content: {violations}")
            return None
        return response

    async def process_intelligence_async(
        self, raw_text: str, category: str = "general"
    ) -> Optional[IntelligenceItem]:
        """
        Process a single piece of raw intelligence (async version)

        Applies Grainger-specific relevance scoring:
        - Boosts US/USMCA content
        - Prioritizes MRO-relevant sectors
        - Adjusts score based on keyword matches
        """
        # Validate response for blocked content
        validated_text = self.validate_response(raw_text)
        if validated_text is None:
            return None

        processed_content = self._clean_and_structure(validated_text)
        relevance_score = self.calculate_base_relevance(raw_text)

        # Apply Grainger-specific relevance boost
        grainger_boost = self.grainger_config.calculate_relevance_boost(raw_text)
        relevance_score = min(relevance_score + grainger_boost, 1.0)

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

    def process_intelligence(self, raw_text: str, category: str = "general") -> Optional[IntelligenceItem]:
        """
        Process a single piece of raw intelligence (sync version for backwards compat)

        Applies Grainger-specific relevance scoring:
        - Boosts US/USMCA content
        - Prioritizes MRO-relevant sectors
        - Adjusts score based on keyword matches
        """
        # Validate response for blocked content
        validated_text = self.validate_response(raw_text)
        if validated_text is None:
            return None

        processed_content = self._clean_and_structure(validated_text)
        relevance_score = self.calculate_base_relevance(raw_text)

        # Apply Grainger-specific relevance boost
        grainger_boost = self.grainger_config.calculate_relevance_boost(raw_text)
        relevance_score = min(relevance_score + grainger_boost, 1.0)

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
        """Generate sector-specific and context-aware action items for MRO market"""
        action_items = []
        text_lower = text.lower()

        # General supply chain and trade impacts
        if any(kw in text_lower for kw in ["sanction", "restriction", "ban", "tariff"]):
            action_items.append(
                "Review supplier exposure to affected regions and identify alternative sourcing"
            )
            action_items.append("Assess inventory levels for potentially impacted product categories")

        if any(kw in text_lower for kw in ["fuel", "oil price", "energy cost", "diesel"]):
            action_items.append("Update cost projections for energy-intensive product categories")
            action_items.append("Review transportation and logistics cost assumptions")

        if any(kw in text_lower for kw in ["regulation", "compliance", "osha", "epa"]):
            action_items.append(
                "Review safety and compliance product inventory for regulatory changes"
            )
            action_items.append(
                "Prepare customer communications on new compliance requirements"
            )

        if any(kw in text_lower for kw in ["safety", "security", "risk"]):
            action_items.append("Assess demand impact for safety equipment and PPE categories")
            action_items.append(
                "Brief sales teams on safety-related product opportunities"
            )

        # MRO Sector-specific action items
        if ClientSector.MANUFACTURING in sectors:
            if "reshoring" in text_lower or "nearshoring" in text_lower:
                action_items.append(
                    "Identify expansion opportunities with manufacturers relocating production"
                )
            elif "automation" in text_lower or "robotics" in text_lower:
                action_items.append(
                    "Review industrial automation product portfolio for growth opportunities"
                )
            else:
                action_items.append(
                    "Monitor manufacturing PMI for demand signals in industrial supplies"
                )

        # Grainger's customer segments
        if ClientSector.GOVERNMENT in sectors:
            if "defense" in text_lower or "military" in text_lower:
                action_items.append(
                    "Assess impact on $400M defense segment and military base operations"
                )
            elif "infrastructure" in text_lower or "federal" in text_lower:
                action_items.append(
                    "Evaluate opportunities from federal infrastructure spending"
                )
            else:
                action_items.append(
                    "Monitor government spending and GSA contract implications"
                )

        if ClientSector.COMMERCIAL_FACILITIES in sectors:
            if "office" in text_lower or "return" in text_lower:
                action_items.append(
                    "Track office occupancy trends for commercial maintenance demand"
                )
            elif "healthcare" in text_lower or "hospital" in text_lower:
                action_items.append(
                    "Assess healthcare facility expansion for maintenance supply demand"
                )
            else:
                action_items.append(
                    "Monitor commercial real estate activity for facility maintenance demand"
                )

        if ClientSector.CONTRACTORS in sectors:
            if "infrastructure" in text_lower or "spending" in text_lower:
                action_items.append(
                    "Position for increased demand from infrastructure project activity"
                )
            elif "materials" in text_lower or "steel" in text_lower or "lumber" in text_lower:
                action_items.append(
                    "Review fastener and building supply inventory for price/availability changes"
                )
            else:
                action_items.append(
                    "Track construction permits and housing starts for regional demand planning"
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
                    asyncio.get_running_loop()
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
        """Template-based 'So What' generator for MRO market intelligence"""
        text_lower = text.lower()

        # Economic impacts on MRO demand
        if "economic" in category or "inflation" in text_lower:
            if "inflation" in text_lower:
                return "Rising input costs will pressure MRO product margins and may require pricing adjustments across industrial categories."
            elif "interest rate" in text_lower:
                return "Higher financing costs may delay equipment purchases, shifting demand toward maintenance and repair over replacement."
            elif "gdp" in text_lower or "growth" in text_lower:
                return "Economic growth patterns suggest shifts in regional MRO demand - adjust inventory and sales coverage accordingly."
            else:
                return "Economic volatility affects industrial customer budgets - emphasize value and total cost of ownership messaging."

        # Geopolitical impacts on supply chain and sourcing
        elif "geopolitical" in category or "sanctions" in text_lower or "political" in text_lower:
            if "sanctions" in text_lower:
                return "Sanctions may disrupt supply chains for certain product categories - identify alternative sourcing options."
            elif "china" in text_lower or "asia" in text_lower:
                return "Asia-Pacific trade dynamics shifting - assess supplier concentration risk and diversification opportunities."
            elif "russia" in text_lower or "ukraine" in text_lower:
                return "Ongoing conflict impacts energy and commodity markets - monitor downstream effects on industrial customer demand."
            elif "tariff" in text_lower or "trade" in text_lower:
                return "Trade policy changes will affect import costs for key product categories - review pricing and sourcing strategies."
            else:
                return "Geopolitical developments warrant supply chain risk assessment and contingency planning."

        # Regulatory impacts on MRO products
        elif "regulation" in category or "compliance" in text_lower:
            if "osha" in text_lower or "safety" in text_lower:
                return "New safety regulations create demand opportunities for compliant PPE and safety equipment."
            elif "epa" in text_lower or "environmental" in text_lower:
                return "Environmental compliance requirements driving demand for sustainable products and waste management solutions."
            elif "sustainability" in text_lower:
                return "Sustainability mandates increasing customer interest in energy-efficient and eco-friendly MRO products."
            else:
                return "Regulatory changes may create new compliance product opportunities - assess portfolio alignment."

        # Manufacturing sector impacts
        elif "manufacturing" in text_lower or "factory" in text_lower or "production" in text_lower:
            if "reshoring" in text_lower or "nearshoring" in text_lower:
                return "Manufacturing reshoring creates growth opportunities - position for new facility outfitting and ongoing MRO needs."
            elif "automation" in text_lower or "robotics" in text_lower:
                return "Automation investments shift maintenance needs - expand portfolio in industrial automation support products."
            elif "downtime" in text_lower or "maintenance" in text_lower:
                return "Unplanned downtime concerns driving preventive maintenance investment - emphasize reliability solutions."
            else:
                return "Manufacturing activity trends signal MRO demand changes - align inventory with production forecasts."

        # Construction sector impacts
        elif "construction" in text_lower or "infrastructure" in text_lower or "building" in text_lower:
            if "infrastructure" in text_lower or "spending" in text_lower:
                return "Infrastructure investment creates sustained demand for construction supplies and safety equipment."
            elif "materials" in text_lower or "steel" in text_lower or "lumber" in text_lower:
                return "Materials cost changes affect contractor budgets - position value alternatives and bulk purchasing options."
            elif "housing" in text_lower or "residential" in text_lower:
                return "Residential construction trends impact contractor tool and supply demand - adjust regional coverage."
            else:
                return "Construction activity indicators suggest demand shifts - monitor permit data for regional planning."

        # Energy sector impacts
        elif "energy" in text_lower or "oil" in text_lower or "drilling" in text_lower:
            if "drilling" in text_lower or "exploration" in text_lower:
                return "Oil and gas activity changes impact demand for pumps, valves, and specialty MRO products."
            elif "renewable" in text_lower or "solar" in text_lower or "wind" in text_lower:
                return "Clean energy growth creates new MRO product opportunities in solar, wind, and grid infrastructure."
            elif "refinery" in text_lower or "downstream" in text_lower:
                return "Refinery and processing facility needs drive demand for safety equipment and specialized maintenance supplies."
            else:
                return "Energy sector dynamics affect regional MRO demand patterns - align with capex trends."

        # Transportation and logistics impacts
        elif "freight" in text_lower or "trucking" in text_lower or "logistics" in text_lower:
            if "fleet" in text_lower or "trucking" in text_lower:
                return "Fleet activity levels signal demand for vehicle maintenance products and shop supplies."
            elif "warehouse" in text_lower or "distribution" in text_lower:
                return "Warehouse and fulfillment growth drives demand for material handling and packaging supplies."
            else:
                return "Logistics sector trends affect demand for fleet and facility maintenance products."

        # Agriculture sector impacts
        elif "agriculture" in text_lower or "farming" in text_lower or "crop" in text_lower:
            if "commodity" in text_lower or "prices" in text_lower:
                return "Commodity price trends affect farm equipment investment and maintenance spending patterns."
            elif "weather" in text_lower or "drought" in text_lower:
                return "Weather patterns impact agricultural equipment usage and create demand for irrigation products."
            else:
                return "Agricultural sector outlook suggests seasonal demand patterns - prepare for equipment maintenance cycles."

        # Supply chain disruptions
        elif "supply chain" in text_lower or "shortage" in text_lower:
            return "Supply chain disruptions require proactive inventory management and alternative supplier identification."

        # Default responses by category
        else:
            if "security" in category:
                return "Security concerns may increase demand for safety and access control products."
            elif "economic" in category:
                return "Economic indicators suggest industrial activity shifts - adjust demand forecasts accordingly."
            else:
                return "Developments warrant monitoring for potential MRO demand implications across key sectors."
