from pymongo import MongoClient
import os

_client = None


def get_connection():
    """Return a connection to the MongoDB database."""
    global _client
    if _client is None:
        _client = MongoClient(os.getenv("MONGO_URI"))
    dbname = os.getenv("MONGO_DBNAME", "DayByDay")
    return _client[dbname]



