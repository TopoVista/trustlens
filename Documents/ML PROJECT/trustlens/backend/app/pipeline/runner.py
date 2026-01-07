import subprocess
from app.pipeline.retriever import retrieve
from app.pipeline.generator import generate_answer


def _call_llm(prompt: str) -> str:
    result = subprocess.run(
        ["ollama", "run", "llama3"],
        input=prompt,
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
    return result.stdout.strip()


def run_rag(query: str, k: int = 5) -> dict:
    if not query.strip():
        raise ValueError("Query must not be empty")
    
    docs = retrieve(query, k=k)

    prompt = generate_answer(query, docs)

    answer = _call_llm(prompt)

    return {
        "query": query,
        "answer": answer,
        "documents": docs
    }
