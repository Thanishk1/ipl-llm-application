import pandas as pd
deliveries = pd.read_parquet('parsed/deliveries.parquet')


def get_batsman_stats(match_id, player_name):
    condition = (deliveries['match_id'] == match_id) & (deliveries['striker'] == player_name)
    match = deliveries[condition]

    runs_scored = match['runs_batter'].sum()
    balls_faced = match['extras_type'].ne('wides').sum()  # <-- FIXED: was is_legal_delivery, now excludes only wides
    no_of_fours = match[match['runs_batter'] == 4].shape[0]
    no_of_sixes = match[match['runs_batter'] == 6].shape[0]
    strike_rate = (runs_scored / balls_faced) * 100 if balls_faced > 0 else 0

    dismissal_kind = None
    dismissal_bowler = None
    dismissal_row = match[match['player_dismissed'] == player_name]
    is_dismissed = not dismissal_row.empty
    if is_dismissed:
        dismissal_kind = dismissal_row['wicket_kind'].values[0]
        dismissal_bowler = dismissal_row['bowler'].values[0]

    return {
        'Runs Scored': runs_scored,
        'Balls Faced': balls_faced,
        'Number of Fours': no_of_fours,
        'Number of Sixes': no_of_sixes,
        'Strike Rate': strike_rate,
        'Is Dismissed': is_dismissed,
        'Dismissal Kind': dismissal_kind,
        'Dismissal Bowler': dismissal_bowler
    }


def get_bowler_stats(match_id, player_name):
    condition = (deliveries['match_id'] == match_id) & (deliveries['bowler'] == player_name)
    match = deliveries[condition]

    balls_bowled = match['is_legal_delivery'].sum()  # unchanged -- correct concept for bowler's over count
    bowler_extras = match['runs_extras'].where(match['extras_type'].isin(['wides', 'noballs']), 0)
    runs_conceded = (match['runs_batter'] + bowler_extras).sum()
    wickets_taken = match['dismissal_credited_to_bowler'].sum()
    economy_rate = (runs_conceded / (balls_bowled / 6)) if balls_bowled > 0 else 0

    return {
        'Balls Bowled': balls_bowled,
        'Runs Conceded': runs_conceded,
        'Wickets Taken': wickets_taken,
        'Economy Rate': economy_rate,
        'Bowler Extras': bowler_extras.sum()
    }

