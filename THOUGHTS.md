# DAY 1
This project is for me to learn AWS, specifically Lambda, TimeStream, and Kinesis

The main idea of this project is to have a website that can do these tasks.

1. Showcase the odds of NBA players (start off with points expand in future)
2. Detect large(undefined) movements in odds and flag them
3. (Far Future, not in the MVP) Provide an ai explanation of why the odd changed. Maybe like a chatbot thingy

I want to learn AWS and will write notes down in this md

### Data Analysis
- I think that Kinesis is the best for this (least knowledge on this aspect)

### Database
- Willing to learn TimeStream
- It seems useful for this Project as it is very fast (will be costly though)

### API
- I plan on using the odds-api API free tier
- Will learn Redis in order to not get killed by rate limits
- I think I should use Lambda to clean and process the data

### Full Stack
- FastAPI 
- Lambda
- TimeStream
- Kinesis
- React
- https://the-odds-api.com/ (api for odds)

So im going to start with creating the logic first

The main questions I need to answer for this part is
    - "How will I be able to detect when a line moves" 
    - "What movement determines a significant enough amount to flag"

# DAY 2
I have started messing around with the api
Right now i learned how to get the data for player points that I want
I'm going to focus on points odds for now

````
def odds_data():
    for event in events[:3]:
        event_id = event['id']
        odds_response = requests.get(
            f'https://api.the-odds-api.com/v4/sports/{SPORT}/events/{event_id}/odds',
            params={
                'api_key': API_KEY,
                'regions': REGION,
                'markets': MARKET,
                'oddsFormat': ODDS_FORMAT,
                'dateFormat': DATE_FORMAT,
            }
        )

        print(odds_response.json())
````
This provides for me three of the events with all of the player points props

Now im thinking about how to detect changes in the api without having a large api usage.

1. I can create an async listener that is listening in on odds 
2. I know that sometimes the book makers will take odds back to change them so that could be something I look for ?
3. Have the data cached, then press a button to detect changes (kinda off course of what I want but interesting route)(saves api usage however)
4. HUGE - maybe I make it listen to the daily player point props, every 5 minutes or so it peeks in at points again and compares them to the cached props

Since I have limited API requests i think that 4 might be the best option, instead of every 5 minutes it would prob be like every 30 minutes~1 hour
In order to conserve I can also add 3 into it where in order to start the actual hourly task you would press a button for that day

I put this info into claude and was alerted about transient blips so that may be something I should look out for.

### PLAN
- First create a function that will loop and whenever the function is ran then it will compare player props.
- Learn how to use caching
- Create a rule that will replace the prop based on odds


### SubTopic - LifeSpans
- Lifepans are the modern version of .onevent(startup)/on_event(shutdown)
- Apps have single lifespans of startup and ending events
- uses @asynccontextmanager
- runs everything in lifespan up to "yield" as startups and after as shutdowns

# Day 3
Last night I was thinking about how to get "useful" data with the least amount of requests then I had an idea

It would be smart if instead of hourly checks (24 checks a day)
Check every 10 minutes during games and have the api not be called if it's not during a game

What I did was I created two functions one that gets events and one that gets the earliest event for the day

```
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
```

### EventBridge
- Found out that I can use EventBridge with AWS over apschedular

# Day 4
Finished my finals today so now I will have more time to work on this project.

I worked on the odds_data function and have been able to produce a function that provides a dictionary of the player over and under props

# Odds_Data
```
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
```

My thought process was
1. I need to get the events
2. I need to parse through the events while not heavily using my API requests
3. I need to create my own data that doesn't include the fluff from the API (only props and player names)

This function does all of these with the help of some helper functions

Some things brought to my attention are that I may want to split these up into multiple dictionaries for team names??
I think for MVP i don't need team names however I may add it in the future.
I think I will end up showcasing the data on the frontend based on either order or highest 'point' line descending

i think it would make sense for the next step to be implementing the cache and then having a system that compares the cache to a new call of odds_data

### REDIS

Learning Redis
- Redis server is needed
- .set() is what writes to Redis
- My data is in a dictionary but Redis doesn't take dictionaries
- I need to find a way to either
  - Convert it into useable data
  - Get the individual data from the dicts cached
- I think that it would make more sense to transform the data since all of the data is going to be cached and compared

Important Redis Functions
- redis.set (sets key value pair)
- redis.get (gets value from key)
- redis.Redis (server startup)

Now I have the data in Redis

