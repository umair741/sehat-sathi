"""Quick test for RAG retrieval: embed query via HF API, search Pinecone, print results."""

from app.rag.embeddings import embed_text
from app.services.vector_store import query_index

query = "diabetes kya hai?"

print(f"Embedding query via HF Inference API: '{query}'")
query_vec = embed_text(query)
print(f"Query vector dimension: {len(query_vec)}")

print("\nSearching Pinecone...")
results = query_index(query_vec, top_k=3)

if not results:
    print("No results found. Is the index populated?")
else:
    for i, r in enumerate(results, 1):
        print(f"\n--- Match {i} | score: {r['score']:.4f} ---")
        print(f"Page: {r['page']} | Source: {r['verified_source'] or r['source_file']}")
        print(f"Text: {r['text'][:120]}...")

print("\nRetriever test done.")
