import os
import sys
from flask import Flask, request
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

# বোট কনফিগারেশন
TOKEN = "7217587502:AAEidV7zPQw3ETExCa15GyNQReXd6iqLu_k"
OWNER_ID = 6632496253

# মেমোরি ডাটাবেজ (সহজ রাখার জন্য)
ADMINS = {OWNER_ID}
OPTIONS = ["Option 1", "Option 2"]  # ডিফল্ট কিছু অপশন

# কনভারসেশন স্টেটসমূহ
CHOOSING_OPTION, GETTING_INFO, ADDING_OPTION, ADDING_ADMIN, DELETING_OPTION = range(5)

app = Flask(__name__)

# বোট অ্যাপ্লিকেশন তৈরি
bot_app = Application.builder().token(TOKEN).build()

# --- হেল্পার ফাংশন ---
def is_admin(user_id):
    return user_id in ADMINS or user_id == OWNER_ID

def get_customer_keyboard():
    if not OPTIONS:
        return ReplyKeyboardMarkup([["No options available"]], resize_keyboard=True)
    # প্রতি লাইনে ২টি করে অপশন বাটন দেখাবে
    keyboard = [OPTIONS[i:i + 2] for i in range(0, len(OPTIONS), 2)]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# --- বোট কমান্ড ও হ্যান্ডলার ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if is_admin(user_id):
        admin_text = (
            "👋 স্বাগতম অ্যাডমিন!\n\n"
            "🛠 **অ্যাডমিন কমান্ডসমূহ:**\n"
            "➕ /addoption - নতুন অপশন তৈরি করুন\n"
            "❌ /deleteoption - অপশন মুছে ফেলুন\n"
            "👤 /addadmin - নতুন অ্যাডমিন যুক্ত করুন\n"
            "🛑 /shutdown - বোট বন্ধ করুন\n\n"
            "গ্রাহকদের ভিউ দেখতে নিচের অপশনগুলো থেকে সিলেক্ট করুন:"
        )
        await update.message.reply_text(admin_text, reply_markup=get_customer_keyboard())
    else:
        await update.message.reply_text(
            "👋 আমাদের বোটে আপনাকে স্বাগতম! নিচে থেকে একটি অপশন সিলেক্ট করুন:",
            reply_markup=get_customer_keyboard()
        )
    return CHOOSING_OPTION

async def handle_option_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected = update.message.text
    
    if selected not in OPTIONS:
        await update.message.reply_text("দয়া করে নিচের বাটন থেকে একটি সঠিক অপশন বেছে নিন।")
        return CHOOSING_OPTION
        
    context.user_data['selected_option'] = selected
    await update.message.reply_text("📝 Add your additional info", reply_markup=ReplyKeyboardRemove())
    return GETTING_INFO

async def handle_additional_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    info = update.message.text
    selected_option = context.user_data.get('selected_option', 'Unknown')
    
    # অনারকে ডাটা পাঠানো
    report = (
        "📥 **নতুন কাস্টমার রেসপন্স!**\n\n"
        f"👤 নাম: {user.full_name}\n"
        f"🆔 ইউজার আইডি: {user.id}\n"
        f"🏷 ইউজারনেম: @{user.username if user.username else 'None'}\n"
        f"📌 সিলেক্টেড অপশন: {selected_option}\n"
        f"💬 অতিরিক্ত তথ্য: {info}"
    )
    
    try:
        await context.bot.send_message(chat_id=OWNER_ID, text=report)
    except Exception as e:
        print(f"Error sending to owner: {e}")

    await update.message.reply_text("✅ আপনার তথ্য সফলভাবে অনারের কাছে পাঠানো হয়েছে! ধন্যবাদ।", reply_markup=get_customer_keyboard())
    return CHOOSING_OPTION

# --- অ্যাডমিন অ্যাকশন সমূহ ---