```
127.0.0.1:6379> GET odds
{
  "Jaxson Hayes": {
    "over": -128,
    "point": 4.5,
    "under": 100
  },
  "Cason Wallace": {
    "over": -111,
    "point": 6.5,
    "under": -115
  },
  "Luguentz Dort": {
    "over": -111,
    "point": 6.5,
    "under": -115
  },
  "LeBron James": {
    "over": 100,
    "point": 22.5,
    "under": -128
  },
  "Jared McCain": {
    "over": -111,
    "point": 6.5,
    "under": -115
  },
  "Alex Caruso": {
    "over": -106,
    "point": 6.5,
    "under": -120
  },
  "Ajay Mitchell": {
    "over": -111,
    "point": 16.5,
    "under": -115
  },
  "Marcus Smart": {
    "over": -104,
    "point": 11.5,
    "under": -122
  },
  "Luke Kennard": {
    "over": 104,
    "point": 8.5,
    "under": -132
  },
  "Jake LaRavia": {
    "over": -106,
    "point": 3.5,
    "under": -120
  },
  "Isaiah Hartenstein": {
    "over": -125,
    "point": 7.5,
    "under": -102
  },
  "Chet Holmgren": {
    "over": -125,
    "point": 16.5,
    "under": -102
  },
  "Rui Hachimura": {
    "over": -113,
    "point": 13.5,
    "under": -113
  },
  "Deandre Ayton": {
    "over": -102,
    "point": 9.5,
    "under": -125
  },
  "Shai Gilgeous-Alexander": {
    "over": -104,
    "point": 29.5,
    "under": -122
  },
  "Austin Reaves": {
    "over": -120,
    "point": 21.5,
    "under": -106
  },
  "Paul George": {
    "over": -108,
    "point": 17.5,
    "under": -122
  },
  "VJ Edgecombe": {
    "over": 100,
    "point": 12.5,
    "under": -132
  },
  "Quentin Grimes": {
    "over": -106,
    "point": 6.5,
    "under": -125
  },
  "Kelly Oubre Jr": {
    "over": -106,
    "point": 12.5,
    "under": -125
  },
  "Josh Hart": {
    "over": 100,
    "point": 12.5,
    "under": -132
  },
  "Miles McBride": {
    "over": -102,
    "point": 9.5,
    "under": -130
  },
  "Tyrese Maxey": {
    "over": -106,
    "point": 25.5,
    "under": -125
  },
  "Mikal Bridges": {
    "over": 100,
    "point": 15.5,
    "under": -132
  },
  "Mitchell Robinson": {
    "over": -108,
    "point": 4.5,
    "under": -122
  },
  "Joel Embiid": {
    "over": 100,
    "point": 25.5,
    "under": -132
  },
  "Karl-Anthony Towns": {
    "over": -114,
    "point": 19.5,
    "under": -114
  },
  "Jalen Brunson": {
    "over": -125,
    "point": 26.5,
    "under": -106
  },
  "Julian Champagnie": {
    "over": -102,
    "point": 8.5,
    "under": -130
  },
  "Julius Randle": {
    "over": -122,
    "point": 17.5,
    "under": -108
  },
  "Dylan Harper": {
    "over": -114,
    "point": 10.5,
    "under": -114
  },
  "Anthony Edwards": {
    "over": -112,
    "point": 25.5,
    "under": -118
  },
  "Victor Wembanyama": {
    "over": -125,
    "point": 25.5,
    "under": -106
  },
  "Keldon Johnson": {
    "over": -130,
    "point": 8.5,
    "under": -102
  },
  "Jaden McDaniels": {
    "over": -114,
    "point": 15.5,
    "under": -114
  },
  "Rudy Gobert": {
    "over": -102,
    "point": 8.5,
    "under": -130
  },
  "Devin Vassell": {
    "over": -130,
    "point": 11.5,
    "under": -102
  },
  "Stephon Castle": {
    "over": -125,
    "point": 16.5,
    "under": -106
  },
  "Terrence Shannon Jr.": {
    "over": -130,
    "point": 7.5,
    "under": -102
  },
  "De'Aaron Fox": {
    "over": -108,
    "point": 17.5,
    "under": -122
  },
  "Naz Reid": {
    "over": -130,
    "point": 11.5,
    "under": -102
  },
  "Ayo Dosunmu": {
    "over": -128,
    "point": 11.5,
    "under": -104
  }
}
```

