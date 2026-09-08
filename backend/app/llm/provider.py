"""Provider boundary. Existing OpenAI pipeline remains unchanged and lazy."""
import os
import json
from app.llm.disabled import DisabledLLMProvider
from app.llm.base import LLMProvider

class OpenAIProvider(LLMProvider):
    """Lazy adapter; importing this module never constructs an SDK client."""
    available = True
    def _client(self):
        from openai import OpenAI
        return OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    def generate(self, prompt: str) -> str:
        response = self._client().chat.completions.create(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), messages=[{"role":"user", "content":prompt}])
        return response.choices[0].message.content or ""
    def generate_structured(self, prompt: str, schema: dict) -> dict:
        return json.loads(self.generate(prompt + "\nReturn JSON matching this schema: " + json.dumps(schema)))

def get_llm_provider():
    return OpenAIProvider() if os.getenv("OPENAI_API_KEY") else DisabledLLMProvider()
