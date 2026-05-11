import os
import json
import httpx
import redis
import uvicorn
from fastapi import FastAPI
from dotenv import load_dotenv
load_dotenv()

# Cache Server
r = redis.Redis(host=os.environ.get("ELASTICACHE_ENDPOINT", "localhost"), port=6379)

#Endpoints AWS
ODDS_URL = os.environ.get("GET_ODDS", "localhost")
FLAGS_URL = os.environ.get("GET_FLAGS", "localhost")
app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/odds")
async def get_odds():
    response = httpx.get(ODDS_URL)
    print(response.status_code)
    print(response.text)
    return response.json()



@app.get("/flags")
async def get_flags():
    response = httpx.get(FLAGS_URL)
    return response.json()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
