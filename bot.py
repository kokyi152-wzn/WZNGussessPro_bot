import logging
import os
import threading
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from config import BOT_TOKEN, ADMIN_ID
from database import add_user, get_package, set_package, can_access, get_history_by_date, get_recent_history, save_history, get_history_by_month, get_history_by_weeks, save_full_thai_result, save_full_laos_result, get_full_thai_result, get_full_laos_result
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
        [InlineKeyboardButton("📊 ဒီနေ့ထီထွက်ရလဒ်", callback_data="lottery_result")],
        [InlineKeyboardButton("💎 Premium ဝယ်ယူရန်", callback_data="premium_info")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ---- Admin Keyboard ----
def get_admin_keyboard():
    keyboard = [
        [InlineKeyboardButton("📝 ထိုင်းထီရလဒ်ထည့်ရန်", callback_data="admin_add_thai")],
        [InlineKeyboardButton("📝 လာအိုထီရလဒ်ထည့်ရန်", callback_data="admin_add_laos")],
        [InlineKeyboardButton("📋 ထိုင်းထီရလဒ်ကြည့်ရန်", callback_data="admin_view_thai")],
        [InlineKeyboardButton("📋 လာအိုထီရလဒ်ကြည့်ရန်", callback_data="admin_view_laos")],
        [InlineKeyboardButton("📊 ပြီးခဲ့သော ဘောလုံးရလဒ်များ", callback_data="past_football")],
        [InlineKeyboardButton("🔙 နောက်သို့", callback_data="admin_back")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ---- /start ----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id, user.username, user.first_name)
    
    if user.id == ADMIN_ID:
        text = f"👑 မင်္ဂလာပါ Admin {user.first_name}!\n\nသင်သည် Admin ဖြစ်ပါသည်။\nအောက်ပါ ခလုတ်များကို အသုံးပြုနိုင်ပါသည်။"
        await update.message.reply_text(text, reply_markup=get_admin_keyboard())
    else:
        text = f"မင်္ဂလာပါ {user.first_name}!\n\nဒီ Bot က ဘောလုံးပွဲ၊ ထိုင်းထီနဲ့ လာအိုထီတွေကို ခန့်မှန်းပေးပါတယ်။\nအောက်က ခလုတ်တွေနဲ့ ရွေးချယ်ပါ။"
        await update.message.reply_text(text, reply_markup=get_main_keyboard())

# ---- Button Handler ----
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    user = query.from_user

    # ---- Admin Menu ----
    if data == "admin_back":
        await query.edit_message_text("👑 Admin Menu", reply_markup=get_admin_keyboard())
        return

    elif data == "admin_add_thai":
        if user_id != ADMIN_ID:
            await query.edit_message_text("⛔ သင်သည် Admin မဟုတ်ပါ။")
            return
        await query.edit_message_text(
            "📝 **ထိုင်းထီရလဒ်ထည့်ရန်**\n\n"
            "အောက်ပါပုံစံအတိုင်း ရိုက်ထည့်ပါ။\n\n"
            "`/addthai YYYY-MM-DD|1st|2nd|3rd|4th|5th|6th|7th|8th|9th|10th|11th|12th|13th|14th|15th|16th|17th|18th|19th|20th`\n\n"
            "ဥပမာ:\n"
            "`/addthai 2026-06-19|123456|234567|345678|456789|567890|678901|789012|890123|901234|012345|123450|234501|345012|450123|501234|612345|723456|834567|945678|056789`\n\n"
            "📌 ဂဏန်းတစ်ခုစီသည် ၆ လုံးဖြစ်ရပါမည်။",
            parse_mode="Markdown"
        )
        return

    elif data == "admin_add_laos":
        if user_id != ADMIN_ID:
            await query.edit_message_text("⛔ သင်သည် Admin မဟုတ်ပါ။")
            return
        await query.edit_message_text(
            "📝 **လာအိုထီရလဒ်ထည့်ရန်**\n\n"
            "အောက်ပါပုံစံအတိုင်း ရိုက်ထည့်ပါ။\n\n"
            "`/addlaos YYYY-MM-DD|1st|2nd|3rd|4th|5th|6th|7th|8th|9th|10th|11th|12th|13th`\n\n"
            "ဥပမာ:\n"
            "`/addlaos 2026-06-19|1234|2345|3456|4567|5678|6789|7890|8901|9012|0123|1230|2340|3450`\n\n"
            "📌 ဂဏန်းတစ်ခုစီသည် ၄ လုံးဖြစ်ရပါမည်။",
            parse_mode="Markdown"
        )
        return

    elif data == "admin_view_thai":
        if user_id != ADMIN_ID:
            await query.edit_message_text("⛔ သင်သည် Admin မဟုတ်ပါ။")
            return
        results = get_full_thai_result()
        if not results:
            await query.edit_message_text("📋 ထိုင်းထီရလဒ် မရှိသေးပါ။", reply_markup=get_admin_keyboard())
            return
        text = "📋 **ထိုင်းထီရလဒ်များ**\n\n"
        for r in results[:10]:
            text += f"📅 {r.get('date', 'N/A')}\n"
            for i in range(1, 21):
                prize = r.get(f'prize_{i}', 'N/A')
                text += f"  {i}st: `{prize}`\n"
            text += "\n"
        await query.edit_message_text(text, reply_markup=get_admin_keyboard(), parse_mode="Markdown")

    elif data == "admin_view_laos":
        if user_id != ADMIN_ID:
            await query.edit_message_text("⛔ သင်သည် Admin မဟုတ်ပါ။")
            return
        results = get_full_laos_result()
        if not results:
            await query.edit_message_text("📋 လာအိုထီရလဒ် မရှိသေးပါ။", reply_markup=get_admin_keyboard())
            return
        text = "📋 **လာအိုထီရလဒ်များ**\n\n"
        for r in results[:10]:
            text += f"📅 {r.get('date', 'N/A')}\n"
            for i in range(1, 14):
                prize = r.get(f'prize_{i}', 'N/A')
                text += f"  {i}st: `{prize}`\n"
            text += "\n"
        await query.edit_message_text(text, reply_markup=get_admin_keyboard(), parse_mode="Markdown")

    # ---- User Features ----
    elif data == "past_football":
        if not can_access(user_id, "past_football"):
            await query.edit_message_text("⛔ Full Package မရှိသေးပါ။", reply_markup=get_main_keyboard() if user_id != ADMIN_ID else get_admin_keyboard())
            return
        results = get_past_football_results()
        
        if not results or results == ["ပြီးခဲ့သော ၇ ရက်အတွင်း ဘောလုံးရလဒ်များ မရှိသေးပါ။"]:
            text = "📊 **ပြီးခဲ့သော ၇ ရက်အတွင်း ဘောလုံးရလဒ်များ**\n\n"
            text += "📭 ပြီးခဲ့သော ၇ ရက်အတွင်း ဘောလုံးရလဒ်များ မရှိသေးပါ။"
            await query.edit_message_text(text, reply_markup=get_admin_keyboard() if user_id == ADMIN_ID else get_main_keyboard())
            return
        
        text = "📊 **ပြီးခဲ့သော ၇ ရက်အတွင်း ဘောလုံးရလဒ်များ**\n\n"
        text += "🟢 ဇယားရှင်းလင်းချက်:\n"
        text += "🏠 = အိမ်ကွင်း | ✈️ = အဝေးကွင်း | ⚽ = ဂိုးရလဒ်\n"
        text += "🟨 = Yellow Card | 🟥 = Red Card | 📊 = ပွဲအခြေအနေ\n\n"
        
        for result in results[:10]:
            text += f"{result}\n\n"
        
        await query.edit_message_text(text, reply_markup=get_admin_keyboard() if user_id == ADMIN_ID else get_main_keyboard())

    elif data == "lottery_thai":
        if not can_access(user_id, "thai"):
            await query.edit_message_text("⛔ ထိုင်းထီ Package မရှိသေးပါ။", reply_markup=get_main_keyboard())
            return
        predictions = get_thai_lottery_predictions()
        today = datetime.now().strftime("%Y-%m-%d")
        text = f"🇹🇭 **ထိုင်းထီခန့်မှန်း (ထိပ်ဆုံး ၅)**\n📅 {today} အတွက်\n\n"
        for p in predictions:
            emoji = "🥇" if p["rank"] == 1 else "🥈" if p["rank"] == 2 else "🥉" if p["rank"] == 3 else f"#{p['rank']}"
            text += f"{emoji} `{p['number']}` (၆လုံး) - ယုံကြည်မှု: {p['confidence']}\n"
        await query.edit_message_text(text, reply_markup=get_main_keyboard())

    elif data == "lottery_laos":
        if not can_access(user_id, "laos"):
            await query.edit_message_text("⛔ လာအိုထီ Package မရှိသေးပါ။", reply_markup=get_main_keyboard())
            return
        predictions = get_laos_lottery_predictions()
        today = datetime.now().strftime("%Y-%m-%d")
        text = f"🇱🇦 **လာအိုထီခန့်မှန်း (ထိပ်ဆုံး ၅)**\n📅 {today} အတွက်\n\n"
        for p in predictions:
            emoji = "🥇" if p["rank"] == 1 else "🥈" if p["rank"] == 2 else "🥉" if p["rank"] == 3 else f"#{p['rank']}"
            text += f"{emoji} `{p['number']}` (၄လုံး) - ယုံကြည်မှု: {p['confidence']}\n"
        await query.edit_message_text(text, reply_markup=get_main_keyboard())

    elif data == "calendar_thai":
        if not can_access(user_id, "thai"):
            await query.edit_message_text("⛔ ထိုင်းထီ Package မရှိသေးပါ။", reply_markup=get_main_keyboard())
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
        await query.edit_message_text(text, reply_markup=get_main_keyboard())

    elif data == "calendar_laos":
        if not can_access(user_id, "laos"):
            await query.edit_message_text("⛔ လာအိုထီ Package မရှိသေးပါ။", reply_markup=get_main_keyboard())
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
        await query.edit_message_text(text, reply_markup=get_main_keyboard())

    elif data == "football":
        if not can_access(user_id, "football"):
            await query.edit_message_text("⛔ Full Package မရှိသေးပါ။", reply_markup=get_main_keyboard())
            return
        preds = get_football_predictions()
        text = "⚽ **ဘောလုံးခန့်မှန်း**\n" + "\n".join(preds)
        await query.edit_message_text(text, reply_markup=get_main_keyboard())

    elif data == "fixtures":
        if not can_access(user_id, "fixtures"):
            await query.edit_message_text("⛔ Full Package မရှိသေးပါ။", reply_markup=get_main_keyboard())
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
        await query.edit_message_text(text, reply_markup=get_main_keyboard())

    elif data == "lottery_result":
        if not can_access(user_id, "lottery_result"):
            await query.edit_message_text("⛔ Full Package မရှိသေးပါ။", reply_markup=get_main_keyboard())
            return
        res = get_lottery_results()
        text = f"📊 **ဒီနေ့ထီရလဒ်**\n🇹🇭 {res['thai']}\n🇱🇦 {res['laos']}\n📌 {res['source']}"
        await query.edit_message_text(text, reply_markup=get_main_keyboard())

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

async def add_thai_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Admin မဟုတ်ပါ။")
        return
    try:
        args = ' '.join(context.args).split('|')
        if len(args) < 2:
            await update.message.reply_text(
                "❗ ပုံစံမှားနေပါသည်။\n"
                "ဥပမာ: `/addthai YYYY-MM-DD|1st|2nd|3rd|...|20th`"
            )
            return
        
        date_str = args[0]
        datetime.strptime(date_str, "%Y-%m-%d")
        
        result_data = {"date": date_str}
        for i, prize in enumerate(args[1:], 1):
            if len(prize) != 6:
                prize = prize.zfill(6)
            result_data[f"prize_{i}"] = prize
        
        save_full_thai_result(result_data)
        await update.message.reply_text(f"✅ {date_str} ရက်စွဲအတွက် ထိုင်းထီရလဒ် {len(args)-1} ခု သိမ်းဆည်းပြီးပါပြီ။")
    except Exception as e:
        await update.message.reply_text(f"❗ အမှားရှိနေပါသည်။\nError: {str(e)}")

async def add_laos_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Admin မဟုတ်ပါ။")
        return
    try:
        args = ' '.join(context.args).split('|')
        if len(args) < 2:
            await update.message.reply_text(
                "❗ ပုံစံမှားနေပါသည်။\n"
                "ဥပမာ: `/addlaos YYYY-MM-DD|1st|2nd|3rd|...|13th`"
            )
            return
        
        date_str = args[0]
        datetime.strptime(date_str, "%Y-%m-%d")
        
        result_data = {"date": date_str}
        for i, prize in enumerate(args[1:], 1):
            if len(prize) != 4:
                prize = prize.zfill(4)
            result_data[f"prize_{i}"] = prize
        
        save_full_laos_result(result_data)
        await update.message.reply_text(f"✅ {date_str} ရက်စွဲအတွက် လာအိုထီရလဒ် {len(args)-1} ခု သိမ်းဆည်းပြီးပါပြီ။")
    except Exception as e:
        await update.message.reply_text(f"❗ အမှားရှိနေပါသည်။\nError: {str(e)}")

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
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("addpremium", add_premium))
    application.add_handler(CommandHandler("removepremium", remove_premium))
    application.add_handler(CommandHandler("addhistory", add_history))
    application.add_handler(CommandHandler("setresult", set_result))
    application.add_handler(CommandHandler("search", search_history))
    application.add_handler(CommandHandler("addthai", add_thai_result))
    application.add_handler(CommandHandler("addlaos", add_laos_result))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    print("Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
