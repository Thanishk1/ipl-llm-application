import pandas as pd
sq = pd.read_parquet('parsed/squads.parquet')
squads = pd.read_parquet("parsed/squads.parquet")
print(squads[(squads['season']=='2026') & (squads['team']=='Royal Challengers Bengaluru')]['player_name'].tolist())
squads = pd.read_parquet("parsed/squads.parquet")
print(squads.shape)
print(squads['team'].unique())