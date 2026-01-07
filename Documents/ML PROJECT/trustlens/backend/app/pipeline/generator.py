"""Generator"""
from typing import List, Dict

def _build_prompt(query: str, docs: List[Dict]) -> str:
    context_blocks = []

    for i, doc in enumerate(docs):
        context_blocks.append(
            f"[Document {i+1}]\n{doc['text']}"
        )

    context = "\n\n".join(context_blocks)

    prompt = f"""
You are a factual assistant.

Answer the question using ONLY the information in the provided documents.
Do NOT use any external knowledge.
Do NOT guess or speculate.
If the documents do not contain the answer, say exactly:
"I do not know based on the provided documents."

Documents:
{context}

Question:
{query}

Answer:
""".strip()

    return prompt


def generate_answer(query: str, docs: List[Dict]) -> str:
    prompt = _build_prompt(query, docs)

    # Placeholder: LLM call will be added later
    return prompt

