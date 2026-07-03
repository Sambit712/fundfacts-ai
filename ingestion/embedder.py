"""
ingestion/embedder.py
---------------------
Converts text chunks to dense vectors using BAAI/bge-small-en-v1.5
and persists them to ChromaDB. Entry point for the full ingestion pipeline.

Run:
    python -m ingestion.embedder
"""

import os
from sentence_transformers import SentenceTransformer

from ingestion.scraper import scrape_all_funds
from ingestion.cleaner import clean
from ingestion.chunker import chunk
from ingestion.corpus_urls import CORPUS_FUNDS
from retrieval.vector_store import reset_collection
from config.settings import EMBEDDING_MODEL

def embed_and_store(chunks: list[dict]) -> None:
    print(f"Loading embedding model: {EMBEDDING_MODEL}...")
    model = SentenceTransformer(EMBEDDING_MODEL)
    
    print(f"Encoding {len(chunks)} chunks...")
    contents = [c["content"] for c in chunks]
    # Encode with normalize_embeddings=True as per plan
    embeddings = model.encode(contents, normalize_embeddings=True)
    
    print("Resetting vector store collection...")
    collection = reset_collection()
    
    print("Inserting chunks into ChromaDB...")
    collection.add(
        ids=[c["chunk_id"] for c in chunks],
        embeddings=embeddings.tolist(),
        documents=contents,
        metadatas=[{k: v for k, v in c.items() if k != "content"} for c in chunks]
    )
    print("Insertion complete.")

def main():
    fund_lookup = {f["id"]: f for f in CORPUS_FUNDS}
    
    print("Starting ingestion pipeline...")
    print(f"Scraping {len(CORPUS_FUNDS)} funds...")
    scraped_data = scrape_all_funds(CORPUS_FUNDS)
    
    all_chunks = []
    
    for data in scraped_data:
        fund_id = data["fund_id"]
        fund = fund_lookup[fund_id]
        
        print(f"Processing: {fund['fund_name']}")
        cleaned_text = clean(data["raw_text"])
        
        fund_meta = {
            **fund,
            "source_url": data["source_url"],
            "scraped_date": data["scraped_date"]
        }
        
        fund_chunks = chunk(cleaned_text, fund_meta)
        all_chunks.extend(fund_chunks)
        
    embed_and_store(all_chunks)
    print("Ingestion pipeline finished successfully!")

if __name__ == "__main__":
    main()

