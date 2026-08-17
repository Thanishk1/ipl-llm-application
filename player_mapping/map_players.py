import json
import re
from collections import Counter, defaultdict
import pandas as pd

# ---- 1. Load base player names from Cricsheet ----
players_df = pd.read_parquet("parsed/players.parquet")
player_names = players_df['player_name'].tolist()  # e.g. 'JM Sharma', 'V Kohli'

# ---- 2. Load report text corpus ----
with open("ipl_all_reports.json", "r", encoding="utf-8") as f:
    all_reports = json.load(f)
all_text = " ".join(r['report_text'] for r in all_reports)


# ---- 3. For each Cricsheet name, find its full first name in report text,
#          filtered by FIRST INITIAL so a famous namesake can't hijack the match ----
def find_full_name(cricsheet_name, all_text):
    parts = cricsheet_name.split()
    surname = parts[-1]
    initials_part = parts[0]
    first_initial = initials_part[0]

    # If the stored name already looks like a real first name (not bare initials,
    # e.g. "Suyash Sharma" rather than "JM Sharma"), trust it as-is.
    if len(initials_part) > 1 and initials_part[1:].islower():
        return cricsheet_name

    pattern = r'\b([A-Z][a-z]+)\s+' + re.escape(surname) + r'\b'
    matches = re.findall(pattern, all_text)
    if not matches:
        return None

    # Keep only candidates whose first letter matches the known initial
    filtered = [m for m in matches if m[0] == first_initial]
    if not filtered:
        return None

    counts = Counter(filtered)
    ranked = counts.most_common()
    top_name, top_count = ranked[0]

    # If two DIFFERENT names both start with this initial and tie in frequency,
    # refuse rather than guess
    if len(ranked) > 1 and ranked[1][1] == top_count:
        return None

    return f"{top_name} {surname}"


# ---- 4. Build the alias table: full name (lowercase) -> Cricsheet stored name ----
ALIAS_MAP = {}
unresolved = []

for name in player_names:
    full_name = find_full_name(name, all_text)
    if full_name:
        ALIAS_MAP[full_name.lower()] = name
    else:
        unresolved.append(name)


# ---- 5. Surname-only fallback, for bare-surname queries ----
surname_map = defaultdict(list)
for name in player_names:
    surname_map[name.split()[-1]].append(name)


def resolve_player_mention(text_snippet):
    """
    text_snippet: a word or two-word phrase from a query, e.g. "Krunal Pandya" or "Pandya"
    Returns the matching Cricsheet player name, or None if unresolved/ambiguous.
    """
    snippet_lower = text_snippet.lower().strip()
    if snippet_lower in ALIAS_MAP:
        return ALIAS_MAP[snippet_lower]
    last_word = text_snippet.split()[-1].capitalize()
    candidates = surname_map.get(last_word, [])
    if len(candidates) == 1:
        return candidates[0]
    first_candidates = first_name_map.get(snippet_lower, [])
    if len(first_candidates) == 1:
        return first_candidates[0]
    return None  # ambiguous or unknown -- refuse rather than guess
# ---- 6. Build (player, season) -> team lookup from deliveries ----
deliveries = pd.read_parquet("parsed/deliveries.parquet")

striker_teams = deliveries[['striker', 'season', 'batting_team']].rename(
    columns={'striker': 'player', 'batting_team': 'team'})
bowler_teams = deliveries[['bowler', 'season', 'bowling_team']].rename(
    columns={'bowler': 'player', 'bowling_team': 'team'})

player_team_df = pd.concat([striker_teams, bowler_teams]).drop_duplicates()

player_team_map = {}
for _, row in player_team_df.iterrows():
    player_team_map[(row['player'], row['season'])] = row['team']

# ---- 7. First-name index, built from ALIAS_MAP ----
first_name_map = defaultdict(list)
for full_name, cricsheet_name in ALIAS_MAP.items():
    first_word = full_name.split()[0]
    if cricsheet_name not in first_name_map[first_word]:
        first_name_map[first_word].append(cricsheet_name)
# ---- 8. Reverse index: player -> every team they've ever played for ----
player_all_teams = defaultdict(set)
for (player, season), team in player_team_map.items():
    player_all_teams[player].add(team)

def get_team_for_player(cricsheet_name, season=None):
    """
    Returns the player's team. If season is given, looks up that exact season.
    If season is None, only returns a team if the player has played for
    exactly ONE team across all seasons in the data -- otherwise refuses
    rather than guess.
    """
    if season is not None:
        return player_team_map.get((cricsheet_name, season))

    teams = player_all_teams.get(cricsheet_name, set())
    if len(teams) == 1:
        return next(iter(teams))
    return None  # played for multiple teams, or unknown -- don't guess