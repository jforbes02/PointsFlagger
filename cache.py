from enum import Enum
import redis
import json
from odds_producer import odds_data


class Flags(Enum):
    INSANE = "41 - 50+ CHANGE!"
    BIG = "30 - 40 CHANGE"
    MEDIUM = "15 - 29 CHANGE"
    SMALL = "5 - 14 CHANGE"

def cache_data(r: redis.Redis, player_data: dict) -> dict:
    """
    :param r: redis server
    :param player_data: data from odds_data()
    :return: cached data
    """
    r.set('odds', json.dumps(player_data))
    return json.loads(r.get('odds'))

def compare_odds(old: dict, new: dict) -> list:
    flags = []
    for player, new_odds in new.items():
        if player not in old:
            continue
        old_odds = old[player]
        for choice in ('over', 'under'):
            if choice not in old_odds or choice not in new_odds:
                continue
            diff = abs(new_odds[choice] - old_odds[choice])
            if diff >= 41:
                flag = Flags.INSANE
            elif diff >= 30:
                flag = Flags.BIG
            elif diff >= 15:
                flag = Flags.MEDIUM
            elif diff >= 5:
                flag = Flags.SMALL
            else:
                continue
            flags.append(f"{player} {choice}: {old_odds[choice]} -> {new_odds[choice]} ({flag.value})")
    return flags

def refresh_odds(r: redis.Redis) -> list:
    old_data = r.get('odds')
    new_data = odds_data()
    flags = []
    if old_data:
        flags = compare_odds(json.loads(old_data), new_data)
    cache_data(r, new_data) #holds the new data
    return flags

if __name__ == "__main__":
    cache_data(redis.Redis(host="localhost", port=6379), player_data=odds_data())