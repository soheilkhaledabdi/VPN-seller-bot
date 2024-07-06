from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
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
                    status TEXT)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS purchases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER,
                    license_key TEXT,
                    status TEXT)''')

conn.commit()

# Bot token and admin list
API_ID = 29365133
API_HASH = "722d0eb612a789286c0ed9966c473ddf"
BOT_TOKEN = "6792619764:AAGmD9A8f1AQ_neJoJmQwdq_FAFwfcz8ZHk"
ADMIN_IDS = [1734062356,799574527]  # List of admin Telegram numeric IDs

# Initialize Client
app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Dictionary to store user states
user_states = {}


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
                                         "اضافه کردن کانفیگ", callback_data="add_config")]
                                 ]))
    else:
        await message.reply_text("سلام به ربات کانفیگ خوش اومدی:)",
                                 reply_markup=InlineKeyboardMarkup([
                                     [InlineKeyboardButton(
                                         "خرید کانفیگ", callback_data="shop")],
                                     [InlineKeyboardButton(
                                         "مشاهده لیست کانفیگ‌های من", callback_data="my_configs")]
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
                                         "اضافه کردن کانفیگ", callback_data="add_config")]
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
            "INSERT INTO licenses (license_key, status) VALUES (?, 'set')", (text,))
        conn.commit()
        await message.reply_text("کانفیگ جدید اضافه شد➕✅")

    elif user_states.get(chat_id) == "adding_licenses":
        licenses = text.split('\n')
        for license_key in licenses:
            cursor.execute(
                "INSERT INTO licenses (license_key, status) VALUES (?, 'set')", (license_key,))
        conn.commit()
        user_states[chat_id] = "admin_logged_in"
        await message.reply_text("کانفیگ‌های جدید اضافه شدند➕✅")


@app.on_message(filters.photo & filters.private)
async def handle_photo(client, message):
    chat_id = message.chat.id

    if user_states.get(chat_id) == "waiting_for_payment_proof":
        user_states[chat_id] = "awaiting_admin_approval"
        file_id = message.photo.file_id
        await message.reply_text("عکس تایید پرداخت دریافت شد. منتظر تایید ادمین باشید.")

        # Inform admins
        for admin_id in ADMIN_IDS:
            await client.send_message(admin_id, f"کاربر {chat_id} عکس تایید پرداخت ارسال کرده است. برای تایید، از دستور /approve {chat_id} استفاده کنید.", reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "تایید", callback_data=f"approve_{chat_id}")]
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
    chat_id = callback_query.from_user.id

    if chat_id in ADMIN_IDS:
        cursor.execute("SELECT license_key, status FROM licenses")
        licenses = cursor.fetchall()

        if licenses:
            response = "لیست کانفیگ‌ها:\n"
            for license in licenses:
                response += f"کانفیگ: {license[0]} - وضعیت: {license[1]}\n"
            await callback_query.message.reply_text(response)
        else:
            await callback_query.message.reply_text("هیچ کانفیگی وجود ندارد.")
    else:
        await callback_query.message.reply_text("شما دسترسی ادمین ندارید ⛔")


@app.on_callback_query(filters.regex("sold_configs"))
async def sold_configs(client, callback_query):
    chat_id = callback_query.from_user.id

    if chat_id in ADMIN_IDS:
        cursor.execute("SELECT license_key FROM licenses WHERE status = 'use'")
        sold_licenses = cursor.fetchall()

        if sold_licenses:
            response = "کانفیگ‌های فروش رفته:\n"
            for license in sold_licenses:
                response += f"کانفیگ: {license[0]}\n"
            await callback_query.message.reply_text(response)
        else:
            await callback_query.message.reply_text("هیچ کانفیگی فروش نرفته است.")
    else:
        await callback_query.message.reply_text("شما دسترسی ادمین ندارید ⛔")


@app.on_callback_query(filters.regex("pending_users"))
async def pending_users(client, callback_query):
    chat_id = callback_query.from_user.id

    if chat_id in ADMIN_IDS:
        cursor.execute(
            "SELECT chat_id, license_key FROM purchases WHERE status = 'pending'")
        pending_purchases = cursor.fetchall()

        if pending_purchases:
            response = "کاربران در انتظار تایید:\n"
            for purchase in pending_purchases:
                response += f"کاربر: {purchase[0]} - کانفیگ: {purchase[1]}\n"
            await callback_query.message.reply_text(response)
        else:
            await callback_query.message.reply_text("هیچ کاربری در انتظار تایید نیست.")
    else:
        await callback_query.message.reply_text("شما دسترسی ادمین ندارید ⛔")


@app.on_callback_query(filters.regex("add_config"))
async def add_config(client, callback_query):
    chat_id = callback_query.from_user.id

    if chat_id in ADMIN_IDS:
        user_states[chat_id] = "adding_licenses"
        await callback_query.message.reply_text("لطفا لیست کانفیگ‌ها را ارسال کنید. هر کانفیگ در یک خط باشد:")
    else:
        await callback_query.message.reply_text("شما دسترسی ادمین ندارید ⛔")


@app.on_callback_query(filters.regex(r"approve_(\d+)"))
async def approve_purchase(client, callback_query):
    admin_id = callback_query.from_user.id
    user_chat_id = int(callback_query.data.split('_')[1])

    if admin_id in ADMIN_IDS:
        cursor.execute(
            "SELECT license_key FROM purchases WHERE chat_id = ? AND status = 'pending'", (user_chat_id,))
        purchase = cursor.fetchone()

        if purchase:
            license_key = purchase[0]
            cursor.execute(
                "UPDATE licenses SET status = 'use' WHERE license_key = ?", (license_key,))
            cursor.execute(
                "UPDATE purchases SET status = 'approved' WHERE chat_id = ? AND license_key = ?", (user_chat_id, license_key))
            conn.commit()

            await client.send_message(user_chat_id, f"خرید شما تایید شد و کانفیگ به شما اختصاص داده شد: {license_key}")
            await callback_query.message.reply_text("خرید تایید شد و کانفیگ به کاربر اختصاص داده شد.")
        else:
            await callback_query.message.reply_text("خریدی برای تایید پیدا نشد.")
    else:
        await callback_query.message.reply_text("شما دسترسی ادمین ندارید ⛔")


@app.on_callback_query(filters.regex("my_configs"))
async def my_configs(client, callback_query):
    chat_id = callback_query.from_user.id

    cursor.execute(
        "SELECT license_key FROM purchases WHERE chat_id = ? AND status = 'approved'", (chat_id,))
    configs = cursor.fetchall()

    if configs:
        response = "لیست کانفیگ‌های شما:\n"
        for config in configs:
            response += f"کانفیگ: {config[0]}\n"
        await callback_query.message.reply_text(response)
    else:
        await callback_query.message.reply_text("شما هیچ کانفیگ تایید شده‌ای ندارید.")

# Run bot
app.run()
