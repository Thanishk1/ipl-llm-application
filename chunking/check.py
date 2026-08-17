import json

with open("final_chunks.json", "r", encoding="utf-8") as f:
    final_chunks = json.load(f)

first_match_id = final_chunks[0]['match_id']
match_chunks = [c for c in final_chunks if c['match_id'] == first_match_id]

print(f"match_id: {first_match_id}, total chunks: {len(match_chunks)}")
print()

for c in match_chunks:
    print(f"--- subheading: '{c['subheading']}' | sub_index: {c['sub_index']} ---")
    print(c['content'])
    print()