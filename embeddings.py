import os
os.environ["HF_HUB_OFFLINE"] = "1"

import json
import numpy as np
from sentence_transformers import SentenceTransformer
# ... rest of your script unchanged
import json
import numpy as np
from sentence_transformers import SentenceTransformer

with open("final_chunks.json", "r", encoding="utf-8") as f:
    all_chunks = json.load(f)

model = SentenceTransformer("all-MiniLM-L6-v2")

texts = []
for chunk in all_chunks:
    text = chunk["season"] + " " + chunk["team1"] + " " + chunk["team2"] + " " + chunk["venue"] + " " + chunk["subheading"] + " " + chunk["content"]
    texts.append(text)

print("Number of texts to embed:", len(texts))  # should print 1139

embeddings = model.encode(texts)

print(embeddings.shape)  # should be (1139, 384)
np.save("chunk_embeddings.npy", embeddings)