from pymongo import MongoClient
from config import MONGODB_URI, DB_NAME, ADMIN_ID
from datetime import datetime, timedelta

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]
users_collection = db["users"]
history_collection = db["lottery_history"]
thai_results_collection = db["thai_lottery_results"]
laos_results_collection = db["laos_lottery_results"]

# ... (အရင်က ရှိပြီးသား functions များ) ...

# ---- ထိုင်းထီရလဒ်များ သိမ်းဆည်းခြင်းနှင့် ပြန်လည်ရယူခြင်း ----
def save_thai_result(date, data):
    """ထိုင်းထီရလဒ်ကို သိမ်းဆည်းမယ်"""
    thai_results_collection.update_one(
        {"date": date},
        {"$set": {"date": date, "results": data, "updated_at": datetime.now()}},
        upsert=True
    )

def get_thai_result(date):
    """ရက်စွဲအလိုက် ထိုင်းထီရလဒ်ကို ပြန်ပေးမယ်"""
    return thai_results_collection.find_one({"date": date})

def get_all_thai_results(limit=20):
    """ထိုင်းထီရလဒ်အကုန်ကို ပြန်ပေးမယ် (နောက်ဆုံးအရင်ဆုံး)"""
    return list(thai_results_collection.find().sort("date", -1).limit(limit))

# ---- လာအိုထီရလဒ်များ သိမ်းဆည်းခြင်းနှင့် ပြန်လည်ရယူခြင်း ----
def save_laos_result(date, data):
    """လာအိုထီရလဒ်ကို သိမ်းဆည်းမယ်"""
    laos_results_collection.update_one(
        {"date": date},
        {"$set": {"date": date, "results": data, "updated_at": datetime.now()}},
        upsert=True
    )

def get_laos_result(date):
    """ရက်စွဲအလိုက် လာအိုထီရလဒ်ကို ပြန်ပေးမယ်"""
    return laos_results_collection.find_one({"date": date})

def get_all_laos_results(limit=20):
    """လာအိုထီရလဒ်အကုန်ကို ပြန်ပေးမယ် (နောက်ဆုံးအရင်ဆုံး)"""
    return list(laos_results_collection.find().sort("date", -1).limit(limit))
