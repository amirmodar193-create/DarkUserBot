import os
import threading
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

# ???? ??? ?? ????? ?? ???? ??? ???? ???????
BOT_TOKEN = "9174255279:AAGccYt95PTy01rH8v140AgNIqcA6BJ2TZA"

# ??? HTTP ??????? ??? ?-Render ?? ????? ????? Timeout ?? ??????
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    print(f"Dummy web server running on port {port}")
    server.serve_forever()

def run_maigret_in_thread(username: str, cmd: str, update: Update):
    try:
        # ???? ????? maigret ?? ??????? ????
        process = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        print(f"Maigret finished for {username}")
    except Exception as e:
        print(f"Error running maigret: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "????! ??? ?? ?? ????? (Username) ????? ???? ?????? ????????:"
    )

async def handle_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.text.strip()
    context.user_data["target_username"] = username

    keyboard = [
        [InlineKeyboardButton("????? ????? (Normal)", callback_data="scan_normal")],
        [InlineKeyboardButton("????? ????? (Full + All)", callback_data="scan_full")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"???? ?? ?????: <b>{username}</b>\n??? ?? ??? ?????? ????? ?????:",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    username = context.user_data.get("target_username", "unknown")
    choice = query.data

    if choice == "scan_normal":
        await query.edit_message_text(f"Running normal scan for {username} with cookies...")
        cmd = f"maigret {username} -H --cookie cookies.txt"
    elif choice == "scan_full":
        await query.edit_message_text(f"Running comprehensive scan for {username} with cookies...\nThis may take a few minutes.")
        cmd = f"maigret {username} -H -a --cookie cookies.txt"
    else:
        return

    thread = threading.Thread(target=run_maigret_in_thread, args=(username, cmd, update))
    thread.start()

def main():
    # ????? ??? ?-Web ?-Thread ???? ??? ????? ?? ????? ?-Render ????
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()

    # ????? ?????? ??? ??????
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_username))

    print("Telegram bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()