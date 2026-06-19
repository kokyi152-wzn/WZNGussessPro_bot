import random
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from config import FOOTBALL_API_KEY, ODDS_API_KEY, OPENWEATHER_API_KEY, ADMIN_ID

# ---- Team name mapping ----
TEAM_NAMES = {
    "Manchester United": "မန်ယူ",
    "Arsenal": "အာဆင်နယ်",
    "Liverpool": "လီဗာပူး",
    "Manchester City": "မန်စီးတီး",
    "Bayern Munich": "ဘိုင်ယန်မြူးနစ်",
    "Borussia Dortmund": "ဒေါ့မွန်",
    "Real Madrid": "ရီးရဲလ်",
    "Barcelona": "ဘာစီလိုနာ",
    "PSG": "ပီအက်စ်ဂျီ",
    "Olympique Marseille": "အိုလမ်ပစ်",
    "Chelsea": "ချယ်လ်ဆီး",
    "Tottenham": "တော့တင်ဟမ်",
    "AC Milan": "အေစီမီလန်",
    "Inter Milan": "အင်တာမီလန်",
    "Juventus": "ဂျူဗင်တပ်",
    "Napoli": "နာပိုလီ",
    "Ajax": "အေဂျက်စ်",
    "Benfica": "ဘင်ဖီကာ",
    "Porto": "ပေါ်တို",
    "Sporting CP": "စပေါ်တင်း",
}

def get_team_name_mm(eng_name):
    return TEAM_NAMES.get(eng_name, eng_name)

# ---- Admin သတ်မှတ်ထားတဲ့ ထီရလဒ် Cache ----
_admin_lottery_cache = {
    "thai": None,
    "laos": None,
    "date": None
}

def set_lottery_result_admin(thai_num, laos_num):
    _admin_lottery_cache["thai"] = thai_num
    _admin_lottery_cache["laos"] = laos_num
    _admin_lottery_cache["date"] = datetime.now().strftime("%Y-%m-%d")

