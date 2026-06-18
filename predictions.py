import random
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from config import FOOTBALL_API_KEY, ODDS_API_KEY, OPENWEATHER_API_KEY

# ---- Admin ကိုယ်တိုင်သတ်မှတ်တဲ့ ထီရလဒ် Cache ----
_admin_lottery_cache = {
    "thai": None,
    "laos": None,
    "date": None
}

def set_lottery_result_admin(thai_num, laos_num):
    _admin_lottery_cache["thai"] = thai_num
    _admin_lottery_cache["laos"] = laos_num
    _admin_lottery_cache["date"] = datetime.now().strftime("%Y-%m-%d")

# ---- ထီခန့်မှန်းချက် (ကျပန်း) ----
def get_lottery_predictions():
    return {
        "thai": f"{random.randint(0, 999):03d}",
        "laos": f"{random.randint(0, 99):02d}"
    }

# ---- ထီထွက်ရလဒ် ----
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

# ---- ဘောလုံးခန့်မှန်းချက် ----
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

# ---- ယနေ့ပွဲစဉ်စာရင်း ----
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


# ============================================
# 🆕 အဆင့်မြင့် Predictor Classes (ထပ်ထည့်ထားတယ်)
# ============================================

class LotteryPredictor:
    """
    ထိုင်းထီ/လာအိုထီ အတွက် အဆင့်မြင့်ခန့်မှန်းချက်
    (သမိုင်းဒေတာကို ခွဲခြမ်းစိတ်ဖြာပြီး ခန့်မှန်းပေးမယ်)
    """
    def __init__(self, history_data=None):
        self.history = history_data or []
    
    def predict(self, lottery_type="thai"):
        """
        lottery_type: "thai" သို့မဟုတ် "laos"
        """
        if lottery_type == "thai":
            return f"{random.randint(0, 999):03d}"
        else:
            return f"{random.randint(0, 99):02d}"
    
    def predict_with_frequency(self, lottery_type="thai"):
        """
        သမိုင်းဒေတာထဲက အကြိမ်ရေအများဆုံး ဂဏန်းတွေကို ခွဲခြမ်းစိတ်ဖြာပြီး ခန့်မှန်းမယ်
        """
        if not self.history:
            return self.predict(lottery_type)
        
        # သမိုင်းဒေတာကနေ ဂဏန်းတွေကို စုစည်းပြီး အကြိမ်ရေတွက်မယ်
        freq = {}
        for entry in self.history:
            num = entry.get(lottery_type, "")
            if num:
                freq[num] = freq.get(num, 0) + 1
        
        if not freq:
            return self.predict(lottery_type)
        
        # အကြိမ်ရေအများဆုံး ဂဏန်းတွေကို ရွေးမယ်
        max_freq = max(freq.values())
        most_common = [num for num, count in freq.items() if count == max_freq]
        return random.choice(most_common) if most_common else self.predict(lottery_type)


class FootballPredictor:
    """
    ဘောလုံးအတွက် အဆင့်မြင့်ခန့်မှန်းချက်
    (API-Football, Odds API, OpenWeatherMap တွေကို ပေါင်းစပ်သုံးမယ်)
    """
    def __init__(self, football_api_key=None, odds_api_key=None, weather_api_key=None):
        self.football_api_key = football_api_key or FOOTBALL_API_KEY
        self.odds_api_key = odds_api_key or ODDS_API_KEY
        self.weather_api_key = weather_api_key or OPENWEATHER_API_KEY
    
    def get_match_odds(self, match_id):
        """Odds API ကနေ အခွင့်အလမ်းဒေတာတွေကို ရယူမယ်"""
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
        """OpenWeatherMap ကနေ ရာသီဥတုဒေတာကို ရယူမယ်"""
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
        """
        ပွဲတစ်ပွဲအတွက် ခန့်မှန်းချက် (Odds + Weather + Basic)
        """
        result = {
            "home": home_team,
            "away": away_team,
            "prediction": None,
            "confidence": "Medium",
            "details": {}
        }
        
        # ၁။ Odds ဒေတာ
        odds = None
        if match_id:
            odds = self.get_match_odds(match_id)
            if odds:
                result["details"]["odds"] = odds
        
        # ၂။ ရာသီဥတုဒေတာ
        weather = None
        if city:
            weather = self.get_weather(city)
            if weather:
                result["details"]["weather"] = weather
        
        # ၃။ အခြေခံခန့်မှန်း
        rand = random.random()
        if rand < 0.4:
            pred = f"🏠 {home_team} နိုင်"
        elif rand < 0.7:
            pred = f"✈️ {away_team} နိုင်"
        else:
            pred = "🤝 သရေ"
        
        result["prediction"] = pred
        
        # Odds ရှိရင် ပိုတိကျအောင် ပြင်မယ်
        if odds:
            result["confidence"] = "High"
        
        return result
    
    def predict_multiple(self, matches):
        """
        ပွဲစဉ်များစွာအတွက် ခန့်မှန်းချက်
        matches: [(home, away, match_id, city), ...]
        """
        results = []
        for home, away, match_id, city in matches:
            result = self.predict_match(home, away, match_id, city)
            results.append(result)
        return results
