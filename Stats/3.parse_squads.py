"""
Extract playing-XI squads from raw Cricsheet JSON files.
Produces squads.parquet: one row per (season, team, player), deduplicated
across every match that team played that season.
"""

import json
from pathlib import Path
import pandas as pd


def parse_squads_from_file(filepath: Path) -> list:
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    info = data.get("info", {})
    raw_season = info.get("season")
    season = str(raw_season) if raw_season is not None else None

    rows = []
    for team, squad in info.get("players", {}).items():
        for player in squad:
            rows.append({
                "season": season,
                "team": team,
                "player_name": player,
            })
    return rows


def main(input_dir: str, output_path: str, seasons_filter: list = None):
    input_path = Path(input_dir)
    json_files = sorted(input_path.glob("*.json"))

    if seasons_filter:
        seasons_filter = set(seasons_filter)

    all_rows = []
    errors = []

    for fp in json_files:
        try:
            with open(fp, "r", encoding="utf-8") as f:
                data = json.load(f)
            s = str(data.get("info", {}).get("season"))
            if seasons_filter and s not in seasons_filter:
                continue
        except Exception as e:
            errors.append((fp.name, str(e)))
            continue

        try:
            rows = parse_squads_from_file(fp)
            all_rows.extend(rows)
        except Exception as e:
            errors.append((fp.name, str(e)))

    df = pd.DataFrame(all_rows)

    # Deduplicate: same player appears in a team's squad across many matches in a season
    df = df.drop_duplicates(subset=["season", "team", "player_name"]).reset_index(drop=True)

    df.to_parquet(output_path, index=False)

    print(f"Processed {len(json_files) - len(errors)} files, {len(errors)} errors")
    print(f"squads.parquet: {df.shape}")
    print(df.groupby(["season", "team"]).size().head(20))

    if errors:
        print("\nErrors:")
        for name, err in errors[:10]:
            print(f"  {name}: {err}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python parse_squads.py <input_dir> <output_path> [seasons_comma_separated]")
        sys.exit(1)
    seasons_arg = sys.argv[3].split(",") if len(sys.argv) > 3 else None
    main(sys.argv[1], sys.argv[2], seasons_filter=seasons_arg)