# ১. অপশন যোগ করা
async def start_add_option(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    await update.message.reply_text("🖋 নতুন অপশনটির নাম লিখুন:")
    return ADDING_OPTION

async def save_option(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_opt = update.message.text
    if new_opt not in OPTIONS:
        OPTIONS.append(new_opt)
    await update.message.reply_text(f"✅ '{new_opt}' অপশনটি সফলভাবে যুক্ত হয়েছে!", reply_markup=get_customer_keyboard())
    return CHOOSING_OPTION

# ২. অপশন মুছে ফেলা
async def start_delete_option(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    if not OPTIONS:
        await update.message.reply_text("মুছে ফেলার মতো কোনো অপশন নেই।")
        return CHOOSING_OPTION
    
    delete_keyboard = [OPTIONS[i:i + 2] for i in range(0, len(OPTIONS), 2)]
    await update.message.reply_text(
        "❌ আপনি কোন অপশনটি মুছে ফেলতে চান? নিচে থেকে সিলেক্ট করুন:",
        reply_markup=ReplyKeyboardMarkup(delete_keyboard, resize_keyboard=True)
    )
    return DELETING_OPTION

async def remove_option(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target_opt = update.message.text
    if target_opt in OPTIONS:
        OPTIONS.remove(target_opt)
        await update.message.reply_text(f"✅ '{target_opt}' অপশনটি মুছে ফেলা হয়েছে।", reply_markup=get_customer_keyboard())
    else:
        await update.message.reply_text("ভুল অপশন। আবার চেষ্টা করুন বা /start লিখুন।", reply_markup=get_customer_keyboard())
    return CHOOSING_OPTION

# ৩. অ্যাডমিন যোগ করা
async def start_add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    await update.message.reply_text("👤 নতুন অ্যাডমিনের Telegram User ID টি লিখুন:")
    return ADDING_ADMIN

async def save_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        new_admin_id = int(update.message.text)
        ADMINS.add(new_admin_id)
        await update.message.reply_text(f"✅ ইউজার আইডি {new_admin_id} সফলভাবে অ্যাডমিন হিসেবে যুক্ত হয়েছে।", reply_markup=get_customer_keyboard())
    except ValueError:
        await update.message.reply_text("❌ ভুল আইডি। দয়া করে শুধুমাত্র সংখ্যায় আইডিটি লিখুন।")
    return CHOOSING_OPTION

# ৪. শাটডাউন
async def shutdown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text("🛑 বোটটি বন্ধ করা হচ্ছে... (Process Exiting)")
    sys.exit(0)

# কনভারসেশন মেইন সেটআপ
conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        CHOOSING_OPTION: [
            CommandHandler("addoption", start_add_option),
            CommandHandler("deleteoption", start_delete_option),
            CommandHandler("addadmin", start_add_admin),
            CommandHandler("shutdown", shutdown),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_option_selection)
        ],
        GETTING_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_additional_info)],
        ADDING_OPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_option)],
        DELETING_OPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, remove_option)],
        ADDING_ADMIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_admin)],
    },
    fallbacks=[CommandHandler("start", start)],
)

bot_app.add_handler(conv_handler)

# --- Vercel Webhook রুট ---
@app.route("/", methods=["POST"])
def telegram_webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot_app.bot)
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(bot_app.process_update(update))
        return "OK", 200
    return "Invalid Request"

# আপডেট করা ডাইনামিক সেট-ওয়েবহুক রুট (Method error সমাধান করা হয়েছে)
@app.route("/setwebhook", methods=["GET", "POST"])
def set_webhook():
    import asyncio
    # রিকোয়েস্ট হোস্ট থেকে ডাইনামিকালি URL তৈরি করা হচ্ছে, তাই হাত দিয়ে লেখার ঝামেলা নেই
    url = f"https://{request.host}/"
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    success = loop.run_until_complete(bot_app.bot.set_webhook(url=url))
    if success:
        return f"Webhook successfully set to {url}", 200
    return "Webhook setup failed", 500
