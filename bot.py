import subprocess
import os
import glob
from threading import Thread
from flask import Flask
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# ????? ??? Web ??????? ????? ?-Render ???? ???? ????
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "DarkUser Bot is alive and running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host='0.0.0.0', port=port)

# ????? ?? ???? ?-BotFather
TOKEN = "9174255279:AAGccYt95PTy01rH8v140AgNIqcA6BJ2TZA"

# ????? ???? ?????? ?? ?????? ??? ?'??
user_search_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "?? Hi, welcome to DarkUser! Send me a username and let's begin the investigation:"
    )

async def handle_username_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.text.strip()
    chat_id = update.effective_chat.id
    
    # ????? ?? ?????? ???? ?????? ??????
    user_search_data[chat_id] = username

    # ????? ?????? ????? ???? ??????
    keyboard = [
        [InlineKeyboardButton("? Normal Scan (Fast)", callback_data="scan_normal")],
        [InlineKeyboardButton("?? Comprehensive Scan (All Sites)", callback_data="scan_full")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"?? You chose to search for: {username}\nWhich scan type would you like to run?",
        reply_markup=reply_markup
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    chat_id = query.message.chat_id
    username = user_search_data.get(chat_id)

    if not username:
        await query.edit_message_text("? Oops, search data expired. Please send the username again.")
        return

    choice = query.data
    if choice == "scan_normal":
        await query.edit_message_text(f"? Running normal scan for {username}...")
        cmd = f"maigret {username} -H"
    elif choice == "scan_full":
        await query.edit_message_text(f"? Running comprehensive scan for {username}...\nThis may take a few minutes, please wait.")
        cmd = f"maigret {username} -H -a"
    else:
        return

    # ???? ????? Maigret
    subprocess.run(cmd, shell=True)

    # ????? ???? ?-HTML ?????
    report_files = glob.glob(f"reports/*{username}*.html")

    if report_files:
        latest_report = report_files[0]
        
        # ????? ???? ???? ???? ?-HTML ????? ??????
        summary_text = f"? Scan completed successfully for: {username}\n\n"
        try:
            with open(latest_report, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
                brief_elem = soup.find('div', class_='brief')
                if brief_elem:
                    summary_text += f"?? Summary: {brief_elem.get_text(strip=True)}\n"
                
                links = soup.find_all('a', href=True)
                found_links = [a['href'] for a in links if 'http' in a['href'] and 'github' not in a['href']][:5]
                if found_links:
                    summary_text += "\n?? Sample of profiles found:\n"
                    for link in found_links:
                        summary_text += f"• {link}\n"
        except Exception:
            summary_text += "Results found, but could not parse the summary text automatically.\n"

        await query.message.reply_text(summary_text)
        
        # ????? ???? ???"? ???? ??????
        with open(latest_report, 'rb') as f:
            await query.message.reply_document(
                document=f, 
                filename=os.path.basename(latest_report),
                caption="?? To download the report in HTML view, click here:"
            )
    else:
        await query.message.reply_text(f"? Scan finished, but no results or report were found for {username}.")

if __name__ == '__main__':
    # ????? ??? ?-Web ???? ???? ???? ??? ???? ?-Render ???? ????
    t = Thread(target=run_web, daemon=True)
    t.start()

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_username_input))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    print("???? ???? ???? ?????? ???????...")
    app.run_polling()