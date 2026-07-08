import telebot
import os

# GitHub-এ কোড পুশ করার জন্য এটি নিরাপদ। 
# টোকেনটি সরাসরি এখানে না লিখে আমরা এনভায়রনমেন্ট ভেরিয়েবল থেকে রিড করব।
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 6632496253 

if not BOT_TOKEN:
    raise ValueError("Error: BOT_TOKEN variable missing from environment settings!")

bot = telebot.TeleBot(BOT_TOKEN)
DB_FILE = "users.txt"

def save_user_mapping(message_id, chat_id):
    """Saves which message ID belongs to which user chat so admin replies work flawlessly"""
    with open(DB_FILE, "a") as f:
        f.write(f"{message_id}:{chat_id}\n")

def get_user_chat_id(reply_to_message_id):
    """Retrieves the customer's chat ID using the replied message ID"""
    if not os.path.exists(DB_FILE):
        return None
    with open(DB_FILE, "r") as f:
        for line in f:
            if line.strip():
                msg_id, chat_id = line.strip().split(":")
                if int(msg_id) == reply_to_message_id:
                    return int(chat_id)
    return None

# Welcome message for users
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if message.chat.id == ADMIN_ID:
        bot.reply_to(message, "⚡ **Xtreme Support Admin Panel Active**\n\nWhen users message this bot, their texts will forward here. Simply use Telegram's **'Reply'** function on their forwarded message to talk back to them.")
    else:
        welcome_text = (
            "👋 **Welcome to Xtreme Support Bot!**\n\n"
            "We specialize in professional digital solutions:\n"
            "🛠️ **Facebook Account Recovery**\n"
            "🚫 **Fake / Imposter Account Takedown**\n\n"
            "Please describe your problem in detail or send relevant screenshots. Our support agent will reply to you directly inside this chat shortly!"
        )
        bot.reply_to(message, welcome_text)

# Handle incoming support messages and admin replies
@bot.message_handler(func=lambda message: True, content_types=['text', 'photo', 'document', 'voice'])
def handle_all_messages(message):
    # 1. CLIENT TO ADMIN
    if message.chat.id != ADMIN_ID:
        user_info = (
            f"📩 **New Support Ticket**\n"
            f"👤 **Name:** {message.from_user.first_name}\n"
            f"🆔 **User ID:** `{message.chat.id}`\n"
            f"🔗 **Username:** @{message.from_user.username if message.from_user.username else 'None'}\n"
            f"━━━━━━━━━━━━━━━━━━"
        )
        bot.send_message(ADMIN_ID, user_info, parse_mode="Markdown")
        
        forwarded = bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
        save_user_mapping(forwarded.message_id, message.chat.id)
        
    # 2. ADMIN TO CLIENT
    else:
        if message.reply_to_message:
            target_user_id = get_user_chat_id(message.reply_to_message.message_id)
            
            if target_user_id:
                try:
                    if message.content_type == 'text':
                        bot.send_message(target_user_id, message.text)
                    elif message.content_type == 'photo':
                        bot.send_photo(target_user_id, message.photo[-1].file_id, caption=message.caption)
                    elif message.content_type == 'document':
                        bot.send_document(target_user_id, message.document.file_id, caption=message.caption)
                    elif message.content_type == 'voice':
                        bot.send_voice(target_user_id, message.voice.file_id)
                    
                    bot.send_message(ADMIN_ID, "✅ *Message delivered to client.*", parse_mode="Markdown")
                except Exception as e:
                    bot.send_message(ADMIN_ID, f"❌ *Delivery failed.* User may have blocked the bot.\n`Error: {e}`", parse_mode="Markdown")
            else:
                bot.send_message(ADMIN_ID, "⚠️ *Error:* Could not map this message to a client ID. Make sure you are replying directly to the forwarded box.")
        else:
            bot.send_message(ADMIN_ID, "💡 *Tip:* To talk to a client, you must right-click/long-press their forwarded message and select **Reply**.")

print("Bot is processing updates live...")
bot.infinity_polling()
