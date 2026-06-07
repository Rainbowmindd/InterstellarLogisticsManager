# Nierelacyjne/backend/db.py
from pymongo import MongoClient
import os

# ZMIEŃ TĘ LINIĘ: DODAJ "?replicaSet=rs0"
# Upewnij się, że "rs0" pasuje do nazwy replikasetu, którego używasz
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/?replicaSet=rs0")
DB_NAME = "interstellar_logistics"

_client = None
_db = None

def get_db():
    global _client, _db
    if _db is None:
        _client = MongoClient(MONGO_URI)
        _db = _client[DB_NAME]
    return _db