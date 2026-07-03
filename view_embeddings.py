import chromadb
import sys
import io
from config.settings import VECTOR_STORE_PATH, COLLECTION_NAME

# Fix Unicode printing issues in Windows terminals (for ₹ symbols)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def main():
    print(f"Connecting to ChromaDB at {VECTOR_STORE_PATH}...")
    client = chromadb.PersistentClient(path=VECTOR_STORE_PATH)
    
    try:
        collection = client.get_collection(COLLECTION_NAME)
    except Exception as e:
        print(f"Could not find collection '{COLLECTION_NAME}'. Make sure ingestion has been run.")
        return

    # Fetch all chunks (we know there are 21). Include embeddings.
    results = collection.get(
        include=["embeddings", "metadatas", "documents"]
    )
    
    total_chunks = len(results["ids"])
    print(f"\nFound {total_chunks} chunks in the database.\n")
    print("-" * 80)
    
    for i in range(total_chunks):
        chunk_id = results["ids"][i]
        meta = results["metadatas"][i]
        doc = results["documents"][i]
        embedding = results["embeddings"][i]
        
        print(f"Chunk ID    : {chunk_id}")
        print(f"Fund Name   : {meta.get('fund_name')}")
        print(f"Chunk Type  : {meta.get('chunk_type')}")
        
        # Display first 100 characters of the content
        snippet = doc[:100] + "..." if len(doc) > 100 else doc
        print(f"Content     : {snippet}")
        
        # Embeddings are large (384 dimensions), so we'll show just the shape and first 5 values
        dim = len(embedding)
        preview = ", ".join([f"{val:.4f}" for val in embedding[:5]])
        print(f"Embedding   : [{preview}, ...] (Total dimensions: {dim})")
        print("-" * 80)

if __name__ == "__main__":
    main()
