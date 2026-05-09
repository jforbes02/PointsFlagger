import os

from dotenv import load_dotenv
import requests
from datetime import datetime, timezone
load_dotenv()

API_KEY = os.environ.get("ODDS_KEY")
SPORT = "basketball_nba"
REGION = 'us'
ODDS_FORMAT = 'american'
DATE_FORMAT = 'unix'
MARKET = 'player_points'


def fetch_events() -> list[dict]:
    """ fetch events from odds api """
    today = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    events_response = requests.get(f'https://api.the-odds-api.com/v4/sports/{SPORT}/events', params={
        'api_key': API_KEY,
        'dateFormat': DATE_FORMAT,
        'commenceTimeFrom': today,
    })

    return events_response.json()

def get_earliest_commence_time() -> datetime:
    """ fetch earliest NBA commence time """
    events = fetch_events()
    earliest = min(events, key=lambda e: e['commence_time'])
    return earliest['commence_time']

def odds_data() -> dict:
    """ fetch odds data for three games from odds api from the events we fetched from the odds api"""
    events = fetch_events()
    if not events:
        raise ValueError(f"No nba events found from odds api today: {events}")

    odds_dict = {} #holds player odds

    for event in events[:3]: #3 games to limit API calls for now
        event_id = event['id'] #unique id for each event for odds_response

        try:
            odds_response = requests.get( #collects the information needed
                f'https://api.the-odds-api.com/v4/sports/{SPORT}/events/{event_id}/odds',
                params={
                    'api_key': API_KEY,
                    'regions': REGION,
                    'markets': MARKET,
                    'oddsFormat': ODDS_FORMAT,
                    'dateFormat': DATE_FORMAT,
                },
                timeout=10 #10 seconds to fetch
            )
            odds_response.raise_for_status()
        except requests.exceptions.Timeout:
            print(f"Timeout while fetching odds data for {event_id}")
            continue
        except requests.exceptions.RequestException as e:
            print(f"Error while fetching odds data for {event_id}: {e}")
            continue

        for bookmaker in odds_response.json()['bookmakers']:
            if bookmaker['key'] != 'fanduel': #filters only fanduel odds
                continue
            for out in bookmaker['markets'][0]['outcomes']: #loop through each Over/Under
                player = out['description']
                if player not in odds_dict:
                    odds_dict[player] = {} #  If we haven't seen this player yet, create an empty dict entry for them.
                if out['name'] == 'Over':
                    odds_dict[player]['over'] = out['price']
                    odds_dict[player]['point'] = out['point'] #point threshold for the player
                else:
                    odds_dict[player]['under'] = out['price']
    return odds_dict

#print(fetch_events())


if __name__ == "__main__":
    odds_data()