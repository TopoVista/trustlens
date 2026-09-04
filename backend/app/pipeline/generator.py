"""Grounded answer generation using OpenAI API"""
import os
import logging
from typing import List, Dict, Optional
from openai import OpenAI, OpenAIError, AuthenticationError, RateLimitError, APIConnectionError

logger = logging.getLogger("trustlens.generator")

_client: Optional[OpenAI] = None


def _get_client() -> OpenAI:
    global _client
    api_key = os.getenv("OPENAI_API_KEY", "").strip().strip("\"'")
    if not api_key:
        from dotenv import load_dotenv
        from pathlib import Path
        backend_env = Path(__file__).resolve().parents[2] / ".env"
        root_env = Path(__file__).resolve().parents[3] / ".env"
        for p in [backend_env, root_env]:
            if p.exists():
                load_dotenv(dotenv_path=p, override=True)
        api_key = os.getenv("OPENAI_API_KEY", "").strip().strip("\"'")

    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY environment variable is missing. "
            "Please configure OPENAI_API_KEY in backend/.env file."
        )
    if _client is None or getattr(_client, "api_key", None) != api_key:
        _client = OpenAI(api_key=api_key)
    return _client



def _build_prompt(query: str, docs: List[Dict]) -> str:
    context_blocks = []
    for i, doc in enumerate(docs):
        text = doc.get("text", "").strip()
        context_blocks.append(f"[Document {i+1}]\n{text}")

    context = "\n\n".join(context_blocks)

    prompt = f"""You are a factual, concise technical assistant.

Answer the user question using ONLY the provided evidence documents below.
Strict rules:
1. Do NOT invent facts or use external/outside knowledge.
2. Do NOT guess, speculate, or extrapolate beyond the provided text.
3. If the provided documents do not contain sufficient evidence to answer the question, say exactly:
   "I do not know based on the provided documents."
4. Be concise and technical. Avoid filler phrases and do not cite document numbers or internal system details.

Evidence Documents:
{context}

Question:
{query}

Answer:"""
    return prompt.strip()


def generate_answer(query: str, docs: List[Dict]) -> str:
    """
    Generate a grounded response using the OpenAI Chat Completions API.
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")

    try:
        client = _get_client()
        model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
        prompt = _build_prompt(query, docs)

        logger.info("Calling OpenAI generation with model: %s", model_name)

        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": "You are a factual assistant. Answer strictly based only on provided context."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,
            max_tokens=500
        )

        if not response.choices:
            raise RuntimeError("OpenAI returned an empty response with no choices.")

        message = response.choices[0].message
        content = message.content
        if not content:
            refusal = getattr(message, "refusal", None)
            if refusal:
                return f"Model refused to answer: {refusal}"
            return "I do not know based on the provided documents."

        answer = content.strip()
        logger.info("OpenAI generation successful (%d characters)", len(answer))
        return answer

    except ValueError as e:
        logger.error("Configuration or input error during generation: %s", str(e))
        raise RuntimeError(str(e)) from None
    except AuthenticationError as e:
        logger.error("OpenAI authentication failure: invalid API key")
        raise RuntimeError("OpenAI authentication failed. Please verify your OPENAI_API_KEY in backend/.env.") from None
    except RateLimitError as e:
        logger.error("OpenAI rate limit reached")
        raise RuntimeError("OpenAI rate limit or quota exceeded. Please check your account quota.") from None
    except APIConnectionError as e:
        logger.error("OpenAI network connection failed: %s", str(e))
        raise RuntimeError("Unable to reach OpenAI servers. Please check network connectivity.") from None
    except OpenAIError as e:
        logger.error("OpenAI API error occurred: %s", str(e))
        raise RuntimeError(f"OpenAI service error: {str(e)}") from None
    except RuntimeError:
        raise
    except Exception as e:
        logger.error("Unexpected error during generation: %s", str(e), exc_info=True)
        raise RuntimeError(f"Unexpected error during answer generation: {str(e)}") from None
