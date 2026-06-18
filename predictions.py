# predictions.py (အသစ်ပြင်ဆင်ထားတဲ့ဟာ)

import random
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from config import FOOTBALL_API_KEY  # ဒီဟာက football-data.org key ဖြစ်မယ်

# ---- ထီပိုင်း (အရင်အတိုင်း) ----
def get_lottery_predictions():
    return {
        "thai": f"{random.randint(0, 999):03d}",
        "laos": f"{random.randint(0, 99):02d}"
    }

# ---- ဘောလုံးခန့်မှန်းချက် (football-data.org သုံးမယ်) ----
def get_football_predictions():
    matches = []
    
    # football-data.org API ကို သုံးမယ်
    if FOOTBALL_API_KEY:
        try:
            url = "https://api.football-data.org/v4/matches"
            headers = {"X-Auth-Token": FOOTBALL_API_KEY}
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                for match in data.get("matches", [])[:5]:
                    home = match["homeTeam"]["name"]
                    away = match["awayTeam"]["name"]
                    # ရိုးရိုး heuristic နဲ့ ခန့်မှန်းမယ်
                    rand = random.random()
                    if rand < 0.4:
                        prediction = f"🏠 {home} နိုင်"
                    elif rand < 0.7:
                        prediction = f"✈️ {away} နိုင်"
                    else:
                        prediction = "🤝 သရေ"
                    matches.append(f"{home} vs {away} -> {prediction}")
                return matches
        except Exception as e:
            print(f"API Error: {e}")
    
    # API မရရင် Mock Data
    mock_matches = [
        ("မန်ယူ", "အာဆင်နယ်"),
        ("လီဗာပူး", "မန်စီးတီး"),
        ("ဘိုင်ယန်မြူးနစ်", "ဒေါ့မွန်"),
    ]
    for home, away in mock_matches:
        rand = random.random()
        if rand < 0.4:
            pred = f"🏠 {home} နိုင်"
        elif rand < 0.7:
            pred = f"✈️ {away} နိုင်"
        else:
            pred = "🤝 သရေ"
        matches.append(f"{home} vs {away} -> {pred}")
    return matches

# ---- ယနေ့ပွဲစဉ်စာရင်း (football-data.org သုံးမယ်) ----
def get_today_fixtures():
    today = datetime.now().strftime("%Y-%m-%d")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    matches = []
    
    if FOOTBALL_API_KEY:
        try:
            url = f"https://api.football-data.org/v4/matches"
            params = {"dateFrom": today, "dateTo": tomorrow, "limit": 10}
            headers = {"X-Auth-Token": FOOTBALL_API_KEY}
            resp = requests.get(url, headers=headers, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                for m in data.get("matches", []):
                    home = m["homeTeam"]["name"]
                    away = m["awayTeam"]["name"]
                    time = m.get("utcDate", "N/A")[:16].replace("T", " ")
                    matches.append(f"🆚 {home} vs {away}\n   ⏰ {time} UTC")
                return matches if matches else ["ယနေ့ပွဲစဉ် မရှိသေးပါ"]
        except Exception as e:
            print(f"Fixtures API Error: {e}")
    
    # Mock Data
    mock = [("မန်ယူ", "အာဆင်နယ်", "20:00"), ("လီဗာပူး", "မန်စီးတီး", "22:00")]
    for home, away, t in mock:
        matches.append(f"🆚 {home} vs {away}\n   ⏰ မြန်မာချိန် {t}")
    return matches
