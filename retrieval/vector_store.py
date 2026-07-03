"""
retrieval/vector_store.py
-------------------------
ChromaDB connection and collection management utilities.

Implemented in Phase 2/3.
"""

import chromadb
from config.settings import VECTOR_STORE_PATH, COLLECTION_NAME

def get_client() -> chromadb.PersistentClient:
    return chromadb.PersistentClient(path=VECTOR_STORE_PATH)

def get_collection() -> chromadb.Collection:
    client = get_client()
    return client.get_or_create_collection(name=COLLECTION_NAME)

def reset_collection() -> chromadb.Collection:
    client = get_client()
    try:
        client.delete_collection(name=COLLECTION_NAME)
    except ValueError:
        pass # Collection might not exist yet
    return client.create_collection(name=COLLECTION_NAME)

