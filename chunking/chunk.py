import json
from collections import Counter

with open("ipl_all_reports.json", "r", encoding="utf-8") as f:
    all_reports = json.load(f)

def chunk(report_text, match_id, title):
    final_text = report_text.split("\n\n")
    chunks = []
    chunks.append({"subheading": "intro", "content": ""})
    for text in final_text:
        is_subheading = len(text) < 100 and not text.strip().endswith(".")
        if is_subheading:
            chunks.append({"subheading": text, "content": ""})
        else:
            chunks[-1]["content"] += "\n" + text
    
    # attach match metadata to every chunk before returning
    for c in chunks:
        c["match_id"] = match_id
        c["title"] = title
    
    return chunks

all_chunks = []
for report in all_reports:
    match_chunks = chunk(report['report_text'], report['match_id'], report['title'])
    all_chunks.extend(match_chunks)

print("Total chunks across all matches:", len(all_chunks))
print("\nSample chunk:")
print(json.dumps(all_chunks[0], indent=2, ensure_ascii=False))

with open("chunked_reports.json", "w", encoding="utf-8") as f:
    json.dump(all_chunks, f, indent=2, ensure_ascii=False)

unique_match_ids_in_chunks = set(c['match_id'] for c in all_chunks)
unique_match_ids_in_reports = set(r['match_id'] for r in all_reports)

print("Matches in reports:", len(unique_match_ids_in_reports))
print("Matches represented in chunks:", len(unique_match_ids_in_chunks))
print("Missing:", unique_match_ids_in_reports - unique_match_ids_in_chunks)

lengths = [len(c['content']) for c in all_chunks]
print("Min:", min(lengths), "Max:", max(lengths), "Avg:", sum(lengths)/len(lengths))

# per-match chunk count check
counts = Counter(c["match_id"] for c in all_chunks)
print("Min chunks per match:", min(counts.values()), "Max chunks per match:", max(counts.values()))
all_headings = [c["subheading"] for c in all_chunks if c["subheading"] != "intro"]
print(set(h for h in all_headings if len(h) < 15))
from collections import Counter
counts = Counter(c["match_id"] for c in all_chunks)
print(min(counts.values()), max(counts.values()))
print(type(all_chunks[0]['match_id']), all_chunks[0]['match_id'])

import pandas as pd
matches = pd.read_parquet("parsed/matches.parquet")  # adjust path
print(matches['match_id'].dtype, matches['match_id'].iloc[0], type(matches['match_id'].iloc[0]))
