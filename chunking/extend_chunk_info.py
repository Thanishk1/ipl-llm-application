import json
import pandas as pd

# 1. Load your chunks and the matches table
with open("chunked_reports.json", "r", encoding="utf-8") as f:
    all_chunks = json.load(f)

matches = pd.read_parquet("parsed/matches.parquet")  # adjust path if needed

# 2. Fix the type mismatch: cast match_id in `matches` to int, since your
# chunks already have match_id as int (from the raw JSON, unquoted numbers).
matches['match_id'] = matches['match_id'].astype(int)

# 3. Build a lookup: match_id -> {season, team1, team2, venue}
match_lookup = matches.set_index('match_id')[['season', 'team1', 'team2', 'venue','date']].to_dict('index')
# .to_dict('index') turns each row into {match_id: {'season': ..., 'team1': ..., ...}}

# 4. Enrich every chunk with the looked-up metadata
missing_lookup = []
for c in all_chunks:
    meta = match_lookup.get(c['match_id'])
    if meta is None:
        missing_lookup.append(c['match_id'])
        continue
    c['season'] = meta['season']
    c['team1'] = meta['team1']
    c['team2'] = meta['team2']
    c['venue'] = meta['venue']
    c['date'] = meta['date']

print("Chunks with no matching match_id in matches.parquet:", len(missing_lookup))

# 5. Null check
missing = [c['match_id'] for c in all_chunks if 'season' not in c or c.get('season') is None]
print("Chunks missing season after join:", len(missing))

# 6. Save
with open("chunked_reports_enriched.json", "w", encoding="utf-8") as f:
    json.dump(all_chunks, f, indent=2, ensure_ascii=False)

print("Sample enriched chunk:")
print(json.dumps(all_chunks[0], indent=2, ensure_ascii=False))