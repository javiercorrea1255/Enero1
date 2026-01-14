"""
Fertilizer Pricing Service.

Resolves fertilizer costs from manual input, cached AI suggestions, or defaults.
Uses OpenAI to suggest current prices when not manually provided.
"""

import os
import json
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class FertilizerPricingService:
    """Service for resolving fertilizer prices with AI-assisted suggestions."""
    
    # In-memory cache for AI-suggested prices (6 hours TTL)
    _price_cache: Dict[str, Tuple[Dict[str, float], datetime]] = {}
    CACHE_TTL_HOURS = 6
    
    # Default fallback prices (MXN per kg) - conservative estimates
    DEFAULT_PRICES = {
        "masterblend": 180.0,  # MXN/kg
        "calcium_nitrate": 150.0,  # MXN/kg
        "epsom_salt": 120.0  # MXN/kg
    }
    
    # Price validation bounds (MXN per kg)
    MIN_PRICE = 20.0
    MAX_PRICE = 600.0
    
    def __init__(self, ai_service=None):
        """
        Initialize pricing service.
        
        Args:
            ai_service: Optional AIService instance for price suggestions
        """
        self.ai_service = ai_service
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.use_ai = bool(self.openai_api_key) and ai_service is not None
    
    def get_fertilizer_costs(
        self,
        masterblend_cost_per_kg: Optional[float] = None,
        calcium_nitrate_cost_per_kg: Optional[float] = None,
        epsom_salt_cost_per_kg: Optional[float] = None,
        region: str = "mexico"
    ) -> Tuple[Dict[str, float], str]:
        """
        Get fertilizer costs from manual input, AI suggestions, or defaults.
        
        Manual inputs are ALWAYS preserved when provided.
        Missing values are filled by AI suggestions (if available), then defaults.
        
        Args:
            masterblend_cost_per_kg: Manual cost for Masterblend (MXN/kg)
            calcium_nitrate_cost_per_kg: Manual cost for Calcium Nitrate (MXN/kg)
            epsom_salt_cost_per_kg: Manual cost for Epsom Salt (MXN/kg)
            region: Geographic region for pricing (default: "mexico")
        
        Returns:
            Tuple of (costs_dict, source) where:
            - costs_dict: {"masterblend": float, "calcium_nitrate": float, "epsom_salt": float}
            - source: "manual", "ai_suggested", or "default"
        """
        # Track which values were provided manually
        manual_count = sum([
            masterblend_cost_per_kg is not None,
            calcium_nitrate_cost_per_kg is not None,
            epsom_salt_cost_per_kg is not None
        ])
        
        # Check if all costs are manually provided
        if manual_count == 3:
            costs = {
                "masterblend": masterblend_cost_per_kg,
                "calcium_nitrate": calcium_nitrate_cost_per_kg,
                "epsom_salt": epsom_salt_cost_per_kg
            }
            # Validate manual costs
            if self._validate_costs(costs):
                logger.info("Using all manually provided fertilizer costs")
                return costs, "manual"
            else:
                logger.warning("Manual costs outside valid range, using defaults")
                return self.DEFAULT_PRICES.copy(), "default"
        
        # Start with manual values where provided, None where missing
        final_costs = {
            "masterblend": masterblend_cost_per_kg,
            "calcium_nitrate": calcium_nitrate_cost_per_kg,
            "epsom_salt": epsom_salt_cost_per_kg
        }
        
        ai_used = False
        
        # Try to fill missing values with AI suggestions
        if self.use_ai and manual_count < 3:
            try:
                ai_costs = self._get_ai_suggested_costs(region)
                if ai_costs:
                    # Only use AI for missing values (preserve manual inputs)
                    if final_costs["masterblend"] is None:
                        final_costs["masterblend"] = ai_costs.get("masterblend")
                        ai_used = True
                    if final_costs["calcium_nitrate"] is None:
                        final_costs["calcium_nitrate"] = ai_costs.get("calcium_nitrate")
                        ai_used = True
                    if final_costs["epsom_salt"] is None:
                        final_costs["epsom_salt"] = ai_costs.get("epsom_salt")
                        ai_used = True
                    
                    if ai_used:
                        logger.info(f"Filled {3 - manual_count} missing costs with AI suggestions")
            except Exception as e:
                logger.error(f"Error getting AI suggested costs: {e}")
        
        # Fill any remaining None values with defaults
        if final_costs["masterblend"] is None:
            final_costs["masterblend"] = self.DEFAULT_PRICES["masterblend"]
        if final_costs["calcium_nitrate"] is None:
            final_costs["calcium_nitrate"] = self.DEFAULT_PRICES["calcium_nitrate"]
        if final_costs["epsom_salt"] is None:
            final_costs["epsom_salt"] = self.DEFAULT_PRICES["epsom_salt"]
        
        # Determine source based on what was used
        if manual_count == 3:
            source = "manual"
        elif ai_used:
            # If AI was used to fill any gaps, mark as ai_suggested
            source = "ai_suggested"
        elif manual_count > 0:
            # Some manual, rest defaults (no AI available)
            source = "manual"
        else:
            # All defaults
            source = "default"
        
        logger.info(f"Final costs: {manual_count} manual, AI={'yes' if ai_used else 'no'}, source={source}")
        return final_costs, source
    
    def _get_ai_suggested_costs(self, region: str) -> Optional[Dict[str, float]]:
        """
        Get AI-suggested costs with caching.
        
        Args:
            region: Geographic region
        
        Returns:
            Dict with suggested costs or None if AI fails
        """
        # Check cache first
        cache_key = f"fertilizer_prices_{region}"
        if cache_key in self._price_cache:
            cached_prices, cached_time = self._price_cache[cache_key]
            if datetime.now() - cached_time < timedelta(hours=self.CACHE_TTL_HOURS):
                logger.info(f"Using cached AI price suggestions for {region}")
                return cached_prices
        
        # Call AI service for suggestions
        try:
            suggested_costs = self._ask_ai_for_prices(region)
            if suggested_costs and self._validate_costs(suggested_costs):
                # Cache the results
                self._price_cache[cache_key] = (suggested_costs, datetime.now())
                return suggested_costs
        except Exception as e:
            logger.error(f"AI price suggestion failed: {e}")
        
        return None
    
    def _ask_ai_for_prices(self, region: str) -> Optional[Dict[str, float]]:
        """
        Ask OpenAI for current fertilizer prices.
        
        Args:
            region: Geographic region
        
        Returns:
            Dict with suggested prices or None
        """
        if not self.ai_service or not self.use_ai:
            return None
        
        prompt = f"""Como experto en agricultura y mercado de insumos agrícolas en {region.upper()}, 
proporciona los precios actuales promedio (en MXN por kilogramo) para los siguientes fertilizantes 
hidropónicos de calidad comercial:

1. Masterblend 4-18-38 (fertilizante base hidropónico)
2. Nitrato de Calcio (Calcium Nitrate, grado hidropónico)
3. Sal de Epsom (Sulfato de Magnesio, MgSO4)

Requisitos:
- Precios al mayoreo para productores (no retail)
- Mercado mexicano actual (últimos 6 meses)
- Formato JSON exacto
- Solo números, sin símbolos de moneda

Responde ÚNICAMENTE con JSON en este formato:
{{
    "masterblend": 180.0,
    "calcium_nitrate": 150.0,
    "epsom_salt": 120.0
}}
"""
        
        try:
            # Use existing AIService to call OpenAI
            if not hasattr(self.ai_service, 'client') or not self.ai_service.client:
                return None
            
            response = self.ai_service.client.chat.completions.create(
                model=self.ai_service.llm_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Eres un experto en mercado de insumos agrícolas en México. "
                            "Proporciona precios reales y actuales en formato JSON. "
                            "Responde SOLO con JSON válido, sin explicaciones adicionales."
                        )
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for factual responses
                max_tokens=200,
                timeout=10.0  # 10 second timeout
            )
            
            content = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            # Sometimes AI wraps JSON in markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            # Parse JSON response
            prices = json.loads(content)
            
            # Validate structure
            if all(key in prices for key in ["masterblend", "calcium_nitrate", "epsom_salt"]):
                return {
                    "masterblend": float(prices["masterblend"]),
                    "calcium_nitrate": float(prices["calcium_nitrate"]),
                    "epsom_salt": float(prices["epsom_salt"])
                }
            else:
                logger.warning(f"AI response missing required keys: {prices}")
                return None
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI price response as JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Error asking AI for prices: {e}")
            return None
    
    def _validate_costs(self, costs: Dict[str, float]) -> bool:
        """
        Validate that costs are within acceptable bounds.
        
        Args:
            costs: Dict of fertilizer costs
        
        Returns:
            True if all costs are valid
        """
        try:
            for fertilizer, price in costs.items():
                if not isinstance(price, (int, float)):
                    return False
                if price < self.MIN_PRICE or price > self.MAX_PRICE:
                    logger.warning(
                        f"Price for {fertilizer} ({price} MXN/kg) outside valid range "
                        f"[{self.MIN_PRICE}, {self.MAX_PRICE}]"
                    )
                    return False
            return True
        except Exception:
            return False
