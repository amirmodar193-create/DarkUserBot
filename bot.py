import subprocess
import os
import glob
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# הדבק כאן את הטוקן שקיבלת מ-BotFather
TOKEN = "9174255279:AAGccYt95PTy01rH8v140AgNIqcA6BJ2TZA"

# מילון זמני לשמירת שם המשתמש לכל צ'אט
user_search_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hi, welcome to DarkUser! Send me a username and let's begin the investigation:"
    )

async def handle_username_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.text.strip()
    chat_id = update.effective_chat.id
    
    # שמירת שם המשתמש עבור המשתמש הנוכחי
    user_search_data[chat_id] = username

    # יצירת כפתורי בחירה לסוג הסריקה
    keyboard = [
        [InlineKeyboardButton("⚡ Normal Scan (Fast)", callback_data="scan_normal")],
        [InlineKeyboardButton("🔍 Comprehensive Scan (All Sites)", callback_data="scan_full")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"🎯 You chose to search for: {username}\nWhich scan type would you like to run?",
        reply_markup=reply_markup
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    chat_id = query.message.chat_id
    username = user_search_data.get(chat_id)

    if not username:
        await query.edit_message_text("❌ Oops, search data expired. Please send the username again.")
        return

    choice = query.data
    if choice == "scan_normal":
        await query.edit_message_text(f"⏳ Running normal scan for {username}...")
        cmd = f"maigret {username} -H"
    elif choice == "scan_full":
        await query.edit_message_text(f"⏳ Running comprehensive scan for {username}...\nThis may take a few minutes, please wait.")
        cmd = f"maigret {username} -H -a"
    else:
        return

    # הרצת פקודת Maigret
    subprocess.run(cmd, shell=True)

    # מציאת קובץ ה-HTML שנוצר
    report_files = glob.glob(f"reports/*{username}*.html")

    if report_files:
        latest_report = report_files[0]
        
        # חילוץ מידע מתוך קובץ ה-HTML להצגה בטלגרם (כטקסט נקי ללא Markdown)
        summary_text = f"✅ Scan completed successfully for: {username}\n\n"
        try:
            with open(latest_report, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
                brief_elem = soup.find('div', class_='brief')
                if brief_elem:
                    summary_text += f"📊 Summary: {brief_elem.get_text(strip=True)}\n"
                
                links = soup.find_all('a', href=True)
                found_links = [a['href'] for a in links if 'http' in a['href'] and 'github' not in a['href']][:5]
                if found_links:
                    summary_text += "\n🔗 Sample of profiles found:\n"
                    for link in found_links:
                        summary_text += f"• {link}\n"
        except Exception:
            summary_text += "Results found, but could not parse the summary text automatically.\n"

        await query.message.reply_text(summary_text)
        
        # שליחת קובץ הדו"ח המלא להורדה עם הניסוח החדש באנגלית
        with open(latest_report, 'rb') as f:
            await query.message.reply_document(
                document=f, 
                filename=os.path.basename(latest_report),
                caption="📁 To download the report in HTML view, click here:"
            )
    else:
        await query.message.reply_text(f"❌ Scan finished, but no results or report were found for {username}.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_username_input))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    print("הבוט החכם פעיל וממתין להודעות...")
    app.run_polling()