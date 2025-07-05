import os
from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
url = os.getenv("MONGO_URL")
client = MongoClient(url, server_api=ServerApi('1'))
print(client.list_database_names())
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

database = client.git_db
events_collection = database.get_collection('EVENTS')