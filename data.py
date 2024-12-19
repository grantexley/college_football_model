#!/usr/bin/env python3

import cfbd
from cfbd.rest import ApiException
from pprint import pprint
import os
import pandas as pd
import sys

def flatten_dict(d, parent_key='', sep='_'):
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def add_prefix_to_keys(d, prefix):
    return {f"{prefix}{key}": value for key, value in d.items()}

def get_team_names(client, year):
    team_api = cfbd.TeamsApi(client)
    try:
        teams = team_api.get_fbs_teams(year=year)
        team_names = [t.school for t in teams]
    except ApiException as e:
        print("Exception when calling TeamsApi->get_fbs_teams: %s\n" % e)
        raise e
    
    return team_names

def get_game_info(client, kwargs):
    game_api = cfbd.GamesApi(client)
    try:
        api_response = game_api.get_games(**kwargs)
        if not api_response: return None
        data = api_response[0].to_dict()
    except ApiException as e:
        print("Exception when calling GamesApi->get_games: %s\n" % e)
        raise e
    
    result = {key: val for key, val in data.items() if key in ['home_team', 'away_team', 'home_points', 'away_points']}
    return result
    
def get_game_ppa(client, kwargs):
    """
    Gets advanced predicted points added for passing, rushing and each down for a given game
    could be good for last 3 games
    """
    ppa_api = cfbd.MetricsApi(client)
    try:
        api_response = ppa_api.get_game_ppa(**kwargs)
    except ApiException as e:
        print("Exception when calling MetricsApi->get_game_ppa: %s\n" % e)
        raise e
    
    #TODO proccess ppa numbers
    # tips: 
    # you will prob have to use flattened_dict above. 
    # Use print statements
    # copy other functions, especially in the main
    
    
def get_season_stats(client, kwargs):
    stats_api = cfbd.StatsApi(client)
    
    if kwargs['end_week'] == 1:
        kwargs['end_week'] = 16
        kwargs['year'] -= 1
    
    try:
        api_response = stats_api.get_advanced_team_season_stats(**kwargs) 
        if not api_response: return None 
        stats = api_response[0].to_dict()
    except ApiException as e:
        print("Exception when calling StatsApi->get_advanced_team_season_stats: %s\n" % e)
        raise e
    
    offense_data = add_prefix_to_keys(flatten_dict(stats['offense']), "offense_")
    defense_data = add_prefix_to_keys(flatten_dict(stats['defense']), "defense_")
    data = offense_data | defense_data
    data = {key: value for key, value in data.items() if 'total' not in key or 'havoc' in key}
    del data['defense_drives']
    del data['defense_plays']
    del data['offense_drives']
    del data['offense_plays']
    
    return data

def save_df(games, output_file, debug):
    df = pd.DataFrame(games)
    df.to_csv(output_file, index=False)
    
    with open('debug.txt', 'w') as f:
        print(debug, file=f)
    
    
def main():
    config = cfbd.Configuration()
    config.api_key['Authorization'] = os.environ['CFBD_API_KEY']
    client = cfbd.ApiClient(config)
    
    seen_games = set()
    years = [int(x) for x in sys.argv[1:]]
    print(years)
    i = 0
    try:
        for year in years:
            games = []
            teams = get_team_names(client, year)
            for team in teams:
                for week in range(2, 16):
                    print(f'Processing game {i}')
                    
                    game_info = get_game_info(client, {'team': team, 'week': week, 'year': year, 'season_type': 'regular'})
                    
                    if not game_info: continue  
                    
                    if game_info['home_team'] not in teams or game_info['away_team'] not in teams: continue
                    
                    if (game_info['home_team'], game_info['away_team']) in seen_games:
                        continue
                    else:
                        seen_games.add((game_info['home_team'], game_info['away_team']))
                        
                        
                    ### Per Game Data Processing ### 
                    
                    home_stats = get_season_stats(client, {'year': year, 'team': game_info['home_team'], 'exclude_garbage_time': True, 'start_week': 1, 'end_week': week})
                    if not home_stats: 
                        print(f'no response for game {i} in home_stats')
                        continue
                    home_stats = add_prefix_to_keys(home_stats, 'home_')
                    
                    
                    away_stats = get_season_stats(client, {'year': year, 'team': game_info['away_team'], 'exclude_garbage_time': True, 'start_week': 1, 'end_week': week})
                    if not away_stats: 
                        print(f'no response for game {i} in away_stats')
                        continue
                    away_stats = add_prefix_to_keys(away_stats, 'away_')
                    
                    
                    game_data = home_stats | away_stats | game_info
                    games.append(game_data)
                    i += 1
                    # return # uncomment to debug with only first game 
            save_df(games, "cfp_data_" + str(year), {})
        
    except Exception as e:
        save_df(games, 'games_data.csv', {'year': year, 'team': team, 'week': week, 'exception': e})
        raise e
    
    print("EXITED WITHOUT ERROR")
    
    
"""
Ideas for move data:
- PPA numbers
- Stadium info
- Time info
- Weather info (might be behind paywall)
- away team travel distance
- player information 
"""    
    
if __name__ == '__main__':
    main()