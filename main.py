from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3

# Create database connection
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Create tables if they don't exist
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                    chat_id INTEGER PRIMARY KEY,
                    name TEXT)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS licenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    license_key TEXT,
                    status TEXT,
                    purchase_id INTEGER)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS purchases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER,
                    license_key TEXT,
                    status TEXT,
                    purchase_id INTEGER)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS config_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id TEXT,
                    file_name TEXT)''')

try:
    cursor.execute('ALTER TABLE purchases ADD COLUMN purchase_id INTEGER')
except sqlite3.OperationalError:
    pass

try:
    cursor.execute('ALTER TABLE licenses ADD COLUMN purchase_id INTEGER')
except sqlite3.OperationalError:
    pass

conn.commit()

# Bot token and admin list
API_ID = 29365133
API_HASH = "722d0eb612a789286c0ed9966c473ddf"
BOT_TOKEN = "6792619764:AAGmD9A8f1AQ_neJoJmQwdq_FAFwfcz8ZHk"
ADMIN_IDS = [1734062356, 799574527]  # List of admin Telegram numeric IDs

# Initialize Client
app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Dictionary to store user states
user_states = {}

# Function to send message to admin
async def send_admin_message(admin_id, message_text, reply_markup=None):
    await app.send_message(admin_id, message_text, reply_markup=reply_markup)

# Command handlers
@app.on_message(filters.command("start"))
async def start(client, message):
    chat_id = message.chat.id
    name = message.from_user.first_name

    # Register user
    cursor.execute(
        "INSERT OR IGNORE INTO users (chat_id, name) VALUES (?, ?)", (chat_id, name))
    conn.commit()

    # Send welcome message
    if chat_id in ADMIN_IDS:
        await message.reply_text("سلام ستونم به ربات مدیریت کانفیگ خوش آمدید.",
                                 reply_markup=InlineKeyboardMarkup([
                                     [InlineKeyboardButton(
                                         "لیست کانفیگ‌ها", callback_data="list_configs")],
                                     [InlineKeyboardButton(
                                         "کانفیگ‌های فروش رفته", callback_data="sold_configs")],
                                     [InlineKeyboardButton(
                                         "کاربران در انتظار تایید", callback_data="pending_users")],
                                     [InlineKeyboardButton(
                                         "اضافه کردن کانفیگ", callback_data="add_config")],
                                     [InlineKeyboardButton(
                                         "مدیریت فایل‌های کانفیگ", callback_data="manage_configs")]
                                 ]))
    else:
        await message.reply_text("سلام به ربات کانفیگ خوش اومدی:)",
                                 reply_markup=InlineKeyboardMarkup([
                                     [InlineKeyboardButton(
                                         "خرید کانفیگ", callback_data="shop")],
                                     [InlineKeyboardButton(
                                         "مشاهده لیست کانفیگ‌های من", callback_data="my_configs")],
                                     [InlineKeyboardButton(
                                         "دانلود فایل‌های کانفیگ", callback_data="download_configs")]
                                 ]))

@app.on_message(filters.command("admin"))
async def admin_login(client, message):
    chat_id = message.chat.id

    if chat_id in ADMIN_IDS:
        user_states[chat_id] = "admin_logged_in"
        await message.reply_text("با موفقیت وارد شدید✅",
                                 reply_markup=InlineKeyboardMarkup([
                                     [InlineKeyboardButton(
                                         "لیست کانفیگ‌ها", callback_data="list_configs")],
                                     [InlineKeyboardButton(
                                         "کانفیگ‌های فروش رفته", callback_data="sold_configs")],
                                     [InlineKeyboardButton(
                                         "کاربران در انتظار تایید", callback_data="pending_users")],
                                     [InlineKeyboardButton(
                                         "اضافه کردن کانفیگ", callback_data="add_config")],
                                     [InlineKeyboardButton(
                                         "مدیریت فایل‌های کانفیگ", callback_data="manage_configs")]
                                 ]))
    else:
        await message.reply_text("شما ادمین نیستید ⛔")

@app.on_message(filters.command("addlicenses") & filters.private)
async def add_licenses(client, message):
    chat_id = message.chat.id

    if user_states.get(chat_id) == "admin_logged_in":
        user_states[chat_id] = "adding_licenses"
        await message.reply_text("لطفا لیست کانفیگ‌ها را ارسال کنید. هر کانفیگ در یک خط باشد:")
    else:
        await message.reply_text("شما دسترسی ادمین ندارید ⛔")

@app.on_message(filters.command("getlicenses") & filters.private)
async def get_licenses(client, message):
    chat_id = message.chat.id

    if user_states.get(chat_id) == "admin_logged_in":
        cursor.execute("SELECT license_key, status FROM licenses")
        licenses = cursor.fetchall()

        if licenses:
            response = "لیست کانفیگ‌ها:\n"
            for license in licenses:
                response += f"کانفیگ: {license[0]} - وضعیت: {license[1]}\n"
            await message.reply_text(response)
        else:
            await message.reply_text("هیچ کانفیگی وجود ندارد.")
    else:
        await message.reply_text("شما دسترسی ادمین ندارید ⛔")

@app.on_message(filters.text & filters.private)
async def handle_text(client, message):
    chat_id = message.chat.id
    text = message.text

    if user_states.get(chat_id) == "admin_logged_in":
        cursor.execute(
            "INSERT INTO licenses (license_key, status, purchase_id) VALUES (?, 'set', NULL)", (text,))
        conn.commit()
        await message.reply_text("کانفیگ جدید اضافه شد➕✅")

    elif user_states.get(chat_id) == "adding_licenses":
        licenses = text.split('\n')
        for license_key in licenses:
            cursor.execute(
                "INSERT INTO licenses (license_key, status, purchase_id) VALUES (?, 'set', NULL)", (license_key,))
        conn.commit()
        user_states[chat_id] = "admin_logged_in"
        await message.reply_text("کانفیگ‌های جدید اضافه شدند➕✅")

@app.on_message(filters.photo & filters.private)
async def handle_photo(client, message):
    chat_id = message.chat.id

    if user_states.get(chat_id) in ["waiting_for_payment_proof", "resend_payment_proof"]:
        user_states[chat_id] = "awaiting_admin_approval"
        file_id = message.photo.file_id
        await message.reply_text("عکس تایید پرداخت دریافت شد. منتظر تایید ادمین باشید.")

        for admin_id in ADMIN_IDS:
            await client.send_photo(admin_id, file_id, caption=f"کاربر {chat_id} عکس تایید پرداخت ارسال کرده است. برای تایید، از دستور /approve {chat_id} استفاده کنید.",
                                    reply_markup=InlineKeyboardMarkup([
                                        [InlineKeyboardButton(
                                            "تایید", callback_data=f"approve_{chat_id}")],
                                        [InlineKeyboardButton(
                                            "رد", callback_data=f"reject_{chat_id}")]
                                    ]))

@app.on_callback_query(filters.regex("shop"))
async def shop_callback(client, callback_query):
    chat_id = callback_query.from_user.id
    user_states[chat_id] = "waiting_for_payment_proof"

    await callback_query.message.reply_text(
        "برای خرید کانفیگ مبلغ را به شماره کارت 1234-5678-9876-5432 واریز کنید و عکس تایید پرداخت را ارسال کنید."
    )

@app.on_callback_query(filters.regex("list_configs"))
async def list_configs(client, callback_query):
    await callback_query.answer()
    cursor.execute("SELECT license_key, status FROM licenses")
    licenses = cursor.fetchall()

    if licenses:
        response = "لیست کانفیگ‌ها:\n"
        for license in licenses:
            response += f"کانفیگ: {license[0]} - وضعیت: {license[1]}\n"
        await callback_query.message.reply_text(response)
    else:
        await callback_query.message.reply_text("هیچ کانفیگی وجود ندارد.")

@app.on_callback_query(filters.regex(r"approve_(\d+)"))
async def approve_payment(client, callback_query):
    admin_id = callback_query.from_user.id
    user_chat_id = int(callback_query.data.split('_')[1])

    if admin_id in ADMIN_IDS:
        cursor.execute(
            "SELECT license_key FROM licenses WHERE status = 'set' AND purchase_id IS NULL LIMIT 1")
        license = cursor.fetchone()

        if license:
            license_key = license[0]
            cursor.execute(
                "INSERT INTO purchases (chat_id, license_key, status, purchase_id) VALUES (?, ?, 'active', NULL)", (user_chat_id, license_key))
            cursor.execute(
                "UPDATE licenses SET status = 'sold', purchase_id = last_insert_rowid() WHERE license_key = ?", (license_key,))
            conn.commit()
            await client.send_message(user_chat_id, f"پرداخت شما تایید شد✅. کانفیگ شما: {license_key}")
            await send_admin_message(admin_id, f"پرداخت کاربر {user_chat_id} تایید شد. کانفیگ: {license_key}")
        else:
            await client.send_message(user_chat_id, "پرداخت شما تایید شد اما هیچ کانفیگی موجود نیست. لطفاً با ادمین تماس بگیرید.")
            await send_admin_message(admin_id, f"پرداخت کاربر {user_chat_id} تایید شد اما هیچ کانفیگی موجود نیست.")
        
        await callback_query.message.delete()
    else:
        await callback_query.answer("شما ادمین نیستید ⛔", show_alert=True)

@app.on_callback_query(filters.regex(r"reject_(\d+)"))
async def reject_payment(client, callback_query):
    admin_id = callback_query.from_user.id
    user_chat_id = int(callback_query.data.split('_')[1])

    if admin_id in ADMIN_IDS:
        user_states[user_chat_id] = "resend_payment_proof"
        await send_admin_message(admin_id, f"رد خرید برای کاربر {user_chat_id} انجام شد.")
        await client.send_message(user_chat_id, "خرید شما توسط ادمین رد شد. برای ارسال مجدد عکس تایید پرداخت، لطفاً دوباره عکس را ارسال کنید.",
                                  reply_markup=InlineKeyboardMarkup([
                                      [InlineKeyboardButton(
                                          "ارسال مجدد عکس تایید پرداخت", callback_data="resend_photo")]
                                  ]))
        
        await callback_query.message.delete()
    else:
        await callback_query.answer("شما ادمین نیستید ⛔", show_alert=True)

@app.on_callback_query(filters.regex("resend_photo"))
async def resend_photo(client, callback_query):
    chat_id = callback_query.from_user.id
    user_states[chat_id] = "resend_payment_proof"

    await callback_query.message.reply_text(
        "لطفاً عکس تایید پرداخت را دوباره ارسال کنید."
    )

@app.on_callback_query(filters.regex("my_configs"))
async def my_configs(client, callback_query):
    chat_id = callback_query.from_user.id

    cursor.execute(
        "SELECT license_key FROM purchases WHERE chat_id = ?", (chat_id,))
    purchases = cursor.fetchall()

    if purchases:
        response = "کانفیگ‌های شما:\n"
        for purchase in purchases:
            response += f"- {purchase[0]}\n"
        await callback_query.message.reply_text(response)
    else:
        await callback_query.message.reply_text("شما هیچ کانفیگی خریداری نکرده‌اید.")

@app.on_callback_query(filters.regex("manage_configs"))
async def manage_configs(client, callback_query):
    chat_id = callback_query.from_user.id
    if chat_id in ADMIN_IDS:
        user_states[chat_id] = "managing_configs"
        await callback_query.message.reply_text("شما وارد بخش مدیریت فایل‌های کانفیگ شدید.\نلطفاً یک فایل کانفیگ ارسال کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "مشاهده لیست فایل‌های کانفیگ", callback_data="view_configs")],
                [InlineKeyboardButton(
                    "اضافه کردن فایل کانفیگ", callback_data="add_config_file")]
            ]))
    else:
        await callback_query.answer("شما ادمین نیستید ⛔", show_alert=True)

@app.on_message(filters.document & filters.private)
async def handle_document(client, message):
    chat_id = message.chat.id

    if user_states.get(chat_id) == "managing_configs":
        file_id = message.document.file_id
        file_name = message.document.file_name

        cursor.execute(
            "INSERT INTO config_files (file_id, file_name) VALUES (?, ?)", (file_id, file_name))
        conn.commit()

        await message.reply_text("فایل کانفیگ با موفقیت اضافه شد✅",
                                 reply_markup=InlineKeyboardMarkup([
                                     [InlineKeyboardButton(
                                         "مشاهده لیست فایل‌های کانفیگ", callback_data="view_configs")]
                                 ]))

@app.on_callback_query(filters.regex("view_configs"))
async def view_configs(client, callback_query):
    chat_id = callback_query.from_user.id

    cursor.execute("SELECT id, file_name FROM config_files")
    config_files = cursor.fetchall()

    if config_files:
        buttons = []
        for config_file in config_files:
            buttons.append([InlineKeyboardButton(
                f"{config_file[1]}", callback_data=f"delete_config_{config_file[0]}")])
        
        await callback_query.message.reply_text("لیست فایل‌های کانفیگ:",
                                                reply_markup=InlineKeyboardMarkup(buttons))
    else:
        await callback_query.message.reply_text("هیچ فایل کانفیگی وجود ندارد.")

@app.on_callback_query(filters.regex(r"delete_config_(\d+)"))
async def delete_config(client, callback_query):
    config_id = int(callback_query.data.split('_')[2])
    chat_id = callback_query.from_user.id

    if chat_id in ADMIN_IDS:
        cursor.execute("DELETE FROM config_files WHERE id = ?", (config_id,))
        conn.commit()
        await callback_query.message.reply_text("فایل کانفیگ با موفقیت حذف شد❌")
    else:
        await callback_query.answer("شما ادمین نیستید ⛔", show_alert=True)

@app.on_callback_query(filters.regex("download_configs"))
async def download_configs(client, callback_query):
    chat_id = callback_query.from_user.id

    cursor.execute("SELECT file_id, file_name FROM config_files")
    config_files = cursor.fetchall()

    if config_files:
        for config_file in config_files:
            await client.send_document(chat_id, config_file[0], caption=config_file[1])
    else:
        await callback_query.message.reply_text("هیچ فایل کانفیگی برای دانلود موجود نیست.")

# Run bot
app.run()