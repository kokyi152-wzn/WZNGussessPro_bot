from pymongo import MongoClient
from config import MONGODB_URI, DB_NAME
from datetime import datetime

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]
users_collection = db["users"]
history_collection = db["lottery_history"]

# ---- User Management ----
def add_user(user_id, username, first_name):
    if not users_collection.find_one({"user_id": user_id}):
        users_collection.insert_one({
            "user_id": user_id,
            "username": username,
            "first_name": first_name,
            "package": "free",
            "joined_date": datetime.now()
        })

def get_user(user_id):
    return users_collection.find_one({"user_id": user_id})

def set_package(user_id, package_type):
    users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"package": package_type}}
    )

def get_package(user_id):
    user = get_user(user_id)
    return user.get("package", "free") if user else "free"

def can_access(user_id, feature):
    pkg = get_package(user_id)
    if pkg == "both": return True
    if pkg == feature: return True
    if feature in ["football", "fixtures", "lottery_result"] and pkg == "both":
        return True
    return False

# ---- History Management ----
def save_history(date, thai_num, laos_num):
    history_collection.update_one(
        {"date": date},
        {"$set": {"date": date, "thai": thai_num, "laos": laos_num, "updated_at": datetime.now()}},
        upsert=True
    )

def get_history_by_date(date):
    return history_collection.find_one({"date": date})

def get_recent_history(limit=10):
    return list(history_collection.find().sort("date", -1).limit(limit))
