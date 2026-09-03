from app.rag.embeddings import embed_texts

# Test with a single sentence
texts = ["Fever is a temporary rise in body temperature above 100.4F."]

embeddings = embed_texts(texts)

print(f"\nNumber of embeddings: {len(embeddings)}")
print(f"Vector dimension: {len(embeddings[0])}")
print(f"First 5 values: {embeddings[0][:5]}")
print("\nEmbedding works!")
