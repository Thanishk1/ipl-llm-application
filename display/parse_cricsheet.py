"""
Parse raw Cricsheet match JSON files into three flat tables:
  - matches.parquet    (one row per match)
  - deliveries.parquet (one row per delivery, ball-by-ball)
  - players.parquet    (player name -> stable id registry, PLAYERS ONLY -- no umpires/officials)

Usage:
    python parse_cricsheet.py <input_dir_with_json_files> <output_dir> [seasons_comma_separated]
"""

import json
import sys
from pathlib import Path
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


def get_match_id(filepath: Path, info: dict) -> str:
    return filepath.stem


def parse_matches(match_id: str, info: dict) -> dict:
    outcome = info.get("outcome", {})
    winner = outcome.get("winner")

    win_by_type = None
    win_by_margin = None
    result_type = "normal"
    if "by" in outcome:
        by = outcome["by"]
        if "runs" in by:
            win_by_type, win_by_margin = "runs", by["runs"]
        elif "wickets" in by:
            win_by_type, win_by_margin = "wickets", by["wickets"]
    elif "result" in outcome:
        result_type = outcome["result"]
    elif "eliminator" in outcome:
        result_type = "eliminator"
        winner = outcome.get("eliminator")

    method = outcome.get("method")

    teams = info.get("teams", [None, None])
    toss = info.get("toss", {})
    pom = info.get("player_of_match", [])

    raw_season = info.get("season")
    season = str(raw_season) if raw_season is not None else None

    return {
        "match_id": match_id,
        "season": season,
        "date": info.get("dates", [None])[0],
        "venue": info.get("venue"),
        "city": info.get("city"),
        "team1": teams[0] if len(teams) > 0 else None,
        "team2": teams[1] if len(teams) > 1 else None,
        "toss_winner": toss.get("winner"),
        "toss_decision": toss.get("decision"),
        "winner": winner,
        "result_type": result_type,
        "win_by_type": win_by_type,
        "win_by_margin": win_by_margin,
        "method": method,
        "player_of_match": pom[0] if pom else None,
    }


def parse_deliveries(match_id: str, info: dict, innings_list: list) -> list:
    rows = []
    raw_season = info.get("season")
    season = str(raw_season) if raw_season is not None else None

    for inn_idx, innings in enumerate(innings_list, start=1):
        batting_team = innings.get("team")
        teams = info.get("teams", [])
        bowling_team = next((t for t in teams if t != batting_team), None)

        for over_block in innings.get("overs", []):
            over_num = over_block.get("over")

            for delivery in over_block.get("deliveries", []):
                extras = delivery.get("extras", {}) or {}
                runs = delivery.get("runs", {}) or {}

                extras_type = None
                if extras:
                    extras_type = next(iter(extras.keys()), None)
                is_legal_delivery = extras_type not in ("wides", "noballs")

                wickets = delivery.get("wickets", [])
                wicket_kind = None
                player_dismissed = None
                dismissal_credited_to_bowler = False
                if wickets:
                    w = wickets[0]
                    wicket_kind = w.get("kind")
                    player_dismissed = w.get("player_out")
                    dismissal_credited_to_bowler = wicket_kind in (
                        "caught", "bowled", "lbw", "stumped", "caught and bowled", "hit wicket"
                    )

                rows.append({
                    "match_id": match_id,
                    "season": season,
                    "innings": inn_idx,
                    "over": over_num,
                    "actual_delivery": delivery.get("actual_delivery"),
                    "batting_team": batting_team,
                    "bowling_team": bowling_team,
                    "striker": delivery.get("batter"),
                    "non_striker": delivery.get("non_striker"),
                    "bowler": delivery.get("bowler"),
                    "runs_batter": runs.get("batter", 0),
                    "runs_extras": runs.get("extras", 0),
                    "runs_total": runs.get("total", 0),
                    "extras_type": extras_type,
                    "is_legal_delivery": is_legal_delivery,
                    "wicket_kind": wicket_kind,
                    "player_dismissed": player_dismissed,
                    "dismissal_credited_to_bowler": dismissal_credited_to_bowler,
                })
    return rows


