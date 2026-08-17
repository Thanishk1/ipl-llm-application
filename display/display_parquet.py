import pandas as pd

# Read entire file
df = pd.read_parquet("parsed/players.parquet")
cols=pd.DataFrame(df.columns, columns=['Columns'])
print(cols)