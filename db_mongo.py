import os
import certifi
from pymongo import MongoClient, ASCENDING, DESCENDING
from config import Config

from fast_store import FastDatabase

_client = None
_db = None

def get_mongo_client():
    global _client
    if _client is None:
        try:
            _client = MongoClient(Config.MONGO_URI, serverSelectionTimeoutMS=2000)
        except Exception:
            _client = None
    return _client

def get_db():
    global _db
    if _db is None:
        # High speed local persistent store
        _db = FastDatabase("placement_local_db.json")
    return _db

def init_mongo_indexes():
    """Initializes high performance indexes on all MongoDB collections"""
    try:
        db = get_db()
        db.users.create_index([("username", ASCENDING)], unique=True)
        db.users.create_index([("member_id", ASCENDING)], unique=True)
        db.users.create_index([("email", ASCENDING)], unique=True)
        
        db.departments.create_index([("code", ASCENDING)], unique=True)
        
        db.students.create_index([("roll_no", ASCENDING)], unique=True)
        db.students.create_index([("department_code", ASCENDING)])
        db.students.create_index([("placement_status", ASCENDING)])
        db.students.create_index([("ug_percent", DESCENDING)])
        db.students.create_index([("name", ASCENDING)])
        
        db.companies.create_index([("name", ASCENDING)])
        db.companies.create_index([("status", ASCENDING)])
        db.companies.create_index([("forwarded_to_admin", ASCENDING)])
        db.companies.create_index([("is_approved", ASCENDING)])
        db.companies.create_index([("created_at", DESCENDING)])
        
        db.placement_drives.create_index([("company_id", ASCENDING)])
        db.placement_drives.create_index([("status", ASCENDING)])
        
        db.offers.create_index([("student_id", ASCENDING)])
        db.offers.create_index([("company_id", ASCENDING)])
        
        db.ats_analyses.create_index([("student_id", ASCENDING)])
        db.ats_analyses.create_index([("created_at", DESCENDING)])
        
        db.activity_logs.create_index([("created_at", DESCENDING)])
        print("MongoDB Indexes initialized successfully!")
    except Exception as e:
        print(f"MongoDB index init notice: {e}")

def get_next_sequence(sequence_name: str) -> int:
    """Generates auto-incrementing integer IDs for collections"""
    db = get_db()
    try:
        result = db.counters.find_one_and_update(
            {"_id": sequence_name},
            {"$inc": {"seq": 1}},
            upsert=True,
            return_document=True
        )
        if result and "seq" in result:
            return int(result["seq"])
        if result and "sequence_value" in result:
            return int(result["sequence_value"])
    except Exception:
        pass
    
    # Fallback
    col_name = sequence_name.replace("_id", "s")
    try:
        col = getattr(db, col_name, None)
        if col:
            return col.count_documents({}) + 1
    except Exception:
        pass
    return 1
