from flask import Flask, request, jsonify, render_template
import pandas as pd
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'Stats'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'rag'))

from Stats.Season_wise_stats import get_season_stats_batsman, get_season_stats_bowler
from Rag.rag import search, embeddings, final_chunks
from Rag.llm_integrtion import generate

app = Flask(__name__)

squads = pd.read_parquet("parsed/squads.parquet")

TEAMS = [
    "Chennai Super Kings", "Mumbai Indians", "Royal Challengers Bengaluru",
    "Kolkata Knight Riders", "Delhi Capitals", "Punjab Kings",
    "Rajasthan Royals", "Sunrisers Hyderabad", "Gujarat Titans", "Lucknow Super Giants"
]

SEASONS = ["2023", "2024", "2025", "2026"]


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/api/teams')
def get_teams():
    return jsonify(TEAMS)


@app.route('/api/seasons')
def get_seasons():
    return jsonify(SEASONS)


@app.route('/api/squad')
def get_squad():
    team = request.args.get('team')
    season = request.args.get('season')
    players = squads[(squads['team'] == team) & (squads['season'] == season)]['player_name'].tolist()
    return jsonify(players)


@app.route('/api/batsman_stats')
def batsman_stats():
    season = request.args.get('season')
    player = request.args.get('player')
    try:
        stats = get_season_stats_batsman(season, player)
        # convert numpy int64/float64 types to plain Python types so jsonify doesn't choke
        stats = {k: (v.item() if hasattr(v, 'item') else v) for k, v in stats.items()}
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route('/api/bowler_stats')
def bowler_stats():
    season = request.args.get('season')
    player = request.args.get('player')
    try:
        stats = get_season_stats_bowler(season, player)
        stats = {k: (v.item() if hasattr(v, 'item') else v) for k, v in stats.items()}
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route('/api/ask', methods=['POST'])
def ask():
    data = request.get_json()
    query = data.get('query', '')
    match_id = data.get('match_id')  # present only when the user picked a candidate match
    try:
        if match_id is not None:
            results = search(query, embeddings, final_chunks, top_k=5, match_id=int(match_id))
            answer = generate(query, results)
            return jsonify({"answer": answer})

        results = search(query, embeddings, final_chunks, top_k=5)

        # search() returns a dict instead of a list when the query matches
        # more than one game (e.g. "RCB vs MI 2026" matched two matches).
        # Handle that case separately instead of passing it to generate().
        if isinstance(results, dict) and results.get('ambiguous'):
            return jsonify({
                "ambiguous": True,
                "candidates": results['candidates']
            })

        answer = generate(query, results)
        return jsonify({"answer": answer})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)