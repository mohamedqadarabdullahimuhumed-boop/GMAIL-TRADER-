import logging
import sqlite3
import random
import string
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    filters
)

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- CONFIGURATION (MACLUUMAADKAAGA) ---
ADMIN_ID = 5926168191  # Telegram ID-gaaga Admin-ka
BOT_TOKEN = "8862676649:AAGiTiAuVaIbClEX9rCr8qCaEiQMISPb7Ww"  # Bot Token-kaaga
ACC_PRICE = 0.20     # Lacagta ku dharaysa user-ka marka akoonka la aqbalo ($0.20)
MIN_WITHDRAWAL = 0.5 # Lacagta ugu yar ee la bixi karo ($0.5)

# States
WAITING_EVC_NUMBER, CONFIRM_EVC_NUMBER = range(2)

# --- DYNAMIC GENERATOR ---
FIRST_NAMES = [
    "Josiah", "Liam", "Noah", "Oliver", "Elijah", "James", "William", "Benjamin",
    "Lucas", "Henry", "Alexander", "Mason", "Michael", "Ethan", "Daniel", "Jacob"
]
DOMAINS = ["sohaggg.site", "mailtemp.org", "verifycode.net", "getsecmail.com"]

def generate_random_string(length=12):
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(length))

def generate_random_password(length=12):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

