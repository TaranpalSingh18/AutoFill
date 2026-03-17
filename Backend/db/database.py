from pymongo import MongoClient
import os
from dotenv import load_dotenv
from pymongo.server_api import ServerApi

load_dotenv()

mongo_uri = os.getenv("MONGO_URI")
cluster_name = os.getenv("MONGO_NAME", "autofill")

if not mongo_uri:
    raise ValueError("MONGO DB URI is missing")

client = MongoClient(mongo_uri, server_api=ServerApi("1"))
db = client[cluster_name]

## acha matlab cluster name ek client ke naam ke array mei stored hai

def ping_mongo():
    client.admin.command("ping")
    print("MongoDB Connected Successfully")
    return True

def close_mongo():
    print("Terminating Connection")
    client.close()