DEFINIETLY RAN OUT OF API REQUEST LOL!


# DAY 5

Worked on fixing some problems with async

In odds_producer I realized that fetch_events() would get called each time odds_data() was called so I used a python cache
I decided to create an events_cache that holds the data from fetch_events() and is called every day at midnight
This information isn't needed to be accessed fast so I put it in a list

In main I realized there was some issues with AsyncSchedulers compatibility with lambda functions
in response I created refresh_events and refresh_odds_job
refresh_events gets the event for the day

Now im going to create the comparison functionality along with flagging

### Comparison + Flagging
- Im thinking that we iterate through both dictionaries and whenever a key with value is changed we calculate by how much and then give it a Flag

```
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
```

I think right now im pretty set on the backed prior to AWS implementation
Im going to take a break and then work on the frontend

# DAY 6

Going to go with React Frontend, should be simple

Singular page that will just showcase the data

using vite to install typescript

So I sparked up a simple frontend that shows the basics that I want

Im going to implement setInterval in order for the data to match the scheduler
```
useEffect(() => {
    async function fetchData() {
      try {
        const [oddsRes, flagsRes] = await Promise.all([
          fetch('/api/odds'),
          fetch('/api/flags'),
        ])
        const oddsJson = await oddsRes.json()
        const flagsJson = await flagsRes.json()
        setOdds(oddsJson)
        setFlags(flagsJson.flags)
      } catch (e) {
        setError('Failed to fetch data. Is the server running?')
      } finally {
        setLoading(false)
      }
    }
    fetchData()
    const interval = setInterval(fetchData, 10 * 60 * 1000)
    return () => clearInterval(interval)
  }, [])

```

Some things that I have been thinking about 
Last nights games I got this error a few times Error while fetching odds data for 40c8a29efb894c4dd6bf6acc5025c9cb: 404 Client Error: Not Found for url: https://api.the-odds-api.com/v4/sports/basketball_nba/events/40c8a29efb894c4dd6bf6acc5025c9cb/odds?api_key=2b077cd2b44ffe4bb5d070e92a6d04c5&regions=us&markets=player_points&oddsFormat=american&dateFormat=unix
Error while fetching odds data for 878243c543236baba132ad43ae333aae: HTTPSConnectionPool(host='api.the-odds-api.com', port=443): Max retries exceeded with url: /v4/sports/basketball_nba/events/878243c543236baba132ad43ae333aae/odds?api_key=2b077cd2b44ffe4bb5d070e92a6d04c5&regions=us&markets=player_points&oddsFormat=american&dateFormat=unix (Caused by NameResolutionError("HTTPSConnection(host='api.the-odds-api.com', port=443): Failed to resolve 'api.the-odds-api.com' ([Errno 8] nodename nor servname provided, or not known)"))
Error while fetching odds data for 77e60e525f42e8337027f550bcd2f1cc: HTTPSConnectionPool(host='api.the-odds-api.com', port=443): Max retries exceeded with url: /v4/sports/basketball_nba/events/77e60e525f42e8337027f550bcd2f1cc/odds?api_key=2b077cd2b44ffe4bb5d070e92a6d04c5&regions=us&markets=player_points&oddsFormat=american&dateFormat=unix (Caused by NameResolutionError("HTTPSConnection(host='api.the-odds-api.com', port=443): Failed to resolve 'api.the-odds-api.com' ([Errno 8] nodename nor servname provided, or not known)"))
Error while fetching odds data for b537062ee0483d20ae932052628b663d: HTTPSConnectionPool(host='api.the-odds-api.com', port=443): Max retries exceeded with url: /v4/sports/basketball_nba/events/b537062ee0483d20ae932052628b663d/odds?api_key=2b077cd2b44ffe4bb5d070e92a6d04c5&regions=us&markets=player_points&oddsFormat=american&dateFormat=unix (Caused by NameResolutionError("HTTPSConnection(host='api.the-odds-api.com', port=443): Failed to resolve 'api.the-odds-api.com' ([Errno 8] nodename nor servname provided, or not known)"))
Error while fetching odds data for 878243c543236baba132ad43ae333aae: HTTPSConnectionPool(host='api.the-odds-api.com', port=443): Max retries exceeded with url: /v4/sports/basketball_nba/events/878243c543236baba132ad43ae333aae/odds?api_key=2b077cd2b44ffe4bb5d070e92a6d04c5&regions=us&markets=player_points&oddsFormat=american&dateFormat=unix (Caused by NameResolutionError("HTTPSConnection(host='api.the-odds-api.com', port=443): Failed to resolve 'api.the-odds-api.com' ([Errno 8] nodename nor servname provided, or not known)"))
Error while fetching odds data for 77e60e525f42e8337027f550bcd2f1cc: HTTPSConnectionPool(host='api.the-odds-api.com', port=443): Max retries exceeded with url: /v4/sports/basketball_nba/events/77e60e525f42e8337027f550bcd2f1cc/odds?api_key=2b077cd2b44ffe4bb5d070e92a6d04c5&regions=us&markets=player_points&oddsFormat=american&dateFormat=unix (Caused by NameResolutionError("HTTPSConnection(host='api.the-odds-api.com', port=443): Failed to resolve 'api.the-odds-api.com' ([Errno 8] nodename nor servname provided, or not known)"))
Error while fetching odds data for b537062ee0483d20ae932052628b663d: HTTPSConnectionPool(host='api.the-odds-api.com', port=443): Max retries exceeded with url: /v4/sports/basketball_nba/events/b537062ee0483d20ae932052628b663d/odds?api_key=2b077cd2b44ffe4bb5d070e92a6d04c5&regions=us&markets=player_points&oddsFormat=american&dateFormat=unix (Caused by NameResolutionError("HTTPSConnection(host='api.the-odds-api.com', port=443): Failed to resolve 'api.the-odds-api.com' ([Errno 8] nodename nor servname provided, or not known)"))

