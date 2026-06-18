import random
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from config import FOOTBALL_API_KEY

# ---- LotteryPredictor Class (ထီခန့်မှန်းချက်အတွက်) ----
class LotteryPredictor:
    def __init__(self):
        # ခန့်မှန်းချက်အတွက် သမိုင်းဒေတာ သိမ်းမယ်
        self.history = []
    
    def predict_thai(self):
        """ထိုင်းထီခန့်မှန်းချက် (ကျပန်းဂဏန်း + ရိုးရှင်းတဲ့ Logic)"""
        # ရိုးရှင်းတဲ့ ခန့်မှန်းနည်း - ကျပန်းဂဏန်းထုတ်ပေးတယ်
        return f"{random.randint(0, 999):03d}"
    
    def predict_laos(self):
        """လာအိုထီခန့်မှန်းချက် (ကျပန်းဂဏန်း + ရိုးရှင်းတဲ့ Logic)"""
        return f"{random.randint(0, 99):02d}"
    
    def predict_both(self):
        """ထိုင်းထီနဲ့ လာအိုထီ နှစ်ခုလုံး ခန့်မှန်းချက်"""
        return {
            "thai": self.predict_thai(),
            "laos": self.predict_laos()
        }

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

# ---- ထီခန့်မှန်းချက် (မူလ Function - နောက်ပြန်လိုက်ဖက်အတွက်) ----
def get_lottery_predictions():
    predictor = LotteryPredictor()
    return predictor.predict_both()

# ---- ထီထွက်ရလဒ် (Admin သတ်မှတ်ချက် → Scraping → ကျပန်း) ----
def get_lottery_results():
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    # 1. Admin သတ်မှတ်ထားတဲ့ Result
    if _admin_lottery_cache["date"] == today_str:
        if _admin_lottery_cache["thai"] and _admin_lottery_cache["laos"]:
            return {
                "thai": _admin_lottery_cache["thai"],
                "laos": _admin_lottery_cache["laos"],
                "source": "Admin မှသတ်မှတ်သည်"
            }
    
    # 2. Web Scraping ကြိုးစားမယ် (ဥပမာ - glomyanmar)
    try:
        url = "https://www.glomyanmar.com/category/laos-lottery/"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            # လက်တွေ့မှာ ဒီနေရာကို ခင်ဗျား ကြည့်ပြီး ပြင်ရမယ်
            thai_num = soup.find("div", class_="lotto-number")
            if thai_num:
                return {
                    "thai": thai_num.text.strip()[:3],
                    "laos": "၀၀",
                    "source": "Website (Scraped)"
                }
    except Exception as e:
        print(f"Scraping Error: {e}")
    
    # 3. မရရင် ကျပန်း
    predictor = LotteryPredictor()
    pred = predictor.predict_both()
    return {
        "thai": pred["thai"],
        "laos": pred["laos"],
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
        except: pass
    # Mock
    mock = [("မန်ယူ", "အာဆင်နယ်", "20:00"), ("လီဗာပူး", "မန်စီးတီး", "22:00")]
    for home, away, t in mock:
        matches.append(f"🆚 {home} vs {away}\n   ⏰ မြန်မာချိန် {t}")
    return matches
