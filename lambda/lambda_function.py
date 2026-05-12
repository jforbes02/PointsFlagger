import redis
import os
import json
from cache import refresh_odds
from odds_producer import get_commence_times
from datetime import datetime, timezone


def get_redis():
    return redis.Redis(host=os.environ['ELASTICACHE_ENDPOINT'], port=6379, ssl=True, decode_responses=True)

def fetch_events_handler(event, context):
    r = get_redis()
    from odds_producer import fetch_plus_cache
    fetch_plus_cache(r)
    start, end = get_commence_times(r)
    r.set('game_window', json.dumps({
        'start': start.isoformat(),
        'end': end.isoformat()
    }))
    return {'statusCode': 200, 'message': "NBA games of the day cached"}


def lambda_handler(event, context):
    r = get_redis()
    window = r.get('game_window')

    if window:
        window = json.loads(window)
        now = datetime.now(timezone.utc)
        start = datetime.fromisoformat(window['start'])
        end = datetime.fromisoformat(window['end'])
        if not (start <= now <= end):
            return {'statusCode': 200, 'message': 'Outside game window'}

    flags = refresh_odds(r)
    r.set('flags', json.dumps(flags))
    return {'statusCode': 200, 'flags': flags}

def get_flags_handler(event, context):
    r = get_redis()
    data = r.get('flags')
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.loads(data) or '{}'
    }
def get_odds_handler(event, context):
    r = get_redis()
    data = r.get('odds')
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.loads(data) or '{}'
    }