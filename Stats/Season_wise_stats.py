import pandas as pd
deliveries = pd.read_parquet('parsed/deliveries.parquet')
def get_season_stats_batsman(season, player_name):
    season_deliveries_by_player = deliveries[(deliveries['season'] == season) & (deliveries['striker'] == player_name)]

    runs_scored = season_deliveries_by_player['runs_batter'].sum()
    balls_faced = season_deliveries_by_player['extras_type'].ne('wides').sum()  # <-- FIXED, same reasoning as above
    no_of_fours = season_deliveries_by_player[season_deliveries_by_player['runs_batter'] == 4].shape[0]
    no_of_sixes = season_deliveries_by_player[season_deliveries_by_player['runs_batter'] == 6].shape[0]
    strike_rate = (runs_scored / balls_faced) * 100 if balls_faced > 0 else 0

    no_of_dismissals = season_deliveries_by_player[season_deliveries_by_player['player_dismissed'] == player_name].shape[0]
    average = (runs_scored / no_of_dismissals) if no_of_dismissals > 0 else runs_scored

    per_match_runs = season_deliveries_by_player.groupby('match_id')['runs_batter'].sum()
    no_of_hundreds = (per_match_runs >= 100).sum()
    no_of_fifties = ((per_match_runs >= 50) & (per_match_runs < 100)).sum()  # cleaner than subtracting after the fact

    no_of_matches = season_deliveries_by_player['match_id'].nunique()
    no_of_not_outs = no_of_matches - no_of_dismissals

    return {
        'Number of Matches': no_of_matches,
        'Number of Not Outs': no_of_not_outs,
        'Runs Scored': runs_scored,
        'Balls Faced': balls_faced,
        'Number of Fours': no_of_fours,
        'Number of Sixes': no_of_sixes,
        'Strike Rate': strike_rate,
        'Number of Dismissals': no_of_dismissals,
        'Average': average,
        'Number of Fifties': no_of_fifties,
        'Number of Hundreds': no_of_hundreds
    }
def get_season_stats_bowler(season, player_name):
    season_deliveries_by_player = deliveries[(deliveries['season'] == season) & (deliveries['bowler'] == player_name)]
    no_of_matches = season_deliveries_by_player['match_id'].nunique()
    balls_bowled = season_deliveries_by_player['is_legal_delivery'].sum()  # unchanged -- correct concept for bowler's over count
    bowler_extras = season_deliveries_by_player['runs_extras'].where(season_deliveries_by_player['extras_type'].isin(['wides', 'noballs']), 0)
    runs_conceded = (season_deliveries_by_player['runs_batter'] + bowler_extras).sum()
    wickets_taken = season_deliveries_by_player['dismissal_credited_to_bowler'].sum()
    economy_rate = (runs_conceded / (balls_bowled / 6)) if balls_bowled > 0 else 0
    bowling_strike_rate = (balls_bowled / wickets_taken) if wickets_taken > 0 else 0
    average = (runs_conceded / wickets_taken) if wickets_taken > 0 else runs_conceded
    return {
        'Number of Matches': no_of_matches,
        'Balls Bowled': balls_bowled,
        'Runs Conceded': runs_conceded,
        'Wickets Taken': wickets_taken,
        'Economy Rate': economy_rate,
        'Bowler Extras': bowler_extras.sum(),
        'Bowling Strike Rate': bowling_strike_rate,
        'Average': average
    }


   