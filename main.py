import logging
from contextlib import asynccontextmanager
import json
import redis
import uvicorn
from apscheduler.schedulers.async_ import AsyncScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import FastAPI

from cache import refresh_odds
from odds_producer import get_commence_times, fetch_events, events_cache

# Cache Server
r = redis.Redis(host="localhost", port=6379)

# App Startup functionality
def refresh_events():
    events = fetch_events()
    events_cache.clear()
    events_cache.extend(events)
    print("New Day, Refreshing events")

def refresh_odds_job():
    global latest_flags
    latest_flags = refresh_odds(r)
    print("New Day, Refreshing odds")

latest_flags = []
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncScheduler() as scheduler:
        """ in future add aws setups """
        refresh_events()
        refresh_odds(r)
        start, end = get_commence_times()
        await scheduler.add_schedule(refresh_odds_job, IntervalTrigger(minutes=10, start_time=start, end_time=end))
        await scheduler.add_schedule(refresh_events, CronTrigger(hour=0))

        yield

#Endpoints
app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/odds")
async def get_odds():
    data = r.get("odds")
    if data is None:
        return {"message": "No odds data found"}
    print("Heres cached odds data")
    return json.loads(data)

@app.get("/flags")
async def get_flags():
    return {"flags": latest_flags}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
