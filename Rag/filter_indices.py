import json
with open("final_chunks.json", "r", encoding="utf-8") as f:
    final_chunks = json.load(f)
def filter_indices(final_chunks, teams=None, season=None):
    filtered_indices = []
    for i, chunk in enumerate(final_chunks):
        if season is not None:
            if chunk['season'] != season:
                continue
        if teams is not None:
            chunk_teams = {chunk['team1'], chunk['team2']}
            if not all(t in chunk_teams for t in teams):
                continue
        filtered_indices.append(i)
    return filtered_indices
# print(idxs)
# for i in idxs:
#     c = final_chunks[i]
#     print(c['season'], '|', c['team1'], 'vs', c['team2'], '|', c['content'][:100] )