from sentence_transformers import SentenceTransformer
import json

model = SentenceTransformer('all-MiniLM-L6-v2')
tokenizer = model.tokenizer
print(model.max_seq_length)  # should print 256

with open("chunked_reports_enriched.json", "r", encoding="utf-8") as f:
    all_chunks = json.load(f)

over_limit = 0
for c in all_chunks:
    text = f"{c['season']} {c['team1']} vs {c['team2']} {c['subheading']} {c['content']}"
    token_count = len(tokenizer.encode(text))
    if token_count > 256:
        over_limit += 1

print(f"{over_limit} / {len(all_chunks)} chunks exceed 256 tokens")