def parse_players(info: dict) -> list:
    """
    Returns ONLY actual playing squad members - excludes umpires, TV umpires,
    and match referees, which Cricsheet lumps together with players inside
    registry.people. info.players (grouped by team) is the ground truth for
    who actually played; we cross-reference against it before trusting a
    registry entry as a "player".
    """
    registry = info.get("registry", {}).get("people", {})

    actual_players = set()
    for team, squad in info.get("players", {}).items():
        actual_players.update(squad)

    return [
        {"player_name": name, "player_id": pid}
        for name, pid in registry.items()
        if name in actual_players
    ]


def parse_file(filepath: Path) -> tuple:
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    info = data.get("info", {})
    match_id = get_match_id(filepath, info)

    match_row = parse_matches(match_id, info)
    delivery_rows = parse_deliveries(match_id, info, data.get("innings", []))
    player_rows = parse_players(info)

    return match_row, delivery_rows, player_rows


DELIVERIES_SCHEMA_COLUMNS = [
    "match_id", "season", "innings", "over", "actual_delivery",
    "batting_team", "bowling_team", "striker", "non_striker", "bowler",
    "runs_batter", "runs_extras", "runs_total", "extras_type",
    "is_legal_delivery", "wicket_kind", "player_dismissed",
    "dismissal_credited_to_bowler",
]


def main(input_dir: str, output_dir: str, seasons_filter: list = None, batch_size: int = 25):
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    json_files = sorted(input_path.glob("*.json"))
    if not json_files:
        print(f"No .json files found in {input_dir}")
        return

    if seasons_filter:
        seasons_filter = set(seasons_filter)
        filtered_files = []
        for fp in json_files:
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    data = json.load(f)
                s = str(data.get("info", {}).get("season"))
                if s in seasons_filter:
                    filtered_files.append(fp)
            except Exception:
                continue
        print(f"Season filter {sorted(seasons_filter)}: {len(filtered_files)}/{len(json_files)} files match.")
        json_files = filtered_files
        if not json_files:
            print("No files left after season filtering. Check season strings (e.g. '2025' vs '2025/26').")
            return

    all_matches, all_players = [], {}
    errors = []

    deliveries_parquet_path = output_path / "deliveries.parquet"
    writer = None
    batch_rows = []

    def flush_batch(rows):
        nonlocal writer
        if not rows:
            return
        df = pd.DataFrame(rows, columns=DELIVERIES_SCHEMA_COLUMNS)
        table = pa.Table.from_pandas(df, preserve_index=False)
        if writer is None:
            writer = pq.ParquetWriter(deliveries_parquet_path, table.schema)
        writer.write_table(table)

    for i, fp in enumerate(json_files, start=1):
        try:
            match_row, delivery_rows, player_rows = parse_file(fp)
            all_matches.append(match_row)
            batch_rows.extend(delivery_rows)
            for p in player_rows:
                all_players[p["player_name"]] = p["player_id"]
        except Exception as e:
            errors.append((fp.name, str(e)))
            continue

        if i % batch_size == 0:
            flush_batch(batch_rows)
            batch_rows = []
            print(f"  ...processed {i}/{len(json_files)} files")

    flush_batch(batch_rows)
    if writer is not None:
        writer.close()

    matches_df = pd.DataFrame(all_matches)
    players_df = pd.DataFrame(
        [{"player_name": k, "player_id": v} for k, v in all_players.items()]
    )

    matches_df.to_parquet(output_path / "matches.parquet", index=False)
    players_df.to_parquet(output_path / "players.parquet", index=False)

    deliveries_row_count = pq.ParquetFile(deliveries_parquet_path).metadata.num_rows if writer is not None else 0

    print(f"\nParsed {len(json_files) - len(errors)}/{len(json_files)} files successfully.")
    print(f"matches.parquet:    {matches_df.shape}")
    print(f"deliveries.parquet: ({deliveries_row_count}, {len(DELIVERIES_SCHEMA_COLUMNS)})")
    print(f"players.parquet:    {players_df.shape}")
    if errors:
        print(f"\n{len(errors)} files failed to parse:")
        for name, err in errors[:10]:
            print(f"  {name}: {err}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python parse_cricsheet.py <input_dir> <output_dir> [seasons_comma_separated]")
        print("Example: python parse_cricsheet.py cricsheet_raw parsed 2025,2025/26,2026")
        sys.exit(1)
    seasons_arg = sys.argv[3].split(",") if len(sys.argv) > 3 else None
    main(sys.argv[1], sys.argv[2], seasons_filter=seasons_arg)