import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from player_mapping.map_players import resolve_player_mention, get_team_for_player
from expand_query import ABBREV_MAP
from player_mapping.map_players import resolve_player_mention
import string
def extract(query, abbrev_map=ABBREV_MAP):
    words = query.split()
    teams = []
    season = None

    # First pass: find the season, since player->team lookup needs it
    for w in words:
        w_clean = w.strip(string.punctuation)
        if w_clean.isdigit() and len(w_clean) == 4:
            season = w_clean

    # Second pass: team abbreviations (existing logic)
    for w in words:
        w_clean = w.strip(string.punctuation)
        if w_clean.upper() in abbrev_map.keys():
            teams.append(abbrev_map[w_clean.upper()])

    # Third pass: player names -> resolve to team (NEW)
    # Check two-word phrases first (e.g. "Virat Kohli"), then single words (e.g. "Kohli")
    cleaned_words = [w.strip(string.punctuation) for w in words]
    for i in range(len(cleaned_words) - 1):
        two_word = f"{cleaned_words[i]} {cleaned_words[i+1]}"
        resolved_player = resolve_player_mention(two_word)
        if resolved_player:
            team = get_team_for_player(resolved_player, season)
            if team and team not in teams:
                teams.append(team)

    for w in cleaned_words:
        resolved_player = resolve_player_mention(w)
        if resolved_player:
            team = get_team_for_player(resolved_player, season)
            if team and team not in teams:
                teams.append(team)
    return teams if teams else None, season
