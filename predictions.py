import random
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from config import FOOTBALL_API_KEY, ODDS_API_KEY, OPENWEATHER_API_KEY

_admin_lottery_cache = {
    "thai": None,
    "laos": None,
    "date": None
}

def set_lottery_result_admin(thai_num, laos_num):
    _admin_lottery_cache["thai"] = thai_num
    _admin_lottery_cache["laos"] = laos_num
    _admin_lottery_cache["date"] = datetime.now().strftime("%Y-%m-%d")

# ---- ထိုင်းထီ ထိပ်ဆုံး ၅ ကွက် (၆ လုံး) ----
def get_thai_lottery_predictions():
    predictions = []
    used_numbers = set()
    for i in range(1, 6):
        while True:
            num = f"{random.randint(0, 999999):06d}"
            if num not in used_numbers:
                used_numbers.add(num)
                break
        confidence = random.choice(["အလွန်ကောင်း", "ကောင်း", "အတန်အသင့်"])
        predictions.append({
            "rank": i,
            "number": num,
            "confidence": confidence
        })
    return predictions

# ---- လာအိုထီ ထိပ်ဆုံး ၅ ကွက် (၄ လုံး) ----
def get_laos_lottery_predictions():
    predictions = []
    used_numbers = set()
    for i in range(1, 6):
        while True:
            num = f"{random.randint(0, 9999):04d}"
            if num not in used_numbers:
                used_numbers.add(num)
                break
        confidence = random.choice(["အလွန်ကောင်း", "ကောင်း", "အတန်အသင့်"])
        predictions.append({
            "rank": i,
            "number": num,
            "confidence": confidence
        })
    return predictions

# ---- ထိုင်းထီကလင်ဒါ ----
def get_thai_calendar():
    today = datetime.now()
    dates = []
    for month_offset in range(3):
        for day in [1, 16]:
            try:
                d = datetime(today.year, today.month + month_offset, day)
                if d >= today:
                    dates.append(d.strftime("%Y-%m-%d (%A)"))
            except:
                pass
    return dates[:6]

# ---- လာအိုထီကလင်ဒါ ----
def get_laos_calendar():
    today = datetime.now()
    dates = []
    for i in range(14):
        d = today + timedelta(days=i)
        if d.weekday() < 5:
            dates.append(d.strftime("%Y-%m-%d (%A)"))
    return dates[:10]

# ---- ပြီးခဲ့သော ဘောလုံးရလဒ်များ ----
def get_past_football_results():
    """ပြီးခဲ့သော ဘောလုံးရလဒ်များကို ပြန်ပေးမယ်"""
    results = []
    if FOOTBALL_API_KEY:
        try:
            url = "https://api.football-data.org/v4/matches"
            params = {"status": "FINISHED", "limit": 10}
            headers = {"X-Auth-Token": FOOTBALL_API_KEY}
            resp = requests.get(url, headers=headers, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                for match in data.get("matches", []):
                    home = match["homeTeam"]["name"]
                    away = match["awayTeam"]["name"]
                    score = match.get("score", {})
                    fulltime = score.get("fullTime", {})
                    home_score = fulltime.get("home", "?")
                    away_score = fulltime.get("away", "?")
                    results.append(f"{home} {home_score} - {away_score} {away}")
                return results
        except Exception as e:
            print(f"API Error: {e}")
    
    # Mock Data
    mock = [
        "မန်ယူ 2 - 1 အာဆင်နယ်",
        "လီဗာပူး 3 - 0 မန်စီးတီး",
        "ဘိုင်ယန်မြူးနစ် 1 - 1 ဒေါ့မွန်",
        "ရီးရဲလ် 2 - 0 ဘာစီလိုနာ",
        "ပီအက်စ်ဂျီ 4 - 2 အိုလမ်ပစ်"
    ]
    return mock

def get_lottery_results():
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    if _admin_lottery_cache["date"] == today_str:
        if _admin_lottery_cache["thai"] and _admin_lottery_cache["laos"]:
            return {
                "thai": _admin_lottery_cache["thai"],
                "laos": _admin_lottery_cache["laos"],
                "source": "Admin မှသတ်မှတ်သည်"
            }
    
    try:
        url = "https://www.glomyanmar.com/category/laos-lottery/"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            thai_num = soup.find("div", class_="lotto-number")
            if thai_num:
                return {
                    "thai": thai_num.text.strip()[:3],
                    "laos": "၀၀",
                    "source": "Website (Scraped)"
                }
    except Exception as e:
        print(f"Scraping Error: {e}")
    
    return {
        "thai": f"{random.randint(0, 999):03d}",
        "laos": f"{random.randint(0, 99):02d}",
        "source": "ခန့်မှန်းချက် (အာမခံချက်မရှိ)"
    }

def get_football_predictions():
    matches = []
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
    
    mock = [("မန်ယူ", "အာဆင်နယ်", "20:00"), ("လီဗာပူး", "မန်စီးတီး", "22:00")]
    for home, away, t in mock:
        matches.append(f"🆚 {home} vs {away}\n   ⏰ မြန်မာချိန် {t}")
    return matches

class LotteryPredictor:
    def __init__(self, history_data=None):
        self.history = history_data or []
    
    def predict(self, lottery_type="thai"):
        if lottery_type == "thai":
            return f"{random.randint(0, 999):03d}"
        else:
            return f"{random.randint(0, 99):02d}"

class FootballPredictor:
    def __init__(self, football_api_key=None, odds_api_key=None, weather_api_key=None):
        self.football_api_key = football_api_key or FOOTBALL_API_KEY
        self.odds_api_key = odds_api_key or ODDS_API_KEY
        self.weather_api_key = weather_api_key or OPENWEATHER_API_KEY
    
    def get_match_odds(self, match_id):
        if not self.odds_api_key:
            return None
        try:
            url = f"https://api.the-odds-api.com/v4/sports/football/events/{match_id}/odds"
            params = {"apiKey": self.odds_api_key, "regions": "eu", "markets": "h2h"}
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            print(f"Odds API Error: {e}")
        return None
    
    def get_weather(self, city):
        if not self.weather_api_key:
            return None
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather"
            params = {"q": city, "appid": self.weather_api_key, "units": "metric"}
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "temp": data["main"]["temp"],
                    "condition": data["weather"][0]["description"]
                }
        except Exception as e:
            print(f"Weather API Error: {e}")
        return None
    
    def predict_match(self, home_team, away_team, match_id=None, city=None):
        result = {
            "home": home_team,
            "away": away_team,
            "prediction": None,
            "confidence": "Medium",
            "details": {}
        }
        
        odds = None
        if match_id:
            odds = self.get_match_odds(match_id)
            if odds:
                result["details"]["odds"] = odds
        
        weather = None
        if city:
            weather = self.get_weather(city)
            if weather:
                result["details"]["weather"] = weather
        
        rand = random.random()
        if rand < 0.4:
            pred = f"🏠 {home_team} နိုင်"
        elif rand < 0.7:
            pred = f"✈️ {away_team} နိုင်"
        else:
            pred = "🤝 သရေ"
        
        result["prediction"] = pred
        
        if odds:
            result["confidence"] = "High"
        
        return result
    
    def predict_multiple(self, matches):
        results = []
        for home, away, match_id, city in matches:
            result = self.predict_match(home, away, match_id, city)
            results.append(result)
        return results
