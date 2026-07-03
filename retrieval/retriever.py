"""
retrieval/retriever.py
----------------------
Given a user query, fetches the most relevant chunks from ChromaDB.
Uses fund name detection to pull all 3 chunks for explicitly mentioned funds,
or falls back to vector similarity search for broad queries.
"""

from sentence_transformers import SentenceTransformer
from config.settings import EMBEDDING_MODEL, TOP_K
from retrieval.vector_store import get_collection

FUND_NAME_MAP = {
    "hdfc mid cap": "HDFC Mid Cap Fund Direct Growth",
    "hdfc multi cap": "HDFC Multi Cap Fund Direct Growth",
    "icici multi asset": "ICICI Prudential Multi Asset Fund Direct Growth",
    "icici prudential multi asset": "ICICI Prudential Multi Asset Fund Direct Growth",
    "sbi contra": "SBI Contra Fund Direct Growth",
    "sbi small midcap": "SBI Small Midcap Fund Direct Growth",
    "sbi small mid cap": "SBI Small Midcap Fund Direct Growth",
    "uti innovation": "UTI Innovation Fund Direct Growth",
    "uti small cap": "UTI Small Cap Fund Direct Growth",
}

# Singleton model to avoid reloading on every query
_model = None

def get_embedding_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model

def detect_funds(query: str) -> list[str]:
    """Returns a list of official fund names mentioned in the query."""
    query_lower = query.lower()
    detected = set()
    for key, official_name in FUND_NAME_MAP.items():
        if key in query_lower:
            detected.add(official_name)
    return list(detected)

def retrieve_chunks(query: str) -> list[dict]:
    """
    Retrieves relevant chunks for the query.
    """
    collection = get_collection()
    detected_funds = detect_funds(query)
    
    # 1. Query Encoding
    model = get_embedding_model()
    encoded_query = model.encode(
        "Represent this sentence for searching relevant passages: " + query,
        normalize_embeddings=True
    ).tolist()

    if len(detected_funds) > 0:
        # Dynamic Retrieval: We know the exact funds.
        # Fetch all 3 chunks per fund.
        fetch_k = len(detected_funds) * 3
        
        if len(detected_funds) == 1:
            where_clause = {"fund_name": detected_funds[0]}
        else:
            where_clause = {"fund_name": {"$in": detected_funds}}
            
        results = collection.query(
            query_embeddings=[encoded_query],
            n_results=fetch_k,
            where=where_clause,
            include=["metadatas", "documents"]
        )
    else:
        # Broad Query: Fallback to top_k=6 vector search
        results = collection.query(
            query_embeddings=[encoded_query],
            n_results=6,
            include=["metadatas", "documents"]
        )

    # Format output
    chunks = []
    if results and results["ids"] and len(results["ids"][0]) > 0:
        # Chroma returns lists of lists for queries
        for i in range(len(results["ids"][0])):
            meta = results["metadatas"][0][i]
            doc = results["documents"][0][i]
            
            chunks.append({
                "content": doc,
                "fund_name": meta.get("fund_name"),
                "source_url": meta.get("source_url"),
                "scraped_date": meta.get("scraped_date"),
                "chunk_type": meta.get("chunk_type"),
            })
            
    return chunks
