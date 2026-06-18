import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME", "bot_db")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# ---- API Keys (ခင်ဗျား ရယူထားတဲ့ဟာတွေ) ----
RAPID_API_KEY_FOOTBALL = os.getenv("RAPID_API_KEY_FOOTBALL")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
