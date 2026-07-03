"""
inference/formatter.py
----------------------
Ensures all API responses conform to a strict JSON schema containing
the answer, sources, and query classification.
"""

def format_factual_response(answer: str, source_url: str, scraped_date: str) -> dict:
    return {
        "type": "factual",
        "answer": answer,
        "source": source_url,
        "last_updated": scraped_date
    }

def format_refusal_response(answer: str) -> dict:
    return {
        "type": "refusal",
        "answer": answer,
        "source": None,
        "last_updated": None
    }
