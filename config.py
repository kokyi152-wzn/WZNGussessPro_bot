import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME", "bot_db")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# ဒီနေရာမှာ FOOTBALL_API_KEY ကို ထည့်ပေးလိုက်ပါ။
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY", None)  # football-data.org က Key ဖြစ်မယ်။

# Optional - ဒါတွေကို မထည့်လည်းရတယ် (Default None ထားလိုက်တယ်)
RAPID_API_KEY_FOOTBALL = os.getenv("RAPID_API_KEY_FOOTBALL", None)
ODDS_API_KEY = os.getenv("ODDS_API_KEY", None)
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", None)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", None)
