import logging
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from config import BOT_TOKEN, ADMIN_ID
from database import add_user, get_package, set_package, can_access, get_history_by_date, get_recent_history, save_history
from predictions import (
    get_football_predictions, get_today_fixtures, get_lottery_predictions,
    get_lottery_results, set_lottery_result_admin, LotteryPredictor, FootballPredictor
)

logging.basicConfig(level=logging.INFO)

lottery_predictor = LotteryPredictor()
football_predictor = FootballPredictor()

def get_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("⚽ ဘောလုံးခန့်မှန်း", callback_data="football")],
        [InlineKeyboardButton("📅 ယနေ့ပွဲစဉ်စာရင်း", callback_data="fixtures")],
        [InlineKeyboardButton("📜 ထိုင်းထီသမိုင်း (နောက်ဆုံး ၁၀)", callback_data="history_thai")],
        [InlineKeyboardButton("📜 လာအိုထီသမိုင်း (နောက်ဆုံး ၁၀)", callback_data="history_laos")],
        [InlineKeyboardButton("🔍 ရက်အလိုက် ရှာဖွေရန်", callback_data="search_date")],
        [InlineKeyboardButton("🇹🇭 ထိုင်းထီခန့်မှန်း", callback_data="lottery_thai")],
        [InlineKeyboardButton("🇱🇦 လာအိုထီခန့်မှန်း", callback_data="lottery_laos")],
        [InlineKeyboardButton("📊 ဒီနေ့ထီထွက်ရလဒ်", callback_data="lottery_result")],
        [InlineKeyboardButton("💎 Premium ဝယ်ယူရန်", callback_data="premium_info")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id, user.username, user.first_name)
    
    if user.id == ADMIN_ID:
        text = f"👑 မင်္ဂလာပါ Admin {user.first_name}!\n\nသင် Admin ဖြစ်တဲ့အတွက် Premium မလိုဘဲ အကုန်ကြည့်လို့ရပါတယ်။"
    else:
        text = f"မင်္ဂလာပါ {user.first_name}!\n\nဒီ Bot က ဘောလုံးပွဲ၊ ထိုင်းထီနဲ့ လာအိုထီတွေကို ခန့်မှန်းပေးပါတယ်။\nအောက်က ခလုတ်တွေနဲ့ ရွေးချယ်ပါ။"
    
    await update.message.reply_text(text, reply_markup=get_main_keyboard())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data == "lottery_thai":
        if not can_access(user_id, "thai"):
            await query.edit_message_text("⛔ ထိုင်းထီ Package မရှိသေးပါ။", reply_markup=get_main_keyboard())
            return
        basic_pred = get_lottery_predictions()
        advanced_pred = lottery_predictor.predict()
        text = f"🇹🇭 **ထိုင်းထီခန့်မှန်း**\n\n📊 Basic: `{basic_pred['thai']}`\n🧠 Advanced: `{advanced_pred}`"
        await query.edit_message_text(text, reply_markup=get_main_keyboard())

    elif data == "lottery_laos":
        if not can_access(user_id, "laos"):
            await query.edit_message_text("⛔ လာအိုထီ Package မရှိသေးပါ။", reply_markup=get_main_keyboard())
            return
        basic_pred = get_lottery_predictions()
        text = f"🇱🇦 **လာအိုထီခန့်မှန်း**\n\n📊 Basic: `{basic_pred['laos']}`"
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
        text = "📅 **ယနေ့ပွဲစဉ်များ**\n\n" + "\n".join(fixtures)
        await query.edit_message_text(text, reply_markup=get_main_keyboard())

    elif data == "lottery_result":
        if not can_access(user_id, "lottery_result"):
            await query.edit_message_text("⛔ Full Package မရှိသေးပါ။", reply_markup=get_main_keyboard())
            return
        res = get_lottery_results()
        text = f"📊 **ဒီနေ့ထီရလဒ်**\n🇹🇭 {res['thai']}\n🇱🇦 {res['laos']}\n📌 {res['source']}"
        await query.edit_message_text(text, reply_markup=get_main_keyboard())

    elif data == "history_thai":
        if not can_access(user_id, "thai"):
            await query.edit_message_text("⛔ ထိုင်းထီ Package မရှိသေးပါ။", reply_markup=get_main_keyboard())
            return
        history = get_recent_history(10)
        if not history:
            text = "📜 ထိုင်းထီသမိုင်း မရှိသေးပါ။"
        else:
            text = "📜 **ထိုင်းထီသမိုင်း (နောက်ဆုံး ၁၀)**\n\n"
            for doc in history:
                text += f"📅 {doc['date']} → `{doc['thai']}`\n"
        await query.edit_message_text(text, reply_markup=get_main_keyboard())

    elif data == "history_laos":
        if not can_access(user_id, "laos"):
            await query.edit_message_text("⛔ လာအိုထီ Package မရှိသေးပါ။", reply_markup=get_main_keyboard())
            return
        history = get_recent_history(10)
        if not history:
            text = "📜 လာအိုထီသမိုင်း မရှိသေးပါ။"
        else:
            text = "📜 **လာအိုထီသမိုင်း (နောက်ဆုံး ၁၀)**\n\n"
            for doc in history:
                text += f"📅 {doc['date']} → `{doc['laos']}`\n"
        await query.edit_message_text(text, reply_markup=get_main_keyboard())

    elif data == "search_date":
        await query.edit_message_text("🔍 `/search YYYY-MM-DD` ပုံစံထည့်ပါ။\nဥပမာ - `/search 2026-06-15`", reply_markup=get_main_keyboard())

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
            "💸 `09767011991`\n"
            "📝 ငွေလွှဲစရင်း Note တွင် ဝယ်ယူလိုသော Package အမည်ကို ရေးပါ။\n"
            "📩 ငွေလွှဲပြီးပါက ပြေစာကို အောက်ပါ Admin ထံ ပို့ပေးပါ။"
        )
        keyboard = [
            [InlineKeyboardButton("📩 Admin ကိုဆက်သွယ်ရန်", url="https://t.me/UzawgyiGoll")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            photo_path = os.path.join('images', 'wavepay.png')
            with open(photo_path, 'rb') as photo:
                await query.message.reply_photo(
                    photo=photo,
                    caption=caption,
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
            await query.delete_message()
        except FileNotFoundError:
            await query.edit_message_text(
                caption + "\n\n⚠️ WavePay Logo ကို ရှာမတွေ့ပါ။",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )

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
        text += f"🇹🇭 {res['thai']}\n"
    if pkg in ["laos", "both"] or uid == ADMIN_ID:
        text += f"🇱🇦 {res['laos']}"
    await update.message.reply_text(text)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addpremium", add_premium))
    app.add_handler(CommandHandler("removepremium", remove_premium))
    app.add_handler(CommandHandler("addhistory", add_history))
    app.add_handler(CommandHandler("setresult", set_result))
    app.add_handler(CommandHandler("search", search_history))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("Bot is starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
