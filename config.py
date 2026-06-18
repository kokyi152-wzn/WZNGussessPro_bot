import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME", "bot_db")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY", None)   # ← ဒီလိုင်းပါဖို့လိုတယ်
ODDS_API_KEY = os.getenv("ODDS_API_KEY", None)           # ← ဒီလိုင်းပါဖို့လိုတယ်
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", None)  # ← ဒီလိုင်းပါဖို့လိုတယ်