def generate_gmail_details():
    first_name = random.choice(FIRST_NAMES)
    gmail_address = f"{generate_random_string(16)}@gmail.com"
    password = generate_random_password(12)
    recovery_email = f"{generate_random_string(8)}@{random.choice(DOMAINS)}"
    return first_name, gmail_address, password, recovery_email

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('gmail_trader.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance REAL DEFAULT 0.0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gmails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            email TEXT,
            status TEXT DEFAULT 'pending'
        )
    ''')
    conn.commit()
    conn.close()

def get_user_data(user_id):
    conn = sqlite3.connect('gmail_trader.db')
    cursor = conn.cursor()
    cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    if not row:
        cursor.execute('INSERT INTO users (user_id, balance) VALUES (?, 0.0)', (user_id,))
        conn.commit()
        balance = 0.0
    else:
        balance = row[0]
    
    cursor.execute("SELECT email FROM gmails WHERE user_id = ? AND status = 'approved'", (user_id,))
    gmails = [r[0] for r in cursor.fetchall()]
    conn.close()
    return balance, gmails

def add_balance(user_id, amount):
    conn = sqlite3.connect('gmail_trader.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, user_id))
    conn.commit()
    conn.close()

def deduct_balance(user_id, amount):
    conn = sqlite3.connect('gmail_trader.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET balance = balance - ? WHERE user_id = ?', (amount, user_id))
    conn.commit()
    conn.close()

# --- KEYBOARD ---
def main_keyboard():
    keyboard = [
        [KeyboardButton("1 ➕️ Samee Gmail Cusub")],
        [KeyboardButton("2 📁 Akoonnadayda"), KeyboardButton("3 💰 Haraaga")],
        [KeyboardButton("4 💳 Lacag La Bixid"), KeyboardButton("5 💬 Caawimaad")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# --- START COMMAND ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    get_user_data(user_id)
    msg = (
        "👋 KU SOO DHAWOOW GMAIL TRADER 📧\n"
        "Gmail samey oo hel lacag. 💸"
    )
    await update.message.reply_text(msg, reply_markup=main_keyboard())

# --- MESSAGE HANDLER ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    balance, gmails = get_user_data(user_id)

    if text == "1 ➕️ Samee Gmail Cusub":
        first_name, gmail_addr, password, recovery_email = generate_gmail_details()
        
        context.user_data['pending_details'] = {
            'first_name': first_name,
            'email': gmail_addr,
            'password': password,
            'recovery': recovery_email
        }

        msg = (
            "📝 Diiwaangeli akoon Gmail adoo isticmaalaya macluumaadka la cayimay.\n\n"
            f"👤 Magaca Hore: {first_name}\n"
            "👤 Magaca Dambe: ✖️\n"
            f"📧 Email: {gmail_addr}\n"
            f"🔑 Furaha Sirta ah: {password}\n"
            f"🛡 Emailka Soo Celinta: {recovery_email}\n\n"
            "⚠️ Hubi inaad isticmaasho macluumaadka saxda ah ee la cayimay."
        )
        inline_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅️ Gmail-ka waa la abuuray", callback_data="gmail_success")],
            [InlineKeyboardButton("❌️ Gmail-ka ma maamulin", callback_data="gmail_failed")]
        ])
        await update.message.reply_text(msg, reply_markup=inline_keyboard)

    elif text == "2 📁 Akoonnadayda":
        if not gmails:
            msg = "Faahfaahin ku saabsan akoonnada la aqbalay. 📧\n\nWeli wax akoon ah oo la oggolaaday ma jiraan."
        else:
            list_text = "\n".join([f"{idx+1} {email}" for idx, email in enumerate(gmails)])
            msg = f"Faahfaahin ku saabsan akoonnada la sameeyay. 📧\n\n{list_text}"
        await update.message.reply_text(msg)

    elif text == "3 💰 Haraaga":
        msg = (
            "💰 Soo Koobiddaada Maaliyadeed\n\n"
            f"💵 Haraaga La Heli Karo: ${balance:.2f}\n\n"
            "ℹ️ Waqtiga Haynta ≈ 3 maalmood.\n"
            "Haraaga waxaa lagu dari doonaa akoonkaaga marka akoonka la aqbalo."
        )
        await update.message.reply_text(msg)

    elif text == "4 💳 Lacag La Bixid":
        msg = (
            f"Haraagaagu waa ${balance:.2f}\n\n"
            "lacag-bixin maxalli ah. 📶\n"
            "🟢 EVC-PLUS\n"
            "🟡 eDahab\n\n"
            f"Haraaga lacagta ugu yar ee laga bixi karo waa ${MIN_WITHDRAWAL:.1f}"
        )
        inline_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🟢 EVC-PLUS", callback_data="pay_evc")],
            [InlineKeyboardButton("🟡 eDahab", callback_data="pay_edahab")]
        ])
        await update.message.reply_text(msg, reply_markup=inline_keyboard)

    elif text == "5 💬 Caawimaad":
        msg = (
            "Hadii cabasho jirto waxaad naga la soo xiriiri kartaa. 💬\n\n"
            "👤: Qadarinho16\n"
            "☎️ : 0610687458"
        )
        await update.message.reply_text(msg)

# --- INLINE CALLBACK HANDLER ---
async def inline_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user = query.from_user

    if data == "gmail_success":
        details = context.user_data.get('pending_details')
        if details:
            conn = sqlite3.connect('gmail_trader.db')
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO gmails (user_id, email, status) VALUES (?, ?, ?)',
                (user.id, details['email'], 'pending')
            )
            db_id = cursor.lastrowid
            conn.commit()
            conn.close()

            msg = "⏳️: Waxaan hubin doonnaa macluumaadka maamulka. 🔎👤\nFadlan tirtir gmail-ka. 📧🗑"
            await query.message.reply_text(msg)

            admin_msg = (
                "📥 **GMAIL CUSUB OOY TAHAY IN LA HUBIYO**\n\n"
                f"👤 **User:** {user.first_name} (@{user.username or 'NoUsername'})\n"
                f"🆔 **User ID:** `{user.id}`\n\n"
                f"📧 **Email:** `{details['email']}`\n"
                f"🔑 **Password:** `{details['password']}`\n"
                f"🛡 **Recovery:** `{details['recovery']}`"
            )
            admin_buttons = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(f"✅ Aqbal (${ACC_PRICE:.2f})", callback_data=f"adm_app_{db_id}_{user.id}"),
                    InlineKeyboardButton("❌ Diid", callback_data=f"adm_rej_{db_id}_{user.id}")
                ]
            ])
            try:
                await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg, reply_markup=admin_buttons, parse_mode="Markdown")
            except Exception as e:
                logging.error(f"Error ka dhacay marka admin loo dirayay: {e}")

            context.user_data['pending_details'] = None

    elif data == "gmail_failed":
        await query.message.reply_text("Fadlan marka hore samee gmail-ka. 📧❗️")

    # --- ADMIN ACTIONS ---
    elif data.startswith("adm_app_"):
        _, _, db_id, target_user_id = data.split("_")
        target_user_id = int(target_user_id)
        
        conn = sqlite3.connect('gmail_trader.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE gmails SET status = 'approved' WHERE id = ?", (db_id,))
        conn.commit()
        conn.close()

        # U kordhi $0.20 haraaga user-ka
        add_balance(target_user_id, ACC_PRICE)

        await query.edit_message_text(f"{query.message.text}\n\n✅ **AQA BALAY:** Haraaga ${ACC_PRICE:.2f} waa loo kordhiyay user-ka.")
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"🎉 **Akoonkii aad sameysay waa la aqbalay!**\n💰 Waxaa akoonkaaga lagu daray ${ACC_PRICE:.2f}."
            )
        except Exception:
            pass

    elif data.startswith("adm_rej_"):
        _, _, db_id, target_user_id = data.split("_")
        target_user_id = int(target_user_id)

        conn = sqlite3.connect('gmail_trader.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE gmails SET status = 'rejected' WHERE id = ?", (db_id,))
        conn.commit()
        conn.close()

        await query.edit_message_text(f"{query.message.text}\n\n❌ **WAA LA DIIDAY.**")
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text="❌ Akoonkii aad sameysay waa la diiday sababtoo ah macluumaadku sax ma ahayn."
            )
        except Exception:
            pass

# --- CONVERSATION FOR PAYMENT ---
async def start_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    context.user_data['payment_method'] = "EVC-PLUS" if query.data == "pay_evc" else "eDahab"
    await query.message.reply_text("Fadlan geli numberka.")
    return WAITING_EVC_NUMBER

async def receive_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    number = update.message.text
    context.user_data['phone_number'] = number
    
    inline_keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Haa 👍", callback_data="confirm_yes"),
            InlineKeyboardButton("Maya 👎", callback_data="confirm_no")
        ]
    ])
    await update.message.reply_text(f"Ma hubtaa in numberku yahay: {number}?", reply_markup=inline_keyboard)
    return CONFIRM_EVC_NUMBER

async def confirm_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = update.effective_user.id
    balance, _ = get_user_data(user_id)

    if data == "confirm_yes":
        # HUBINTA HARAAGA: ma ku filan yahay $0.5 ama ka badan?
        if balance >= MIN_WITHDRAWAL:
            # 1. Ka jar haraaga user-ka
            deduct_balance(user_id, balance)

            # 2. U dir fariin guul ah User-ka
            msg = (
                "✅️ Waad ku guuleysatay inaa kala baxdo lacagta. 💸\n"
                "Waxaa lacagta ku soo diri doono maamulka. 👤 👍"
            )
            await query.message.reply_text(msg)

            # 3. U DIR ADIGA (ADMIN-KA) NAMBARKA SI AAD LACAGTA UGU DIRTO
            phone = context.user_data.get('phone_number')
            method = context.user_data.get('payment_method', 'EVC-PLUS')
            user_name = query.from_user.first_name
            username = query.from_user.username or "NoUsername"

            admin_alert = (
                "🚨 **CODSIGII LACAG BIXINTA (WITHDRAWAL)** 🚨\n\n"
                f"👤 **User:** {user_name} (@{username})\n"
                f"🆔 **User ID:** `{user_id}`\n"
                f"📱 **Nambarka:** `{phone}`\n"
                f"📲 **Bixinta:** {method}\n"
                f"💵 **Lacagta Lagu Dirayo:** ${balance:.2f}"
            )
            try:
                await context.bot.send_message(chat_id=ADMIN_ID, text=admin_alert, parse_mode="Markdown")
            except Exception as e:
                logging.error(f"Admin-ka lacag bixinta waa loo diri waayay: {e}")

        else:
            # DHIBAATO: Haraaga ka yar $0.5 -> ADMIN-KA WAXBA LOO DIRIN MAHYO
            msg = "Fadlan Haraaga Muku Filna!"
            await query.message.reply_text(msg)
    else:
        await query.message.reply_text("Kala baxa lacagta waa la joojiyay.")

    return ConversationHandler.END

async def cancel_conv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hawshii waa la meel-dhabay.")
    return ConversationHandler.END

# --- MAIN BOT RUNNER ---
def main():
    init_db()
    
    app = Application.builder().token(BOT_TOKEN).build()

    payment_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_payment, pattern="^(pay_evc|pay_edahab)$")
        ],
        states={
            WAITING_EVC_NUMBER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_number)
            ],
            CONFIRM_EVC_NUMBER: [
                CallbackQueryHandler(confirm_payment, pattern="^(confirm_yes|confirm_no)$")
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel_conv)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(payment_conv)
    app.add_handler(CallbackQueryHandler(inline_button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot-ku waa shaqaynayaa...")
    app.run_polling()

if __name__ == "__main__":
    main()
