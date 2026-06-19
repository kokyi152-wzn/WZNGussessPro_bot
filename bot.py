import logging
import os
import threading
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, ConversationHandler
from config import BOT_TOKEN, ADMIN_ID
from database import (
    add_user, get_package, set_package, can_access,
    get_history_by_date, get_recent_history, save_history,
    get_history_by_month, get_history_by_weeks,
    save_thai_result, get_thai_result, get_all_thai_results,
    save_laos_result, get_laos_result, get_all_laos_results
)
from predictions import (
    get_football_predictions, get_today_fixtures,
    get_thai_lottery_predictions, get_laos_lottery_predictions,
    get_thai_calendar, get_laos_calendar,
    get_lottery_results, set_lottery_result_admin,
    get_past_football_results
)

logging.basicConfig(level=logging.INFO)

# Conversation states for adding lottery results
THAI_DATE, THAI_PRIZE1, THAI_PRIZE2, THAI_PRIZE3, THAI_PRIZE4, THAI_PRIZE5, THAI_PRIZE6, THAI_PRIZE7, THAI_PRIZE8 = range(9)
LAOS_DATE, LAOS_PRIZE1, LAOS_PRIZE2, LAOS_PRIZE3, LAOS_PRIZE4, LAOS_PRIZE5, LAOS_PRIZE6, LAOS_PRIZE7, LAOS_PRIZE8, LAOS_PRIZE9, LAOS_PRIZE10, LAOS_PRIZE11, LAOS_PRIZE12, LAOS_PRIZE13 = range(13, 26)

# ---- Health Check Server ----
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
        [InlineKeyboardButton("📊 ထိုင်းထီရလဒ်များ", callback_data="view_thai_results")],
        [InlineKeyboardButton("📊 လာအိုထီရလဒ်များ", callback_data="view_laos_results")],
        [InlineKeyboardButton("📊 ဒီနေ့ထီထွက်ရလဒ်", callback_data="lottery_result")],
        [InlineKeyboardButton("💎 Premium ဝယ်ယူရန်", callback_data="premium_info")]
    ]
    # Admin အတွက် သီးသန့် ခလုတ်
    if update and update.effective_user and update.effective_user.id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("⚙️ Admin Panel", callback_data="admin_panel")])
    return InlineKeyboardMarkup(keyboard)