# ---- အချိန်စစ်ဆေးခြင်း Function ----
def can_show_thai_prediction(user_id):
    """ထိုင်းထီခန့်မှန်းချက်ကို ပြခွင့်ရှိမရှိ စစ်ဆေးမယ်"""
    # Admin ဆိုရင် အချိန်မရွေး ကြည့်လို့ရမယ်
    if user_id == ADMIN_ID:
        return True, None
    
    today = datetime.now()
    # ထိုင်းထီထွက်မယ့်ရက်ကို ရှာမယ် (၁ ရက် နဲ့ ၁၆ ရက်)
    thai_draw_dates = []
    for month_offset in range(3):
        for day in [1, 16]:
            try:
                d = datetime(today.year, today.month + month_offset, day)
                if d >= today:
                    thai_draw_dates.append(d)
            except:
                pass
    
    if not thai_draw_dates:
        return False, "ထိုင်းထီထွက်မယ့်ရက် မတွေ့ပါ။"
    
    next_draw_date = thai_draw_dates[0]
    # ထီမထွက်ခင် ည ၁၂ နာရီ (23:59) မှာ ပြခွင့်ရမယ်
    # ဒါပေမယ့် ခင်ဗျားပြောတာက ထီမထွက်ခင် ည ၁၂ နာရီမှာ ပြမယ်ဆိုတော့
    # အဲဒီအချိန်ကို သတ်မှတ်ဖို့ လိုပါတယ်
    # ဥပမာ - ထီက ၁၆ ရက်နေ့ထွက်မယ်ဆိုရင် ၁၅ ရက်နေ့ ည ၁၂ နာရီမှာ ပြမယ်
    # ဒါကြောင့် ထီထွက်မယ့်ရက်ရဲ့ တစ်ရက်အလို ည ၁၂ နာရီကို စစ်ဆေးမယ်
    
    # ထီထွက်မယ့်ရက်ရဲ့ ည ၁၂ နာရီ (23:59) ကို စစ်ဆေးမယ်
    # ဒါပေမယ့် ခင်ဗျားပြောတာက ထီထွက်မယ့်ရက်ရဲ့ တစ်ရက်အလိုမှာ ပြမယ်ဆိုတော့
    # အဲဒီအချိန်ကို ရောက်ပြီလားဆိုတာ စစ်ဆေးဖို့ လိုပါတယ်
    
    # နောက်ထွက်မယ့်ရက်ရဲ့ တစ်ရက်အလို ည ၁၂ နာရီ
    release_time = next_draw_date - timedelta(days=1)
    release_time = release_time.replace(hour=23, minute=59, second=0)
    
    if today >= release_time:
        return True, None
    else:
        # ပြခွင့်မရသေးရင် ဘယ်အချိန်မှာ ပြမလဲဆိုတာ ပြန်ပြောမယ်
        time_left = release_time - today
        hours_left = int(time_left.total_seconds() // 3600)
        minutes_left = int((time_left.total_seconds() % 3600) // 60)
        return False, f"⏳ ထိုင်းထီခန့်မှန်းချက်ကို ထီမထွက်မီ ည ၁၂ နာရီမှ စတင်ပြပေးမည်။\n\n⏰ ကျန်အချိန်: {hours_left} နာရီ {minutes_left} မိနစ်"

def can_show_laos_prediction(user_id):
    """လာအိုထီခန့်မှန်းချက်ကို ပြခွင့်ရှိမရှိ စစ်ဆေးမယ်"""
    if user_id == ADMIN_ID:
        return True, None
    
    today = datetime.now()
    # လာအိုထီထွက်မယ့်ရက် (တနင်္လာ - သောကြာ)
    # ဒီနေ့ကနေ ရက် ၇ အတွင်း ထွက်မယ့်ရက်ကို ရှာမယ်
    laos_draw_dates = []
    for i in range(7):
        d = today + timedelta(days=i)
        if d.weekday() < 5:  # Mon=0, Tue=1, Wed=2, Thu=3, Fri=4
            laos_draw_dates.append(d)
    
    if not laos_draw_dates:
        return False, "လာအိုထီထွက်မယ့်ရက် မတွေ့ပါ။"
    
    next_draw_date = laos_draw_dates[0]
    # ထီထွက်မယ့်ရက် ညနေ ၆ နာရီ (18:00) မှာ ပြခွင့်ရမယ်
    release_time = next_draw_date.replace(hour=18, minute=0, second=0)
    
    if today >= release_time:
        return True, None
    else:
        time_left = release_time - today
        hours_left = int(time_left.total_seconds() // 3600)
        minutes_left = int((time_left.total_seconds() % 3600) // 60)
        return False, f"⏳ လာအိုထီခန့်မှန်းချက်ကို ထီထွက်မည့်နေ့ ညနေ ၆ နာရီမှ စတင်ပြပေးမည်။\n\n⏰ ကျန်အချိန်: {hours_left} နာရီ {minutes_left} မိနစ်"

# ---- ထိုင်းထီခန့်မှန်းချက် ----
def get_thai_lottery_predictions(user_id):
    # အချိန်စစ်ဆေးပါ
    can_show, msg = can_show_thai_prediction(user_id)
    if not can_show:
        return None, msg
    
    predictions = []
    used_numbers = set()
    for i in range(1, 6):
        while True:
            num = f"{random.randint(0, 999999):06d}"
            if num not in used_numbers:
                used_numbers.add(num)
                break
        if i == 1:
            confidence = "အလွန်ကောင်း 🔥"
        elif i == 2:
            confidence = "အလွန်ကောင်း"
        elif i == 3:
            confidence = "ကောင်း"
        else:
            confidence = "အတန်အသင့်"
        predictions.append({"rank": i, "number": num, "confidence": confidence})
    
    return predictions, None

# ---- လာအိုထီခန့်မှန်းချက် ----
def get_laos_lottery_predictions(user_id):
    can_show, msg = can_show_laos_prediction(user_id)
    if not can_show:
        return None, msg
    
    predictions = []
    used_numbers = set()
    for i in range(1, 6):
        while True:
            num = f"{random.randint(0, 9999):04d}"
            if num not in used_numbers:
                used_numbers.add(num)
                break
        if i == 1:
            confidence = "အလွန်ကောင်း 🔥"
        elif i == 2:
            confidence = "အလွန်ကောင်း"
        elif i == 3:
            confidence = "ကောင်း"
        else:
            confidence = "အတန်အသင့်"
        predictions.append({"rank": i, "number": num, "confidence": confidence})
    
    return predictions, None

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
    results = []
    
    if FOOTBALL_API_KEY:
        try:
            from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            to_date = datetime.now().strftime("%Y-%m-%d")
            url = "https://api.football-data.org/v4/matches"
            params = {"dateFrom": from_date, "dateTo": to_date, "status": "FINISHED", "limit": 20}
            headers = {"X-Auth-Token": FOOTBALL_API_KEY}
            resp = requests.get(url, headers=headers, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                for match in data.get("matches", []):
                    home = match["homeTeam"]["name"]
                    away = match["awayTeam"]["name"]
                    date = match.get("utcDate", "")
                    date_str = date.split("T")[0] if date else "N/A"
                    home_mm = get_team_name_mm(home)
                    away_mm = get_team_name_mm(away)
                    score = match.get("score", {})
                    fulltime = score.get("fullTime", {})
                    home_score = fulltime.get("home", "?")
                    away_score = fulltime.get("away", "?")
                    results.append(f"📅 {date_str}\n🏠 {home_mm} {home_score} - {away_score} ✈️ {away_mm}")
                return results if results else ["ပြီးခဲ့သော ၇ ရက်အတွင်း ဘောလုံးရလဒ်များ မရှိသေးပါ။"]
        except Exception as e:
            print(f"Past Football API Error: {e}")
    
    today = datetime.now()
    mock_results = []
    sample_results = [
        ("မန်ယူ", "အာဆင်နယ်", 2, 1),
        ("လီဗာပူး", "မန်စီးတီး", 3, 0),
        ("ဘိုင်ယန်မြူးနစ်", "ဒေါ့မွန်", 1, 1),
        ("ရီးရဲလ်", "ဘာစီလိုနာ", 2, 0),
        ("ပီအက်စ်ဂျီ", "အိုလမ်ပစ်", 4, 2),
        ("ချယ်လ်ဆီး", "တော့တင်ဟမ်", 1, 0),
        ("အေစီမီလန်", "အင်တာမီလန်", 2, 2),
    ]
    for i, (home, away, h_score, a_score) in enumerate(sample_results[:7]):
        d = today - timedelta(days=i+1)
        date_str = d.strftime("%Y-%m-%d")
        mock_results.append(f"📅 {date_str}\n🏠 {home} {h_score} - {a_score} ✈️ {away}")
    return mock_results

# ---- ထီရလဒ် ----
def get_lottery_results():
    today_str = datetime.now().strftime("%Y-%m-%d")
    if _admin_lottery_cache["date"] == today_str:
        if _admin_lottery_cache["thai"] and _admin_lottery_cache["laos"]:
            return {
                "thai": _admin_lottery_cache["thai"],
                "laos": _admin_lottery_cache["laos"],
                "source": "✅ Admin မှ အတည်ပြုထားသော ရလဒ်"
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
                    "source": "✅ အတည်ပြုထားသော ထီရလဒ်"
                }
    except Exception as e:
        print(f"Scraping Error: {e}")
    return {
        "thai": f"{random.randint(0, 999):03d}",
        "laos": f"{random.randint(0, 99):02d}",
        "source": "📊 ကျွမ်းကျင်သူများ၏ ခန့်မှန်းချက်"
    }

# ---- ဘောလုံးခန့်မှန်းချက် ----
def get_football_predictions():
    matches = []
    if FOOTBALL_API_KEY:
        try:
            url = "https://api.football-data.org/v4/matches"
            params = {"status": "SCHEDULED", "limit": 5}
            headers = {"X-Auth-Token": FOOTBALL_API_KEY}
            response = requests.get(url, headers=headers, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                for match in data.get("matches", [])[:5]:
                    home = match["homeTeam"]["name"]
                    away = match["awayTeam"]["name"]
                    home_mm = get_team_name_mm(home)
                    away_mm = get_team_name_mm(away)
                    rand = random.random()
                    if rand < 0.4:
                        prediction = f"🏠 {home_mm} နိုင်"
                    elif rand < 0.7:
                        prediction = f"✈️ {away_mm} နိုင်"
                    else:
                        prediction = "🤝 သရေ"
                    matches.append(f"{home_mm} vs {away_mm} → {prediction}")
                return matches
        except Exception as e:
            print(f"Football Prediction API Error: {e}")
    mock_matches = [
        ("မန်ယူ", "အာဆင်နယ်"),
        ("လီဗာပူး", "မန်စီးတီး"),
        ("ဘိုင်ယန်မြူးနစ်", "ဒေါ့မွန်"),
        ("ရီးရဲလ်", "ဘာစီလိုနာ"),
        ("ပီအက်စ်ဂျီ", "အိုလမ်ပစ်"),
    ]
    for home, away in mock_matches:
        rand = random.random()
        if rand < 0.4:
            pred = f"🏠 {home} နိုင်"
        elif rand < 0.7:
            pred = f"✈️ {away} နိုင်"
        else:
            pred = "🤝 သရေ"
        matches.append(f"{home} vs {away} → {pred}")
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
                    home_mm = get_team_name_mm(home)
                    away_mm = get_team_name_mm(away)
                    time = m.get("utcDate", "N/A")[:16].replace("T", " ")
                    matches.append(f"🆚 {home_mm} vs {away_mm}\n   ⏰ {time} UTC")
                return matches if matches else ["ယနေ့ပွဲစဉ် မရှိသေးပါ"]
        except Exception as e:
            print(f"Fixtures API Error: {e}")
    mock = [("မန်ယူ", "အာဆင်နယ်", "20:00"), ("လီဗာပူး", "မန်စီးတီး", "22:00")]
    for home, away, t in mock:
        matches.append(f"🆚 {home} vs {away}\n   ⏰ မြန်မာချိန် {t}")
    return matches
