import logging
import os
import threading
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
from config import BOT_TOKEN, ADMIN_ID
from database import add_user, get_package, set_package, can_access, get_history_by_date, get_recent_history, save_history, get_history_by_month, get_history_by_weeks
from predictions import (
    get_football_predictions, get_today_fixtures,
    get_thai_lottery_predictions, get_laos_lottery_predictions,
    get_thai_calendar, get_laos_calendar,
    get_lottery_results, set_lottery_result_admin, LotteryPredictor, FootballPredictor,
    get_past_football_results
)

logging.basicConfig(level=logging.INFO)

lottery_predictor = LotteryPredictor()
football_predictor = FootballPredictor()

# ---- Health Check Server (HEAD method ပါ) ----
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ['/', '/health']:
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_HEAD(self):
        if self.path in ['/', '/health']:
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

def run_health_server():
    port = int(os.environ.get('PORT', 8080))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    print(f"✅ Health check server running on port {port}")
    server.serve_forever()

# ---- Keyboard ----
def get_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("⚽ ဘောလုံးခန့်မှန်း", callback_data="football")],
        [InlineKeyboardButton("📅 ယနေ့ပွဲစဉ်စာရင်း", callback_data="fixtures")],
        [InlineKeyboardButton("📊 ပြီးခဲ့သော ဘောလုံးရလဒ်များ", callback_data="past_football")],
        [InlineKeyboardButton("🇹🇭 ထိုင်းထီခန့်မှန်း (ထိပ်ဆုံး ၅)", callback_data="lottery_thai")],
        [InlineKeyboardButton("🇱🇦 လာအိုထီခန့်မှန်း (ထိပ်ဆုံး ၅)", callback_data="lottery_laos")],
        [InlineKeyboardButton("📅 ထိုင်းထီကလင်ဒါ", callback_data="calendar_thai")],
        [InlineKeyboardButton("📅 လာအိုထီကလင်ဒါ", callback_data="calendar_laos")],
        [InlineKeyboardButton("📊 ဒီနေ့ထီထွက်ရလဒ်", callback_data="lottery_result")],
        [InlineKeyboardButton("💎 Premium ဝယ်ယူရန်", callback_data="premium_info")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ---- /start ----
def start(update: Update, context: CallbackContext):
    user = update.effective_user
    add_user(user.id, user.username, user.first_name)
    
    if user.id == ADMIN_ID:
        text = f"👑 မင်္ဂလာပါ Admin {user.first_name}!\n\nသင် Admin ဖြစ်တဲ့အတွက် Premium မလိုဘဲ အကုန်ကြည့်လို့ရပါတယ်။"
    else:
        text = f"မင်္ဂလာပါ {user.first_name}!\n\nဒီ Bot က ဘောလုံးပွဲ၊ ထိုင်းထီနဲ့ လာအိုထီတွေကို ခန့်မှန်းပေးပါတယ်။\nအောက်က ခလုတ်တွေနဲ့ ရွေးချယ်ပါ။"
    
    update.message.reply_text(text, reply_markup=get_main_keyboard())

# ---- Button Handler ----
def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id
    data = query.data

    # ---- ထိုင်းထီခန့်မှန်း (ထိပ်ဆုံး ၅) ----
    if data == "lottery_thai":
        if not can_access(user_id, "thai"):
            query.edit_message_text("⛔ ထိုင်းထီ Package မရှိသေးပါ။", reply_markup=get_main_keyboard())
            return
        predictions = get_thai_lottery_predictions()
        today = datetime.now().strftime("%Y-%m-%d")
        text = f"🇹🇭 **ထိုင်းထီခန့်မှန်း (ထိပ်ဆုံး ၅)**\n📅 {today} အတွက်\n\n"
        for p in predictions:
            emoji = "🥇" if p["rank"] == 1 else "🥈" if p["rank"] == 2 else "🥉" if p["rank"] == 3 else f"#{p['rank']}"
            text += f"{emoji} `{p['number']}` (၆လုံး) - ယုံကြည်မှု: {p['confidence']}\n"
        query.edit_message_text(text, reply_markup=get_main_keyboard())

    # ---- လာအိုထီခန့်မှန်း (ထိပ်ဆုံး ၅) ----
    elif data == "lottery_laos":
        if not can_access(user_id, "laos"):
            query.edit_message_text("⛔ လာအိုထီ Package မရှိသေးပါ။", reply_markup=get_main_keyboard())
            return
        predictions = get_laos_lottery_predictions()
        today = datetime.now().strftime("%Y-%m-%d")
        text = f"🇱🇦 **လာအိုထီခန့်မှန်း (ထိပ်ဆုံး ၅)**\n📅 {today} အတွက်\n\n"
        for p in predictions:
            emoji = "🥇" if p["rank"] == 1 else "🥈" if p["rank"] == 2 else "🥉" if p["rank"] == 3 else f"#{p['rank']}"
            text += f"{emoji} `{p['number']}` (၄လုံး) - ယုံကြည်မှု: {p['confidence']}\n"
        query.edit_message_text(text, reply_markup=get_main_keyboard())

    # ---- ပြီးခဲ့သော ဘောလုံးရလဒ်များ ----
    elif data == "past_football":
        if not can_access(user_id, "football"):
            query.edit_message_text("⛔ Full Package မရှိသေးပါ။", reply_markup=get_main_keyboard())
            return
        results = get_past_football_results()
        text = "📊 **ပြီးခဲ့သော ဘောလုံးရလဒ်များ**\n\n"
        if results:
            for r in results[:10]:
                text += f"🆚 {r}\n"
        else:
            text += "ပြီးခဲ့သော ဘောလုံးရလဒ်များ မရှိသေးပါ။"
        query.edit_message_text(text, reply_markup=get_main_keyboard())

    # ---- ထိုင်းထီကလင်ဒါ (ပြီးခဲ့တဲ့ ၃ လ) ----
    elif data == "calendar_thai":
        if not can_access(user_id, "thai"):
            query.edit_message_text("⛔ ထိုင်းထီ Package မရှိသေးပါ။", reply_markup=get_main_keyboard())
            return
        # ထွက်မယ့်ရက်တွေ
        dates = get_thai_calendar()
        text = "📅 **ထိုင်းထီထွက်မယ့်ရက်များ**\n\n"
        text += "🗓️ ထိုင်းထီက လ၁ရက်နဲ့ ၁၆ရက်တွေမှာ ထွက်ပါတယ်။\n\n"
        for d in dates:
            text += f"📌 {d}\n"
        
        # ပြီးခဲ့တဲ့ ၃ လက ထွက်ဂဏန်းများ
        history = get_history_by_month(3)
        if history:
            text += "\n📜 **ပြီးခဲ့တဲ့ ၃ လအတွင်း ထွက်ဂဏန်းများ**\n\n"
            for h in history[:10]:
                thai_num = h.get('thai', 'N/A')
                if len(thai_num) < 6:
                    thai_num = thai_num.zfill(6)
                text += f"📅 {h['date']} → `{thai_num}`\n"
        query.edit_message_text(text, reply_markup=get_main_keyboard())

    # ---- လာအိုထီကလင်ဒါ (ပြီးခဲ့တဲ့ ၄ ပတ်) ----
    elif data == "calendar_laos":
        if not can_access(user_id, "laos"):
            query.edit_message_text("⛔ လာအိုထီ Package မရှိသေးပါ။", reply_markup=get_main_keyboard())
            return
        # ထွက်မယ့်ရက်တွေ
        dates = get_laos_calendar()
        text = "📅 **လာအိုထီထွက်မယ့်ရက်များ**\n\n"
        text += "🗓️ လာအိုထီက တနင်္လာကနေ သောကြာအထိ နေ့စဉ်ထွက်ပါတယ်။\n\n"
        for d in dates:
            text += f"📌 {d}\n"
        
        # ပြီးခဲ့တဲ့ ၄ ပတ်က ထွက်ဂဏန်းများ
        history = get_history_by_weeks(4)
        if history:
            text += "\n📜 **ပြီးခဲ့တဲ့ ၄ ပတ်အတွင်း ထွက်ဂဏန်းများ**\n\n"
            for h in history[:10]:
                laos_num = h.get('laos', 'N/A')
                if len(laos_num) < 4:
                    laos_num = laos_num.zfill(4)
                text += f"📅 {h['date']} → `{laos_num}`\n"
        query.edit_message_text(text, reply_markup=get_main_keyboard())

    # ---- ဘောလုံး ----
    elif data == "football":
        if not can_access(user_id, "football"):
            query.edit_message_text("⛔ Full Package မရှိသေးပါ။", reply_markup=get_main_keyboard())
            return
        preds = get_football_predictions()
        text = "⚽ **ဘောလုံးခန့်မှန်း**\n" + "\n".join(preds)
        query.edit_message_text(text, reply_markup=get_main_keyboard())

    # ---- ပွဲစဉ်စာရင်း ----
    elif data == "fixtures":
        if not can_access(user_id, "fixtures"):
            query.edit_message_text("⛔ Full Package မရှိသေးပါ။", reply_markup=get_main_keyboard())
            return
        fixtures = get_today_fixtures()
        text = "📅 **ယနေ့ပွဲစဉ်များ (မြန်မာစံတော်ချိန်)**\n\n"
        for fixture in fixtures:
            if "⏰" in fixture:
                parts = fixture.split("⏰")
                time_part = parts[1].strip()
                try:
                    utc_str = time_part.replace(" UTC", "").strip()
                    utc_dt = datetime.strptime(utc_str, "%Y-%m-%d %H:%M")
                    mmt_dt = utc_dt + timedelta(hours=6, minutes=30)
                    mmt_str = mmt_dt.strftime("%Y-%m-%d %I:%M %p")
                    fixture = fixture.replace(time_part, f"{mmt_str} (မြန်မာချိန်)")
                except:
                    pass
            text += fixture + "\n\n"
        query.edit_message_text(text, reply_markup=get_main_keyboard())

    # ---- ဒီနေ့ထီရလဒ် ----
    elif data == "lottery_result":
        if not can_access(user_id, "lottery_result"):
            query.edit_message_text("⛔ Full Package မရှိသေးပါ။", reply_markup=get_main_keyboard())
            return
        res = get_lottery_results()
        text = f"📊 **ဒီနေ့ထီရလဒ်**\n🇹🇭 {res['thai']}\n🇱🇦 {res['laos']}\n📌 {res['source']}"
        query.edit_message_text(text, reply_markup=get_main_keyboard())

    # ---- Premium Info (WavePay Logo ဖျက်ပြီး) ----
    elif data == "premium_info":
        caption = (
            "💎 **Premium Package များ**\n\n"
            "🇹🇭 **ထိုင်းထီ**\n"
            "   • ၁၅ ရက်တစ်ခါ ထွက်သည်။\n"
            "   • တစ်ကြိမ်စာ - ၅၀,၀၀၀ ကျပ်\n"
            "   • တစ်လစာ (၂ကြိမ်) - ၈၀,၀၀၀ ကျပ်\n\n"
            "🇱🇦 **လာအိုထီ**\n"
            "   • တစ်ပတ် ၅ရက် (တနင်္လာ - သောကြာ) ထွက်သည်။\n"
            "   • တစ်ပတ်စာ (၅ကြိမ်) - ၅၀,၀၀၀ ကျပ် 🔥\n"
            "   • တစ်လစာ - ၁၈၀,၀၀၀ ကျပ်\n\n"
            "📲 **ငွေလွှဲရန်**\n"
            "💸 `09767011991 (Wave Account)`\n"
            "📝 ငွေလွှဲစရင်း Note တွင် ဝယ်ယူလိုသော Package အမည်ကို ရေးပါ။\n"
            "📩 ငွေလွှဲပြီးပါက ပြေစာကို အောက်ပါ Admin ထံ ပို့ပေးပါ။"
        )
        keyboard = [
            [InlineKeyboardButton("📩 Admin ကိုဆက်သွယ်ရန်", url="https://t.me/UzawgyiGoll")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(caption, reply_markup=reply_markup, parse_mode="Markdown")

# ---- Admin Commands ----
def add_premium(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("⛔ Admin မဟုတ်ပါ။")
        return
    try:
        uid = int(context.args[0]); pkg = context.args[1].lower()
        if pkg not in ["thai", "laos", "both"]:
            update.message.reply_text("❗ thai / laos / both သာထည့်ပါ။")
            return
        set_package(uid, pkg)
        update.message.reply_text(f"✅ User {uid} → {pkg}")
    except:
        update.message.reply_text("❗ /addpremium <user_id> <thai/laos/both>")

def remove_premium(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("⛔ Admin မဟုတ်ပါ။")
        return
    try:
        uid = int(context.args[0])
        set_package(uid, "free")
        update.message.reply_text(f"❌ User {uid} ကို ဖြုတ်လိုက်ပြီး။")
    except:
        update.message.reply_text("❗ /removepremium <user_id>")

def add_history(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("⛔ Admin မဟုတ်ပါ။")
        return
    try:
        date_str = context.args[0]; thai = context.args[1]; laos = context.args[2]
        datetime.strptime(date_str, "%Y-%m-%d")
        if len(thai)!=3 or len(laos)!=2:
            update.message.reply_text("❗ ထိုင်း ၃လုံး၊ လာအို ၂လုံးဖြစ်ရမယ်။")
            return
        save_history(date_str, thai, laos)
        update.message.reply_text(f"✅ {date_str} သိမ်းပြီး။\n🇹🇭 {thai}\n🇱🇦 {laos}")
    except:
        update.message.reply_text("❗ /addhistory YYYY-MM-DD THAI LAOS")

def set_result(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("⛔ Admin မဟုတ်ပါ။")
        return
    try:
        thai = context.args[0]; laos = context.args[1]
        set_lottery_result_admin(thai, laos)
        update.message.reply_text(f"✅ ဒီနေ့ရလဒ် သတ်မှတ်ပြီး။\n🇹🇭 {thai}\n🇱🇦 {laos}")
    except:
        update.message.reply_text("❗ /setresult THAI LAOS")

def search_history(update: Update, context: CallbackContext):
    uid = update.effective_user.id
    pkg = get_package(uid)
    if pkg == "free" and uid != ADMIN_ID:
        update.message.reply_text("⛔ Premium မရှိပါ။")
        return
    try:
        date_str = context.args[0]
        datetime.strptime(date_str, "%Y-%m-%d")
    except:
        update.message.reply_text("❗ /search YYYY-MM-DD")
        return
    res = get_history_by_date(date_str)
    if not res:
        update.message.reply_text(f"❌ {date_str} အတွက် ဒေတာမရှိပါ။")
        return
    text = f"🔍 **{date_str}**\n"
    if pkg in ["thai", "both"] or uid == ADMIN_ID:
        thai_num = res.get('thai', 'N/A')
        if len(thai_num) < 6:
            thai_num = thai_num.zfill(6)
        text += f"🇹🇭 {thai_num}\n"
    if pkg in ["laos", "both"] or uid == ADMIN_ID:
        laos_num = res.get('laos', 'N/A')
        if len(laos_num) < 4:
            laos_num = laos_num.zfill(4)
        text += f"🇱🇦 {laos_num}"
    update.message.reply_text(text)

# ---- Main ----
def main():
    # Health check server ကို Thread နဲ့ စတင်ပါ
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()
    
    # Bot ကို စတင်ပါ (Updater ကို ပြင်ဆင်ထားတယ်)
    updater = Updater(token=BOT_TOKEN)  # ← ဒီမှာ token= ထည့်ထားတယ်
    dispatcher = updater.dispatcher
    
    # Handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("addpremium", add_premium))
    dispatcher.add_handler(CommandHandler("removepremium", remove_premium))
    dispatcher.add_handler(CommandHandler("addhistory", add_history))
    dispatcher.add_handler(CommandHandler("setresult", set_result))
    dispatcher.add_handler(CommandHandler("search", search_history))
    dispatcher.add_handler(CallbackQueryHandler(button_handler))
    
    print("Bot is starting...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