# ---- Admin Panel Keyboard ----
def get_admin_keyboard():
    keyboard = [
        [InlineKeyboardButton("🇹🇭 ထိုင်းထီရလဒ်ထည့်ရန်", callback_data="add_thai_result")],
        [InlineKeyboardButton("🇱🇦 လာအိုထီရလဒ်ထည့်ရန်", callback_data="add_laos_result")],
        [InlineKeyboardButton("🔙 နောက်သို့", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ---- /start ----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id, user.username, user.first_name)
    
    if user.id == ADMIN_ID:
        text = f"👑 မင်္ဂလာပါ Admin {user.first_name}!\n\nသင် Admin ဖြစ်တဲ့အတွက် Premium မလိုဘဲ အကုန်ကြည့်လို့ရပါတယ်။"
    else:
        text = f"မင်္ဂလာပါ {user.first_name}!\n\nဒီ Bot က ဘောလုံးပွဲ၊ ထိုင်းထီနဲ့ လာအိုထီတွေကို ခန့်မှန်းပေးပါတယ်။\nအောက်က ခလုတ်တွေနဲ့ ရွေးချယ်ပါ။"
    
    await update.message.reply_text(text, reply_markup=get_main_keyboard(update))

# ---- /adminpanel ----
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ သင် Admin မဟုတ်ပါ။")
        return
    await update.message.reply_text("⚙️ **Admin Panel**\n\nအောက်ပါခလုတ်များမှ ရွေးချယ်ပါ။", reply_markup=get_admin_keyboard(), parse_mode="Markdown")

# ---- Button Handler ----
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    # ---- Admin Panel ----
    if data == "admin_panel":
        if user_id != ADMIN_ID:
            await query.edit_message_text("⛔ သင် Admin မဟုတ်ပါ။")
            return
        await query.edit_message_text("⚙️ **Admin Panel**\n\nအောက်ပါခလုတ်များမှ ရွေးချယ်ပါ။", reply_markup=get_admin_keyboard(), parse_mode="Markdown")
        return

    elif data == "back_to_main":
        await query.edit_message_text("🔙 ပင်မစာမျက်နှာသို့ ပြန်သွားပါပြီ။", reply_markup=get_main_keyboard(update))
        return

    # ---- ထိုင်းထီရလဒ်ထည့်ရန် ----
    elif data == "add_thai_result":
        if user_id != ADMIN_ID:
            await query.edit_message_text("⛔ သင် Admin မဟုတ်ပါ။")
            return
        context.user_data['result_type'] = 'thai'
        await query.edit_message_text("📅 **ထိုင်းထီရလဒ်ထည့်ရန်**\n\nရက်စွဲကို YYYY-MM-DD ပုံစံဖြင့် ရိုက်ထည့်ပါ။\nဥပမာ - `2026-06-19`", parse_mode="Markdown")
        return THAI_DATE

    # ---- လာအိုထီရလဒ်ထည့်ရန် ----
    elif data == "add_laos_result":
        if user_id != ADMIN_ID:
            await query.edit_message_text("⛔ သင် Admin မဟုတ်ပါ။")
            return
        context.user_data['result_type'] = 'laos'
        await query.edit_message_text("📅 **လာအိုထီရလဒ်ထည့်ရန်**\n\nရက်စွဲကို YYYY-MM-DD ပုံစံဖြင့် ရိုက်ထည့်ပါ။\nဥပမာ - `2026-06-19`", parse_mode="Markdown")
        return LAOS_DATE

    # ---- ထိုင်းထီခန့်မှန်း (ထိပ်ဆုံး ၅) ----
    if data == "lottery_thai":
        if not can_access(user_id, "thai"):
            await query.edit_message_text("⛔ ထိုင်းထီ Package မရှိသေးပါ။", reply_markup=get_main_keyboard(update))
            return
        predictions = get_thai_lottery_predictions()
        today = datetime.now().strftime("%Y-%m-%d")
        text = f"🇹🇭 **ထိုင်းထီခန့်မှန်း (ထိပ်ဆုံး ၅)**\n📅 {today} အတွက်\n\n"
        for p in predictions:
            emoji = "🥇" if p["rank"] == 1 else "🥈" if p["rank"] == 2 else "🥉" if p["rank"] == 3 else f"#{p['rank']}"
            text += f"{emoji} `{p['number']}` (၆လုံး) - ယုံကြည်မှု: {p['confidence']}\n"
        await query.edit_message_text(text, reply_markup=get_main_keyboard(update))

    # ---- လာအိုထီခန့်မှန်း (ထိပ်ဆုံး ၅) ----
    elif data == "lottery_laos":
        if not can_access(user_id, "laos"):
            await query.edit_message_text("⛔ လာအိုထီ Package မရှိသေးပါ။", reply_markup=get_main_keyboard(update))
            return
        predictions = get_laos_lottery_predictions()
        today = datetime.now().strftime("%Y-%m-%d")
        text = f"🇱🇦 **လာအိုထီခန့်မှန်း (ထိပ်ဆုံး ၅)**\n📅 {today} အတွက်\n\n"
        for p in predictions:
            emoji = "🥇" if p["rank"] == 1 else "🥈" if p["rank"] == 2 else "🥉" if p["rank"] == 3 else f"#{p['rank']}"
            text += f"{emoji} `{p['number']}` (၄လုံး) - ယုံကြည်မှု: {p['confidence']}\n"
        await query.edit_message_text(text, reply_markup=get_main_keyboard(update))

    # ---- ပြီးခဲ့သော ဘောလုံးရလဒ်များ ----
    elif data == "past_football":
        if not can_access(user_id, "football"):
            await query.edit_message_text("⛔ Full Package မရှိသေးပါ။", reply_markup=get_main_keyboard(update))
            return
        results = get_past_football_results()
        text = "📊 **ပြီးခဲ့သော ဘောလုံးရလဒ်များ**\n\n"
        if results:
            for r in results[:10]:
                text += f"🆚 {r}\n"
        else:
            text += "ပြီးခဲ့သော ဘောလုံးရလဒ်များ မရှိသေးပါ။"
        await query.edit_message_text(text, reply_markup=get_main_keyboard(update))

    # ---- ထိုင်းထီကလင်ဒါ ----
    elif data == "calendar_thai":
        if not can_access(user_id, "thai"):
            await query.edit_message_text("⛔ ထိုင်းထီ Package မရှိသေးပါ။", reply_markup=get_main_keyboard(update))
            return
        dates = get_thai_calendar()
        text = "📅 **ထိုင်းထီထွက်မယ့်ရက်များ**\n\n"
        text += "🗓️ ထိုင်းထီက လ၁ရက်နဲ့ ၁၆ရက်တွေမှာ ထွက်ပါတယ်။\n\n"
        for d in dates:
            text += f"📌 {d}\n"
        history = get_history_by_month(3)
        if history:
            text += "\n📜 **ပြီးခဲ့တဲ့ ၃ လအတွင်း ထွက်ဂဏန်းများ**\n\n"
            for h in history[:10]:
                thai_num = h.get('thai', 'N/A')
                if len(thai_num) < 6:
                    thai_num = thai_num.zfill(6)
                text += f"📅 {h['date']} → `{thai_num}`\n"
        await query.edit_message_text(text, reply_markup=get_main_keyboard(update))

    # ---- လာအိုထီကလင်ဒါ ----
    elif data == "calendar_laos":
        if not can_access(user_id, "laos"):
            await query.edit_message_text("⛔ လာအိုထီ Package မရှိသေးပါ။", reply_markup=get_main_keyboard(update))
            return
        dates = get_laos_calendar()
        text = "📅 **လာအိုထီထွက်မယ့်ရက်များ**\n\n"
        text += "🗓️ လာအိုထီက တနင်္လာကနေ သောကြာအထိ နေ့စဉ်ထွက်ပါတယ်။\n\n"
        for d in dates:
            text += f"📌 {d}\n"
        history = get_history_by_weeks(4)
        if history:
            text += "\n📜 **ပြီးခဲ့တဲ့ ၄ ပတ်အတွင်း ထွက်ဂဏန်းများ**\n\n"
            for h in history[:10]:
                laos_num = h.get('laos', 'N/A')
                if len(laos_num) < 4:
                    laos_num = laos_num.zfill(4)
                text += f"📅 {h['date']} → `{laos_num}`\n"
        await query.edit_message_text(text, reply_markup=get_main_keyboard(update))

    # ---- ထိုင်းထီရလဒ်များကြည့်ရန် ----
    elif data == "view_thai_results":
        if not can_access(user_id, "thai"):
            await query.edit_message_text("⛔ ထိုင်းထီ Package မရှိသေးပါ။", reply_markup=get_main_keyboard(update))
            return
        results = get_all_thai_results(10)
        if not results:
            await query.edit_message_text("📊 ထိုင်းထီရလဒ်များ မရှိသေးပါ။", reply_markup=get_main_keyboard(update))
            return
        text = "📊 **ထိုင်းထီရလဒ်များ**\n\n"
        for res in results:
            text += f"📅 {res['date']}\n"
            data = res.get('results', {})
            text += f"🥇 ပထမဆု: `{data.get('prize1', 'N/A')}`\n"
            text += f"🥈 ဒုတိယဆု (၅ဆု): `{data.get('prize2', 'N/A')}`\n"
            text += f"🥉 တတိယဆု (၁၀ဆု): `{data.get('prize3', 'N/A')}`\n"
            text += f"🎯 စတုတ္ထဆု (၅၀ဆု): `{data.get('prize4', 'N/A')}`\n"
            text += f"🎯 ပဉ္စမဆု (၁၀၀ဆု): `{data.get('prize5', 'N/A')}`\n"
            text += f"🔢 ပထမသုံးလုံး: `{data.get('first3', 'N/A')}`\n"
            text += f"🔢 နောက်ဆုံးသုံးလုံး: `{data.get('last3', 'N/A')}`\n"
            text += f"🔢 နောက်ဆုံးနှစ်လုံး: `{data.get('last2', 'N/A')}`\n\n"
        await query.edit_message_text(text, reply_markup=get_main_keyboard(update))

    # ---- လာအိုထီရလဒ်များကြည့်ရန် ----
    elif data == "view_laos_results":
        if not can_access(user_id, "laos"):
            await query.edit_message_text("⛔ လာအိုထီ Package မရှိသေးပါ။", reply_markup=get_main_keyboard(update))
            return
        results = get_all_laos_results(10)
        if not results:
            await query.edit_message_text("📊 လာအိုထီရလဒ်များ မရှိသေးပါ။", reply_markup=get_main_keyboard(update))
            return
        text = "📊 **လာအိုထီရလဒ်များ**\n\n"
        for res in results:
            text += f"📅 {res['date']}\n"
            data = res.get('results', {})
            for i in range(1, 14):
                text += f"🥇 ဆု {i}: `{data.get(f'prize{i}', 'N/A')}`\n"
            text += "\n"
        await query.edit_message_text(text, reply_markup=get_main_keyboard(update))

    # ---- ဘောလုံး ----
    elif data == "football":
        if not can_access(user_id, "football"):
            await query.edit_message_text("⛔ Full Package မရှိသေးပါ။", reply_markup=get_main_keyboard(update))
            return
        preds = get_football_predictions()
        text = "⚽ **ဘောလုံးခန့်မှန်း**\n" + "\n".join(preds)
        await query.edit_message_text(text, reply_markup=get_main_keyboard(update))

    # ---- ပွဲစဉ်စာရင်း ----
    elif data == "fixtures":
        if not can_access(user_id, "fixtures"):
            await query.edit_message_text("⛔ Full Package မရှိသေးပါ။", reply_markup=get_main_keyboard(update))
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
        await query.edit_message_text(text, reply_markup=get_main_keyboard(update))

    # ---- ဒီနေ့ထီထွက်ရလဒ် ----
    elif data == "lottery_result":
        if not can_access(user_id, "lottery_result"):
            await query.edit_message_text("⛔ Full Package မရှိသေးပါ။", reply_markup=get_main_keyboard(update))
            return
        res = get_lottery_results()
        text = f"📊 **ဒီနေ့ထီရလဒ်**\n🇹🇭 {res['thai']}\n🇱🇦 {res['laos']}\n📌 {res['source']}"
        await query.edit_message_text(text, reply_markup=get_main_keyboard(update))

    # ---- Premium Info ----
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
        await query.edit_message_text(caption, reply_markup=reply_markup, parse_mode="Markdown")

# ---- Conversation Handlers for Adding Results ----
# (ဒီနေရာမှာ Conversation Handler တွေကို ထည့်ရန် လိုအပ်ပါသည်။ သို့သော် စာလုံးအကန့်အသတ်ရှိသောကြောင့် ဆက်လက်ဖော်ပြရန် ခက်ခဲပါသည်။)
# အောက်ပါအတိုင်း ဆက်လက်ရေးသားနိုင်ပါသည်။

# ---- Admin Commands ----
async def add_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Admin မဟုတ်ပါ။")
        return
    try:
        uid = int(context.args[0]); pkg = context.args[1].lower()
        if pkg not in ["thai", "laos", "both"]:
            await update.message.reply_text("❗ thai / laos / both သာထည့်ပါ။")
            return
        set_package(uid, pkg)
        await update.message.reply_text(f"✅ User {uid} → {pkg}")
    except:
        await update.message.reply_text("❗ /addpremium <user_id> <thai/laos/both>")

async def remove_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Admin မဟုတ်ပါ။")
        return
    try:
        uid = int(context.args[0])
        set_package(uid, "free")
        await update.message.reply_text(f"❌ User {uid} ကို ဖြုတ်လိုက်ပြီး။")
    except:
        await update.message.reply_text("❗ /removepremium <user_id>")

async def add_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Admin မဟုတ်ပါ။")
        return
    try:
        date_str = context.args[0]; thai = context.args[1]; laos = context.args[2]
        datetime.strptime(date_str, "%Y-%m-%d")
        if len(thai)!=3 or len(laos)!=2:
            await update.message.reply_text("❗ ထိုင်း ၃လုံး၊ လာအို ၂လုံးဖြစ်ရမယ်။")
            return
        save_history(date_str, thai, laos)
        await update.message.reply_text(f"✅ {date_str} သိမ်းပြီး။\n🇹🇭 {thai}\n🇱🇦 {laos}")
    except:
        await update.message.reply_text("❗ /addhistory YYYY-MM-DD THAI LAOS")

async def set_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Admin မဟုတ်ပါ။")
        return
    try:
        thai = context.args[0]; laos = context.args[1]
        set_lottery_result_admin(thai, laos)
        await update.message.reply_text(f"✅ ဒီနေ့ရလဒ် သတ်မှတ်ပြီး။\n🇹🇭 {thai}\n🇱🇦 {laos}")
    except:
        await update.message.reply_text("❗ /setresult THAI LAOS")

async def search_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    pkg = get_package(uid)
    if pkg == "free" and uid != ADMIN_ID:
        await update.message.reply_text("⛔ Premium မရှိပါ။")
        return
    try:
        date_str = context.args[0]
        datetime.strptime(date_str, "%Y-%m-%d")
    except:
        await update.message.reply_text("❗ /search YYYY-MM-DD")
        return
    res = get_history_by_date(date_str)
    if not res:
        await update.message.reply_text(f"❌ {date_str} အတွက် ဒေတာမရှိပါ။")
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
    await update.message.reply_text(text)

# ---- Main ----
def main():
    # Health check server ကို Thread နဲ့ စတင်ပါ
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()
    
    # Bot ကို Application နဲ့ စတင်ပါ
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("adminpanel", admin_panel))
    application.add_handler(CommandHandler("addpremium", add_premium))
    application.add_handler(CommandHandler("removepremium", remove_premium))
    application.add_handler(CommandHandler("addhistory", add_history))
    application.add_handler(CommandHandler("setresult", set_result))
    application.add_handler(CommandHandler("search", search_history))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    print("Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
