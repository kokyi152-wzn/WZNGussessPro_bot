from pymongo import MongoClient
from config import MONGODB_URI, DB_NAME, ADMIN_ID
from datetime import datetime, timedelta

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]
users_collection = db["users"]
history_collection = db["lottery_history"]
thai_result_collection = db["thai_full_results"]
laos_result_collection = db["laos_full_results"]

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
    if user:
        return user.get("package", "free")
    return "free"

def can_access(user_id, feature):
    if user_id == ADMIN_ID:
        return True
    pkg = get_package(user_id)
    if pkg == "both":
        return True
    if feature == "thai" and pkg == "thai":
        return True
    if feature == "laos" and pkg == "laos":
        return True
    if feature in ["football", "fixtures", "lottery_result", "past_football"]:
        return pkg == "both"
    return False

def save_history(date, thai_num, laos_num):
    history_collection.update_one(
        {"date": date},
        {"$set": {
            "date": date,
            "thai": thai_num,
            "laos": laos_num,
            "updated_at": datetime.now()
        }},
        upsert=True
    )

def get_history_by_date(date):
    return history_collection.find_one({"date": date})

def get_recent_history(limit=1000):
    return list(history_collection.find().sort("date", -1).limit(limit))

def get_history_by_month(months=3):
    cutoff_date = datetime.now() - timedelta(days=months*30)
    cutoff_str = cutoff_date.strftime("%Y-%m-%d")
    return list(history_collection.find({"date": {"$gte": cutoff_str}}).sort("date", -1))

def get_history_by_weeks(weeks=4):
    cutoff_date = datetime.now() - timedelta(days=weeks*7)
    cutoff_str = cutoff_date.strftime("%Y-%m-%d")
    return list(history_collection.find({"date": {"$gte": cutoff_str}}).sort("date", -1))

def save_full_thai_result(data):
    thai_result_collection.update_one(
        {"date": data["date"]},
        {"$set": data},
        upsert=True
    )

def get_full_thai_result():
    return list(thai_result_collection.find().sort("date", -1))

def get_full_thai_result_by_date(date):
    return thai_result_collection.find_one({"date": date})

def save_full_laos_result(data):
    laos_result_collection.update_one(
        {"date": data["date"]},
        {"$set": data},
        upsert=True
    )

def get_full_laos_result():
    return list(laos_result_collection.find().sort("date", -1))

def get_full_laos_result_by_date(date):
    return laos_result_collection.find_one({"date": date})