I might need to increase the time between calls

Also, I wonder if I should clear the cache after the last game of the day, but Then it would be a little trash for someone to come on the website and see nothing

### AWS

Now im going to be diving into a bunch of use cases and videos about AWS and see if and how I could implement them into this project.

1. Cloudwatch + Lambda
   - Serverless CRON jobs
   - Potentially replaces apscheduler if I understand correctly
2. SQS + Lambda
   - Can be used for notification service for huge changes in data
3. ElastiCache
   - Found out that Redis needs to be converted to ElastiCache in order to go AWS
   - In order for elasticache I need a VPC
4. EC2
   - EC2 is used to store security groups
   - Security group is a firewall that controls what traffic goes in and out
   - Basically we are going to say allow connections to Redis port "6379"

### VPC
- VPCs are private clouds

### ElastiCache
- I created my first ElastiCache instance
- Created a security group that will allow ElastiCache and Lambda to communicate


### Lambda
- A Lambda function is a piece of code triggered by something

# DAY 7
Continuing to work on AWS
Im trying to get a lambda version of refresh_odds so that it can utilize ElastiCache but I am getting errors.

I have to switch from using a local events_cache: list[dict] = []

Was dealing with some bugs with lambda but I got Redis to work with Lambda


Ive learned with Lambda the Runtime Settings are important, all lambda handler function are in one file but the Runtime Settings handler setting determines which function will be ran

VPCs dont have internet so a NAT gateway is needed!

I got both of the functions to work now

### NAT, VPC, Lambda, Route Tables, Subnets
- In this project I decided to utilize Redis so ElastiCache is a must if I want to implement AWS 
- While creating my first Lambda functions there was a few issues with testing errors
- NATs are Network Address Translation's
- These allow for internet access for multiple tools in the VPC (VPC inherently don't have internet)
- Subnets are parts of the VPC 
- Public Subnets use the Internet Gateway to access the internet
- Private Subnets go through the NAT gateway where AWS services like Lambda and Elasticache live
- For outside the VPC requests Route Tables are used for outside traffic from instances like odds-api


Now Im going to implement the scheduling by using 

### EventBridge
- EventBridge is super easy to use
- You create the schedule then implement it with Lambda Invoke
- 

###Lambda
- The Lambda Functions are working

So im starting to realize that not much code is needed in my main.py
The workflow is interesting because its
EventBridge → Lambda → ElastiCache → FastAPI

The FastApi server doesn't ever come in contact with lambda which is pretty cool to me

Tried to run the fastapi server endpoints but infinite loop

I asked Claude why this is and it say that I may benefit from creating lambdas that get the elasticache data
then connecting the fastapi to that which makes sense to me.

When using Lambda Functions the return should be in this format
```
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': data or '{}'
    }
```
My endpoint wasn't working but now it is


Okay so I got the website to work now its time for deployment

Im going to be using Render to deploy the backend Vercel for frontend