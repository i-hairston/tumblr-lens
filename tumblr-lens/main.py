
from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
import os
import requests

app = FastAPI()
client = MongoClient(os.getenv('MONGODB_URI', 'mongodb://localhost:27017/'))
db = client['your_database_name']
followers_collection = db['followers']

TUMBLR_API_BASE_URL = 'https://api.tumblr.com/v2/blog/{}/followers'

@app.get("/followers/{source_blog}")
async def get_followers(source_blog: str):
    cached_followers = followers_collection.find_one({"source_blog": source_blog})
    if cached_followers:
        return {"followers": cached_followers["followers"]}

    source_access_token = os.getenv('SOURCE_ACCESS_TOKEN')
    headers = {
        'Authorization': f'Bearer {source_access_token}',
    }

    try:
        response = requests.get(TUMBLR_API_BASE_URL.format(source_blog), headers=headers)
        response.raise_for_status()
        followers_data = response.json().get('response', {}).get('users', [])

        followers_collection.update_one(
            {"source_blog": source_blog},
            {"$set": {"followers": followers_data}},
            upsert=True
        )

        return {"followers": followers_data}
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve followers: {str(e)}")
