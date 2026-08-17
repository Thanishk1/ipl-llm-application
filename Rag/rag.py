from extract_from_query import extract 
from expand_query import expand_query
from cosine import cosine_similarity
from filter_indices import filter_indices
import numpy as np
import json

embeddings = np.load("chunk_embeddings.npy")
with open("final_chunks.json", "r", encoding="utf-8") as f:
    final_chunks = json.load(f)


def search(query, embeddings, final_chunks, top_k=5, match_id=None):
    # If the caller already knows which specific match to search within
    # (e.g. the user picked one after an ambiguous-match prompt), skip
    # straight to filtering by match_id and ranking within it.
    if match_id is not None:
        idxs = [i for i, c in enumerate(final_chunks) if c['match_id'] == match_id]
        embeddings_subset = embeddings[idxs]
        final_chunks_subset = [final_chunks[i] for i in idxs]

        expanded_query = expand_query(query)
        similarities = cosine_similarity(expanded_query, embeddings_subset)
        top_k_indices = np.argsort(similarities[0])[::-1][:top_k]

        results = []
        for idx in top_k_indices:
            chunk = final_chunks_subset[idx]
            similarity_score = similarities[0][idx]
            results.append((chunk, similarity_score))
        return results

    teams, season = extract(query)
    if teams or season:
        idxs = filter_indices(final_chunks, teams=teams if teams else None, season=season)

        # Ambiguity check: only relevant when the query names exactly two teams
        # (a specific matchup). A single-team query naturally spans many matches
        # and isn't ambiguous in the same sense.
        if teams and len(teams) == 2:
            distinct_matches = {}
            for i in idxs:
                mid = final_chunks[i]['match_id']
                if mid not in distinct_matches:
                    distinct_matches[mid] = {
                        'date': final_chunks[i]['date'],
                        'venue': final_chunks[i]['venue']
                    }
            if len(distinct_matches) > 1:
                return {
                    'ambiguous': True,
                    'candidates': [
                        {'match_id': mid, 'date': info['date'], 'venue': info['venue']}
                        for mid, info in distinct_matches.items()
                    ]
                }

        embeddings_subset = embeddings[idxs]
        final_chunks_subset = [final_chunks[i] for i in idxs]
    else:
        embeddings_subset = embeddings
        final_chunks_subset = final_chunks

    expanded_query = expand_query(query)
    similarities = cosine_similarity(expanded_query, embeddings_subset)
    top_k_indices = np.argsort(similarities[0])[::-1][:top_k]

    results = []
    for idx in top_k_indices:
        chunk = final_chunks_subset[idx]
        similarity_score = similarities[0][idx]
        results.append((chunk, similarity_score))
    return results


if __name__ == "__main__":
    query = input("Enter your query: ")
    results = search(query, embeddings, final_chunks, top_k=6)

    if isinstance(results, dict) and results.get('ambiguous'):
        print(f"\nQuery: {query}")
        print("\nThis query matches more than one game. Which one did you mean?\n")
        for i, c in enumerate(results['candidates']):
            print(f"  {i+1}. {c['date']} at {c['venue']} (match_id: {c['match_id']})")
        print()
    else:
        print(f"Query: {query}\n")
        for i, (chunk, score) in enumerate(results):
            print(f"Result {i+1}:")
            print(f"Season: {chunk['season']}")
            print(f"Teams: {chunk['team1']} vs {chunk['team2']}")
            print(f"Content: {chunk['content'][:200]}...")
            print(f"Similarity Score: {score:.4f}\n")