from enum import Enum
import redis
import json
from odds_producer import odds_data

class Flags(Enum):
    INSANE = "41-50+ CHANGE!"
    BIG = " 30 - 40 CHANGE"
    MEDIUM = " 15 - 29 CHANGE"
    SMALL = " 5 - 14 CHANGE"

def cache_data(r: redis.Redis, player_data: dict) -> None:
    """
    :param r: redis server
    :param player_data: data from odds_data()
    :return: None
    """
    r.set('odds', json.dumps(player_data)) #converts dictionary into json for r

    print("Here is the cached data!")
    return json.loads(r.get('odds'))


if __name__ == "__main__":
    cache_data(redis.Redis(host="localhost", port=6379), player_data=odds_data())