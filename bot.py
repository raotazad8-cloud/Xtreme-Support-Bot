import telebot
import os
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

# Token & Admin configuration
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 6632496253 

if not BOT_TOKEN:
    raise ValueError("Error: BOT_TOKEN variable missing from environment settings!")

bot = telebot.TeleBot(BOT_TOKEN)
DB_FILE = "users.txt"

# 🛠️ Dummy Server Setup for Render Free Web Service
class DummyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Bot is alive and running!")

def run_dummy_server():
    # Render provides a PORT environment variable automatically
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), DummyServer)
    server.serve_forever()

def save_user_mapping(message_id, chat_id):
    with open(DB_FILE, "a") as f:
        f.write(f"{message_id}:{chat_id}\n")

def get_user_chat_id(reply_to_message_id):
    if not os.path.exists(DB_FILE):
        return None
    with open(DB_FILE, "r") as f:
        for line in f:
            if line.strip():
                msg_id, chat_id = line.strip().split(":")
                if int(msg_id) == reply_to_message_id:
                    return int(chat_id)
    return None

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if message.chat.id == ADMIN_ID:
        bot.reply_to(message, "⚡ **Xtreme Support Admin Panel Active**\n\nWhen users message this bot, their texts will forward here. Reply to their messages to chat back.")
    else:
        welcome_text = (
            "👋 **Welcome to Xtreme Support Bot!**\n\n"
            "We specialize in professional digital solutions:\n"
            "🛠️ **Facebook Account Recovery**\n"
            "🚫 **Fake / Imposter Account Takedown**\n\n"
            "Please describe your problem in detail. Our support agent will reply to you shortly!"
        )
        bot.reply_to(message, welcome_text)

@bot.message_handler(func=lambda message: True, content_types=['text', 'photo', 'document', 'voice'])
def handle_all_messages(message):
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
                    bot.send_message(ADMIN_ID, f"❌ *Delivery failed.* \n`Error: {e}`", parse_mode="Markdown")
            else:
                bot.send_message(ADMIN_ID, "⚠️ *Error:* Could not map this message to a client ID.")
        else:
            bot.send_message(ADMIN_ID, "💡 *Tip:* Use **Reply** on a forwarded message to talk to a client.")

print("Starting dummy server and bot...")
# Start the server in a separate background thread so it doesn't block the bot
Thread(target=run_dummy_server, daemon=True).start()

# Start the Telegram Bot
bot.infinity_polling()
