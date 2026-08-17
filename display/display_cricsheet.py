import pandas as pd

df = pd.read_parquet(r"D:\IPL_VISUALISATION\cricsheet_ipl_2025_2026.parquet")

print(df.shape)
print(df.columns.tolist())
print(df.dtypes)
df.head(10)