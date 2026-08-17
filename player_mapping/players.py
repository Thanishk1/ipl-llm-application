import pandas as pd

deliveries = pd.read_parquet("parsed/deliveries.parquet")

# A player could appear as striker, non_striker, or bowler -- we need every
# (player, season, team) combination they were involved in, across all three roles.
striker_teams = deliveries[['striker', 'season', 'batting_team']].rename(
    columns={'striker': 'player', 'batting_team': 'team'})
bowler_teams = deliveries[['bowler', 'season', 'bowling_team']].rename(
    columns={'bowler': 'player', 'bowling_team': 'team'})

player_team_df = pd.concat([striker_teams, bowler_teams]).drop_duplicates()

# Build a dict: (player, season) -> team
player_team_map = {}
for _, row in player_team_df.iterrows():
    player_team_map[(row['player'], row['season'])] = row['team']

print(len(player_team_map))
print(player_team_map.get(("V Kohli", "2025")))