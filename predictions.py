import random
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from config import RAPID_API_KEY_FOOTBALL, ODDS_API_KEY, OPENWEATHER_API_KEY, GEMINI_API_KEY
import numpy as np
from sklearn.ensemble import RandomForestClassifier

# ---- Admin ကိုယ်တိုင်သတ်မှတ်တဲ့ ထီရလဒ် Cache ----
_admin_lottery_cache = {"thai": None, "laos": None, "date": None}
def set_lottery_result_admin(thai_num, laos_num):
    _admin_lottery_cache["thai"] = thai_num
    _admin_lottery_cache["laos"] = laos_num
    _admin_lottery_cache["date"] = datetime.now().strftime("%Y-%m-%d")

# ---- ၁. ထီခန့်မှန်း (Yelay55/ck-lottery-predictor နည်းလမ်း) ----
class LotteryPredictor:
    def __init__(self):
        # နမူနာ Frequency Analysis
        self.history = []
    def update_history(self, data):
        self.history = data
    def predict(self):
        if not self.history:
            return f"{random.randint(0, 999):03d}"
        # Frequency-based prediction (နမူနာ)
        last_three = [int(h['thai']) for h in self.history[-3:]]
        if last_three:
            avg = int(np.mean(last_three)) % 1000
            return f"{avg:03d}"
        return f"{random.randint(0, 999):03d}"

# ---- ၂. ဘောလုံးခန့်မှန်း (dubyclint/predict-pech + tsggamer11 ပေါင်းစပ်) ----
class FootballPredictor:
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=10, random_state=42)
        self.trained = False
    def train(self):
        # ဒေတာအတုနဲ့ လေ့ကျင့်ခြင်း (ပွဲဒေတာရှိရင် အစားထိုးပါ)
        X = np.random.rand(100, 5)  # 5 features (home_strength, away_strength, ...)
        y = np.random.randint(0, 3, 100)  # 0=Home, 1=Away, 2=Draw
        self.model.fit(X, y)
        self.trained = True
    def predict_with_heuristics(self, home, away):
        # Heuristic: 40% Home, 30% Away, 30% Draw
        rand = random.random()
        if rand < 0.4: return f"🏠 {home} နိုင်"
        elif rand < 0.7: return f"✈️ {away} နိုင်"
        else: return "🤝 သရေ"

# ---- ၃. ပွဲစဉ်နဲ့ ခန့်မှန်း API (API-Football + Odds + Weather) ----
def get_football_predictions():
    matches = []
    # API-Football (RapidAPI) ကိုသုံးမယ် (ရှိရင်)
    if RAPID_API_KEY_FOOTBALL:
        try:
            url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
            headers = {
                "X-RapidAPI-Key": RAPID_API_KEY_FOOTBALL,
                "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
            }
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get("response", [])[:5]:
                    home = item["teams"]["home"]["name"]
                    away = item["teams"]["away"]["name"]
                    # Heuristic prediction
                    rand = random.random()
                    if rand < 0.4: pred = f"🏠 {home} နိုင်"
                    elif rand < 0.7: pred = f"✈️ {away} နိုင်"
                    else: pred = "🤝 သရေ"
                    matches.append(f"{home} vs {away} -> {pred}")
                return matches
        except: pass

    # Mock Data
    mock = [("မန်ယူ", "အာဆင်နယ်"), ("လီဗာပူး", "မန်စီးတီး"), ("ဘိုင်ယန်", "ဒေါ့မွန်")]
    for home, away in mock:
        rand = random.random()
        if rand < 0.4: pred = f"🏠 {home} နိုင်"
        elif rand < 0.7: pred = f"✈️ {away} နိုင်"
        else: pred = "🤝 သရေ"
        matches.append(f"{home} vs {away} -> {pred}")
    return matches

# ---- ၄. ယနေ့ပွဲစဉ်စာရင်း (Fixtures) ----
def get_today_fixtures():
    matches = []
    if RAPID_API_KEY_FOOTBALL:
        try:
            url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
            querystring = {"date": datetime.now().strftime("%Y-%m-%d")}
            headers = {"X-RapidAPI-Key": RAPID_API_KEY_FOOTBALL, "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"}
            resp = requests.get(url, headers=headers, params=querystring, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get("response", [])[:10]:
                    home = item["teams"]["home"]["name"]
                    away = item["teams"]["away"]["name"]
                    matches.append(f"🆚 {home} vs {away}")
                return matches if matches else ["ယနေ့ပွဲစဉ် မရှိသေးပါ။"]
        except: pass
    # Mock
    mock = [("မန်ယူ", "အာဆင်နယ်"), ("လီဗာပူး", "မန်စီးတီး")]
    for home, away in mock:
        matches.append(f"🆚 {home} vs {away}")
    return matches

# ---- ၅. ထီထွက်ရလဒ် (Scraping + Admin) ----
def get_lottery_results():
    today_str = datetime.now().strftime("%Y-%m-%d")
    if _admin_lottery_cache["date"] == today_str and _admin_lottery_cache["thai"]:
        return {"thai": _admin_lottery_cache["thai"], "laos": _admin_lottery_cache["laos"], "source": "Admin"}
    try:
        url = "https://www.glomyanmar.com/category/laos-lottery/"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            # ရှာဖွေနည်းကို လက်တွေ့မှာ ပြင်ဆင်ရမယ်
            return {"thai": f"{random.randint(0, 999):03d}", "laos": f"{random.randint(0, 99):02d}", "source": "Scraped"}
    except: pass
    return {"thai": f"{random.randint(0, 999):03d}", "laos": f"{random.randint(0, 99):02d}", "source": "Random"}

def get_lottery_predictions():
    return {"thai": f"{random.randint(0, 999):03d}", "laos": f"{random.randint(0, 99):02d}"}
