from app.llm.base import LLMProvider

class DisabledLLMProvider(LLMProvider):
    reason = "LLM unavailable; deterministic analytics-only mode is active."
    def generate(self, prompt: str) -> str: return self.reason
    def generate_structured(self, prompt: str, schema: dict) -> dict: return {"status":"llm_unavailable", "message":self.reason}
