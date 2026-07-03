import chromadb
from config.settings import VECTOR_STORE_PATH, COLLECTION_NAME
from ingestion.corpus_urls import CORPUS_FUNDS

client = chromadb.PersistentClient(path=VECTOR_STORE_PATH)
collection = client.get_collection(COLLECTION_NAME)

count = collection.count()
print(f'Total chunks: {count}')
assert count == 21, f'Unexpected chunk count: {count} (expected 21)'
print('Chunk count: PASS\n')

results = collection.get(limit=10, include=['metadatas', 'documents'])
required_meta_keys = ['chunk_id', 'chunk_type', 'fund_name', 'amc', 'category', 'sub_category', 'source_url', 'scraped_date']

for i, meta in enumerate(results['metadatas']):
    for key in required_meta_keys:
        assert key in meta, f'Chunk {i} missing metadata key: {key}'
    assert len(results['documents'][i]) > 50, f'Chunk {i} content too short'
print('Metadata schema: PASS\n')

for fund in CORPUS_FUNDS:
    results = collection.get(where={'fund_name': fund['fund_name']}, include=['metadatas'])
    fund_count = len(results['ids'])
    print(f"{fund['id']}: {fund_count} chunks")
    assert fund_count == 3, f"Expected 3 chunks for {fund['id']}, got: {fund_count}"
print('Per-fund coverage: PASS')
