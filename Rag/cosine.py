import numpy as np
import json
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("all-MiniLM-L6-v2")
def cosine_similarity(query, embeddings):
    query_embedding = model.encode([query])
    dot_product = query_embedding @ embeddings.T
    query_norm=np.linalg.norm(query_embedding)
    embeddings_norm=np.linalg.norm(embeddings, axis=1)
    return dot_product / (query_norm * embeddings_norm)