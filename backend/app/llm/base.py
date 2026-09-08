from typing import Any, Dict

class LLMProvider:
    available = False
    def generate(self, prompt: str) -> str: raise NotImplementedError
    def generate_structured(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]: raise NotImplementedError
