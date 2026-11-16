"""
Knowledge Loader for FiveHorses Platform
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional


class KnowledgeLoader:
    """Loads and provides access to knowledge base data"""

    def __init__(self, knowledge_root: Optional[Path] = None):
        if knowledge_root is None:
            knowledge_root = Path(__file__).parent / "knowledge"
        self.knowledge_root = Path(knowledge_root)
        self.knowledge_cache = {}
        self._load_all_knowledge()

    def _load_all_knowledge(self):
        for file_path in self.knowledge_root.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                key = file_path.stem
                self.knowledge_cache[key] = data
            except Exception as e:
                print(f"Error loading {file_path}: {e}")

    def get_knowledge(self, key: str) -> Optional[Dict[str, Any]]:
        return self.knowledge_cache.get(key)

    def get_regional_price(self, region: str, price_type: str) -> Optional[float]:
        regional_pricing = self.get_knowledge("regional_pricing")
        if not regional_pricing:
            return None
        regions = regional_pricing.get("regions", {})
        region_data = regions.get(region)
        if region_data:
            return region_data.get(price_type)
        for key, data in regions.items():
            if key.lower() == region.lower():
                return data.get(price_type)
        return None

    def get_r_code(self, code: str) -> Optional[Dict[str, Any]]:
        r_codes = self.get_knowledge("r_codes")
        if not r_codes:
            return None
        return r_codes.get("codes", {}).get(code.upper())
