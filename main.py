from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import PeerIdInvalid

import sqlite3
import qrcode
import io
from PIL import Image
import os


# Create database connection
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                    chat_id INTEGER PRIMARY KEY,
                    name TEXT)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS licenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    license_key TEXT,
                    status TEXT,
                    chat_id INTEGER,
                    purchase_id INTEGER)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS purchases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER,
                    license_key TEXT,
                    status TEXT)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS config_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id TEXT,
                    file_name TEXT)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS wallets
                  (user_id INTEGER PRIMARY KEY, balance REAL)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS referrals
                  (user_id INTEGER PRIMARY KEY, referrer_id INTEGER)''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS openvpn_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
)
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS purchased_configs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        plan_id INTEGER,
        plan_type TEXT,
        purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')


cursor.execute('''
CREATE TABLE IF NOT EXISTS v2ray_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
)
''')

cursor.execute('''CREATE TABLE IF NOT EXISTS configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plan_id INTEGER,
                    plan_type TEXT,
                    config_text TEXT,
                    FOREIGN KEY(plan_id) REFERENCES licenses(id)
                )''')


try:
    cursor.execute('ALTER TABLE licenses ADD COLUMN chat_id INTEGER')
except sqlite3.OperationalError:
    pass

try:
    cursor.execute('ALTER TABLE purchases ADD COLUMN purchase_id INTEGER')
except sqlite3.OperationalError:
    pass

try:
    cursor.execute('ALTER TABLE licenses ADD COLUMN config_type TEXT')
except sqlite3.OperationalError:
    pass

try:
    cursor.execute('''ALTER TABLE licenses
                  ADD COLUMN plan_type TEXT CHECK(plan_type IN ('openvpn', 'v2ray'))''')
except sqlite3.OperationalError:
    pass

try:
    cursor.execute('''
                   ALTER TABLE configs ADD COLUMN status TEXT DEFAULT 'available';
                   ''')

except sqlite3.OperationalError:
    pass


try:
    cursor.execute('''
                   ALTER TABLE openvpn_plans ADD COLUMN price INTEGER;
                   ''')
except sqlite3.OperationalError:
    pass

try:
    cursor.execute('''
                   ALTER TABLE v2ray_plans ADD COLUMN price INTEGER;
                   ''')
except sqlite3.OperationalError:
    pass

conn.commit()

# end database

# Bot token and admin list
API_ID = 29365133
API_HASH = "722d0eb612a789286c0ed9966c473ddf"
BOT_TOKEN = "7448692701:AAHKuwrFJlZot86nKm9TWnbqM1fslJ_mRYE"
ADMIN_IDS = [1734062356, 799574527, 6171236939,5973267660,6171236939,624982815,494197025]

# Initialize Client
app = Client("FIFI shop", api_id=API_ID,
             api_hash=API_HASH, bot_token=BOT_TOKEN)

# Dictionary to store user states
user_states = {}
pending_transactions = {}

# Function to send message to admin


async def send_admin_message(admin_id, message_text, reply_markup=None):
    await app.send_message(admin_id, message_text, reply_markup=reply_markup)

# Command handlers


@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    chat_id = message.chat.id
    name = message.from_user.first_name

    cursor.execute(
        "INSERT OR IGNORE INTO users (chat_id, name) VALUES (?, ?)", (chat_id, name))
    conn.commit()

    args = message.text.split()
    if len(args) > 1:
        referrer_id = int(args[1])
        cursor.execute(
            "SELECT referrer_id FROM referrals WHERE user_id = ?", (chat_id,))
        referrer = cursor.fetchone()

        if not referrer:
            cursor.execute(
                "INSERT OR IGNORE INTO referrals (user_id, referrer_id) VALUES (?, ?)", (chat_id, referrer_id))
            conn.commit()
            await message.reply_text("🎉 شما از طریق لینک معرفی وارد شده‌اید. خوش آمدید! 🎉")

    if chat_id in ADMIN_IDS:
        user_states[chat_id] = "admin_logged_in"
        await message.reply_text("✅ سلام عزیزم به بخش ادمین خوش اومدی از منو های زیر برای مدیریت ربات استفاده بکن!",
                                 reply_markup=InlineKeyboardMarkup([
                                     [InlineKeyboardButton(
                                         "پروفایل من 👩🏼‍💻🧑🏻‍💻", callback_data="profile")],
                                     [InlineKeyboardButton(
                                         "کانفیگ‌های فروش رفته 💼", callback_data="sold_configs")],
                                     [InlineKeyboardButton(
                                         "کانفیگ OpenVPN ➕", callback_data="openvpn_config")],
                                     [InlineKeyboardButton(
                                         "کانفیگ V2Ray ➕", callback_data="v2ray_config")],
                                     [InlineKeyboardButton(
                                         "مدیریت فایل‌های کانفیگ 🗂", callback_data="manage_configs")],
                                     [InlineKeyboardButton(
                                         "زیر مجموعه گیری 🔗", callback_data="referral_link")]
                                 ]))
    else:
        await message.reply_text("👋🏻سلام به ربات خودتون خوش اومدید❤️\nاز منو های زیر جهت خرید میتونید استفاده کنید🤗❤️",
                                 reply_markup=InlineKeyboardMarkup([
                                     [InlineKeyboardButton(
                                         "پروفایل من 👩🏼‍💻🧑🏻‍💻", callback_data="profile")],
                                     [InlineKeyboardButton(
                                         "🌎 سرویس‌گیمینگ", callback_data="shop_openvpn")],
                                     [InlineKeyboardButton(
                                         "📱 V2", callback_data="shop_v2ray")],
                                     [InlineKeyboardButton(
                                         "مشاهده لیست کانفیگ‌های من 📄", callback_data="my_configs")],
                                     [InlineKeyboardButton(
                                         "دانلود فایل‌های کانفیگ 📥", callback_data="download_configs")],
                                     [InlineKeyboardButton(
                                         " افزایش موجودی کیف پول 💰", callback_data="add_amount")],
                                     [InlineKeyboardButton(
                                         " زیر مجموعه گیری 🔗", callback_data="referral_link")],
                                     [InlineKeyboardButton(
                                         "ارتباط پشتیبانی 📞", callback_data="support_id")],
                                     [InlineKeyboardButton(
                                         "آموزش 📚", callback_data="tutorials")]
                                 ]))


@app.on_callback_query(filters.regex("go_home"))
async def start(client, callback_query):
    chat_id = callback_query.from_user.id
    name = callback_query.from_user.first_name
    if chat_id in ADMIN_IDS:
        user_states[chat_id] = "admin_logged_in"
        await callback_query.message.edit_text(
            "✅ سلام عزیزم به بخش ادمین خوش اومدی از منو های زیر برای مدیریت ربات استفاده بکن!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "پروفایل من 👩🏼‍💻🧑🏻‍💻 ", callback_data="profile")],
                [InlineKeyboardButton(
                    "کانفیگ‌های فروش رفته 💼", callback_data="sold_configs")],
                [InlineKeyboardButton("کانفیگ OpenVPN ➕",
                                      callback_data="openvpn_config")],
                [InlineKeyboardButton(
                    "کانفیگ V2Ray ➕", callback_data="v2ray_config")],
                [InlineKeyboardButton(
                    "مدیریت فایل‌های کانفیگ 🗂", callback_data="manage_configs")],
                [InlineKeyboardButton(
                    "زیر مجموعه گیری 🔗", callback_data="referral_link")]
            ])
        )
    else:
        await callback_query.message.edit_text(
            "👋🏻سلام به ربات خودتون خوش اومدید❤️\nاز منو های زیر جهت خرید میتونید استفاده کنید🤗❤️",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "پروفایل من 👩🏼‍💻🧑🏻‍💻", callback_data="profile")],
                [InlineKeyboardButton(
                    "🌎 سرویس‌گیمینگ", callback_data="shop_openvpn")],
                [InlineKeyboardButton(
                    "📱 V2", callback_data="shop_v2ray")],
                [InlineKeyboardButton(
                    "مشاهده لیست کانفیگ‌های من 📄", callback_data="my_configs")],
                [InlineKeyboardButton(
                    "دانلود فایل‌های کانفیگ 📥", callback_data="download_configs")],
                [InlineKeyboardButton(
                    " افزایش موجودی کیف پول 💰", callback_data="add_amount")],
                [InlineKeyboardButton(
                    " زیر مجموعه گیری 🔗", callback_data="referral_link")],
                [InlineKeyboardButton(
                    "ارتباط پشتیبانی 📞", callback_data="support_id")],
                [InlineKeyboardButton(
                    "آموزش 📚", callback_data="tutorials")]
            ])
        )


@app.on_callback_query(filters.regex("support_id"))
async def support_callback(client, callback_query):
    await callback_query.message.reply_text("📞 برای ارتباط با پشتیبانی به ایدی زیر پیام بدید: @FifiSupport")


@app.on_callback_query(filters.regex("tutorials"))
async def tutorials_callback(client, callback_query):
    await callback_query.message.reply_text("📚 لطفاً نوع آموزش مورد نظر خود را انتخاب کنید:",
                                            reply_markup=InlineKeyboardMarkup([
                                                [InlineKeyboardButton(
                                                    "گیمینگ 🎮", callback_data="gaming_tutorial")],
                                                [InlineKeyboardButton(
                                                    "V2 📱", callback_data="v2_tutorial")]
                                            ]))


@app.on_callback_query(filters.regex("gaming_tutorial"))
async def gaming_tutorial_callback(client, callback_query):
    video_paths = ["videos/gaming-android.MOV", "videos/gaming-iphone.MOV"]
    for video_path in video_paths:
        if os.path.exists(video_path):
            with open(video_path, "rb") as video:
                await callback_query.message.reply_video(video)
        else:
            await callback_query.message.reply_text(f"❌ در ارسال ویدیو مشکلی پیش اومده به ادمین بگید")

@app.on_callback_query(filters.regex("v2_tutorial"))
async def v2_tutorial_callback(client, callback_query):
    video_path = "videos/v2.MOV"
    if os.path.exists(video_path):
        with open(video_path, "rb") as video:
            await callback_query.message.reply_video(video)
    else:
            await callback_query.message.reply_text(f"❌ در ارسال ویدیو مشکلی پیش اومده به ادمین بگید")

@app.on_callback_query(filters.regex("sold_configs"))
async def sold_configs(client, callback_query):
    chat_id = callback_query.from_user.id

    if chat_id in ADMIN_IDS:
        cursor.execute(
            "SELECT license_key, chat_id FROM licenses WHERE status = 'sold'")
        sold_licenses = cursor.fetchall()

        if sold_licenses:
            response = "کانفیگ‌های فروش رفته:\n"
            for license_key, user_id in sold_licenses:
                response += f"کانفیگ: {license_key} - کاربر: {user_id}\n"
            await callback_query.message.reply_text(response)
        else:
            await callback_query.message.reply_text("هیچ کانفیگ فروخته‌شده‌ای وجود ندارد.")
    else:
        await callback_query.answer("شما دسترسی ادمین ندارید ⛔", show_alert=True)


@app.on_callback_query(filters.regex("openvpn_config"))
async def openvpn_config(client, callback_query):
    chat_id = callback_query.from_user.id
    if chat_id in ADMIN_IDS:
        user_states[chat_id] = "admin_logged_in"
        await client.send_message(
            chat_id=chat_id,
            text="مدیریت کانفیگ OpenVPN:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "➕ اضافه کردن پلن جدید", callback_data="add_plan_openvpn")],
                [InlineKeyboardButton(
                    "➕ اضافه کردن کانفیگ OpenVPN", callback_data="add_config_open")]
            ])
        )
    else:
        await callback_query.answer("⛔ شما دسترسی ادمین ندارید.", show_alert=True)


@app.on_callback_query(filters.regex("add_config_open"))
async def add_openvpn_config(client, callback_query):
    chat_id = callback_query.from_user.id
    if chat_id in ADMIN_IDS:
        cursor.execute("SELECT id, name FROM openvpn_plans")
        openvpn_plans = cursor.fetchall()

        buttons = [
            [InlineKeyboardButton(
                plan[1], callback_data=f"add_openvpn_plan_{plan[0]}")]
            for plan in openvpn_plans
        ]

        user_states[chat_id] = "select_openvpn_plan"
        await client.send_message(chat_id, "لطفا پلن کانفیگ OpenVPN را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(buttons))
    else:
        await callback_query.answer("شما ادمین نیستید ⛔", show_alert=True)


@app.on_callback_query(filters.regex(r"^add_openvpn_plan_\d+$"))
async def process_openvpn_plan(client, callback_query):
    chat_id = callback_query.from_user.id

    if chat_id in ADMIN_IDS:
        plan_id = int(callback_query.data.split("_")[-1])

        user_states[chat_id] = {
            "action": "collect_config",
            "type": "openvpn",
            "plan_id": plan_id
        }

        await client.send_message(chat_id, f"کانفیگ ها رو خط به خط وارد بکنید")
    else:
        await callback_query.answer("مشکلی به وجود امده با اول دوباره امتحان بکنید بعد با سازنده تماس بگیرید", show_alert=True)


@app.on_callback_query(filters.regex("v2ray_config_add"))
async def add_v2ray_config(client, callback_query):
    chat_id = callback_query.from_user.id
    if chat_id in ADMIN_IDS:
        cursor.execute("SELECT id, name FROM v2ray_plans")
        v2ray_plans = cursor.fetchall()

        buttons = [
            [InlineKeyboardButton(
                plan[1], callback_data=f"add_v2ray_plan_{plan[0]}")]
            for plan in v2ray_plans
        ]

        user_states[chat_id] = "select_v2ray_plan"
        await client.send_message(chat_id, "لطفا پلن کانفیگ V2Ray را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(buttons))
    else:
        await callback_query.answer("شما ادمین نیستید ⛔", show_alert=True)


@app.on_callback_query(filters.regex(r"^add_v2ray_plan_\d+$"))
async def process_v2ray_plan(client, callback_query):
    chat_id = callback_query.from_user.id

    if chat_id in ADMIN_IDS:
        plan_id = int(callback_query.data.split("_")[-1])

        user_states[chat_id] = {
            "action": "collect_config",
            "type": "v2ray",
            "plan_id": plan_id
        }

        await client.send_message(chat_id, f"کانفیگ ها رو خط به خط وارد بکنید")
    else:
        await callback_query.answer("مشکلی به وجود امده با اول دوباره امتحان بکنید بعد با سازنده تماس بگیرید", show_alert=True)


@app.on_message(filters.text & filters.private)
async def handle_private_message(client, message):
    chat_id = message.chat.id
    text = message.text.strip()

    if chat_id in user_states:
        state = user_states[chat_id]

        if isinstance(state, dict):
            action = state.get("action")

            if action == "collect_config":
                type_of_plan = state["type"]
                config_lines = text.split('\n')
                plan_id = state["plan_id"]

                try:
                    for config_text in config_lines:
                        cursor.execute("INSERT INTO configs (plan_id, plan_type, config_text) VALUES (?, ?, ?)",
                                       (plan_id, type_of_plan, config_text.strip()))
                    conn.commit()
                    await message.reply_text("کانفیگ‌ها با موفقیت اضافه شدند.")
                except Exception as e:
                    await message.reply_text(f"خطایی در افزودن کانفیگ‌ها رخ داده است: {str(e)}")
                finally:
                    del user_states[chat_id]

            elif action == "adding_openvpn_plan":
                step = state.get("step")

                if step == "name":
                    user_states[chat_id]["name"] = text
                    user_states[chat_id]["step"] = "price"
                    await message.reply_text("لطفاً قیمت پلن OpenVPN را به تومان وارد کنید:")

                elif step == "price":
                    try:
                        price = int(text)
                        plan_name = user_states[chat_id]["name"]
                        cursor.execute(
                            "INSERT INTO openvpn_plans (name, price) VALUES (?, ?)", (plan_name, price))
                        conn.commit()
                        await message.reply_text(f"پلن OpenVPN با نام {plan_name} و قیمت {price} تومان با موفقیت اضافه شد ✅")
                    except ValueError:
                        await message.reply_text("لطفاً یک عدد معتبر برای قیمت وارد کنید.")
                    finally:
                        del user_states[chat_id]

            elif action == "adding_v2ray_plan":
                step = state.get("step")

                if step == "name":
                    user_states[chat_id]["name"] = text
                    user_states[chat_id]["step"] = "price"
                    await message.reply_text("لطفاً قیمت پلن V2Ray را به تومان وارد کنید:")

                elif step == "price":
                    try:
                        price = int(text)
                        plan_name = user_states[chat_id]["name"]
                        cursor.execute(
                            "INSERT INTO v2ray_plans (name, price) VALUES (?, ?)", (plan_name, price))
                        conn.commit()
                        await message.reply_text(f"پلن V2Ray با نام {plan_name} و قیمت {price} تومان با موفقیت اضافه شد ✅")
                    except ValueError:
                        await message.reply_text("لطفاً یک عدد معتبر برای قیمت وارد کنید.")
                    finally:
                        del user_states[chat_id]

        if state == "adding_wallet_amount":
            try:
                amount = float(text)
                pending_transactions[chat_id] = {"amount": amount}
                user_states[chat_id] = "awaiting_payment_proof"
                await message.reply_text("لطفاً مقدار مورد نظر کیف پول خود را به شماره کارت زیر واریز بکنید و سپس عکس واریزی را ارسال کنید❤️🙏🏻\n1234-5678-9876-5432\nیزدانی")
            except ValueError:
                await message.reply_text("لطفاً یک عدد معتبر وارد کنید.")

        elif state == "adding_licenses":
            licenses = text.split('\n')
            for license_key in licenses:
                cursor.execute(
                    "INSERT INTO licenses (license_key, status, purchase_id) VALUES (?, 'set', NULL)", (license_key,))
            conn.commit()
            user_states[chat_id] = "admin_logged_in"
            await message.reply_text("کانفیگ‌های جدید اضافه شدند➕✅")

        elif state == "admin_logged_in":
            cursor.execute(
                "INSERT INTO licenses (license_key, status, purchase_id) VALUES (?, 'set', NULL)", (text,))
            conn.commit()
            await message.reply_text("کانفیگ جدید اضافه شد➕✅")
    else:
        pass


@app.on_callback_query(filters.regex("profile"))
async def profile(client, callback_query):
    chat_id = callback_query.from_user.id
    try:
        cursor.execute("SELECT name FROM users WHERE chat_id = ?", (chat_id,))
        user_profile = cursor.fetchone()
    except sqlite3.OperationalError as e:
        await callback_query.answer("خطا در دریافت پروفایل. لطفاً بعداً تلاش کنید.", show_alert=True)
        print(e)
        return

    if user_profile:
        name = user_profile[0]
    else:
        await callback_query.answer("پروفایل شما یافت نشد ⛔", show_alert=True)
        return

    # Fetch wallet balance
    cursor.execute("SELECT balance FROM wallets WHERE user_id = ?", (chat_id,))
    wallet = cursor.fetchone()
    balance = wallet[0] if wallet else 0

    # Fetch referral count
    cursor.execute(
        "SELECT COUNT(*) FROM referrals WHERE referrer_id = ?", (chat_id,))
    referral_count = cursor.fetchone()[0]

    # Fetch configuration count
    cursor.execute(
        "SELECT COUNT(*) FROM purchases WHERE chat_id = ?", (chat_id,))
    config_count = cursor.fetchone()[0]

    # Prepare the profile message
    profile_message = (
        f"👤 پروفایل شما:\n\n"
        f"📝 نام: {name}\n"
        f"💰 موجودی کیف پول: {balance} تومان\n"
        f"👥 تعداد ریفرال‌ها: {referral_count}\n"
        f"📁 تعداد کانفیگ‌ها: {config_count}\n"
    )

    await client.send_message(
        chat_id=chat_id,
        text=profile_message
    )

    await callback_query.answer()


@app.on_callback_query(filters.regex("referral_link"))
async def send_referral_link(client, callback_query):
    chat_id = callback_query.from_user.id
    referral_link = f"https://t.me/fifishopbot?start={chat_id}"
    await callback_query.message.reply_text(
        f"با لینک زیر دوستاتو به ربات دعوت کن و با هر خرید 10,000 تومان بدست بیار💎💸\n\n{referral_link}"
    )


@app.on_callback_query(filters.regex("v2ray_config"))
async def v2ray_config(client, callback_query):
    chat_id = callback_query.from_user.id
    if chat_id in ADMIN_IDS:
        user_states[chat_id] = "admin_logged_in"
        await client.send_message(
            chat_id=chat_id,
            text="مدیریت کانفیگ V2Ray:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "➕ اضافه کردن پلن جدید", callback_data="add_v2ray_plan")],
                [InlineKeyboardButton(
                    "➕ اضافه کردن کانفیگ V2Ray", callback_data="v2ray_config_add")]
            ])
        )
    else:
        await callback_query.answer("⛔ شما دسترسی ادمین ندارید.", show_alert=True)


@app.on_callback_query(filters.regex("add_plan_openvpn"))
async def add_openvpn_plan(client, callback_query):
    chat_id = callback_query.from_user.id
    if chat_id in ADMIN_IDS:
        user_states[chat_id] = {
            "action": "adding_openvpn_plan", "step": "name"}
        await callback_query.message.reply_text("لطفاً نام پلن جدید OpenVPN را وارد کنید:")


@app.on_callback_query(filters.regex("add_v2ray_plan"))
async def add_v2ray_plan(client, callback_query):
    chat_id = callback_query.from_user.id
    if chat_id in ADMIN_IDS:
        user_states[chat_id] = {"action": "adding_v2ray_plan", "step": "name"}
        await callback_query.message.reply_text("لطفاً نام پلن جدید V2Ray را وارد کنید:")


@app.on_callback_query(filters.regex("add_amount"))
async def add_amount(client, callback_query):
    chat_id = callback_query.from_user.id
    user_states[chat_id] = "adding_wallet_amount"
    print(user_states)
    await callback_query.message.reply_text("لطفا مبلغ مورد نیاز خود را به تومان وارد بکنید")


@app.on_message(filters.photo & filters.private)
async def handle_wallet_amount_photo(client, message):
    chat_id = message.chat.id
    state = user_states[chat_id]

    
    print(state)
    if user_states.get(chat_id) == "awaiting_payment_proof":
        photo_id = message.photo.file_id
        pending_transactions[chat_id]["photo_id"] = photo_id
        await message.reply_text("عکس واریزی دریافت شد. در حال ارسال به ادمین برای تایید.")

        for admin_id in ADMIN_IDS:
            try:
                await client.get_users(admin_id)
                await client.send_photo(
                    chat_id=admin_id,
                    photo=photo_id,
                    caption=f"کاربر {chat_id} درخواست افزودن {pending_transactions[chat_id]['amount']} به کیف پول را دارد.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            "تایید", callback_data=f"confirm_{chat_id}")],
                        [InlineKeyboardButton(
                            "رد", callback_data=f"reject_{chat_id}")]
                    ])
                )
            except Exception as e:
                print(f"Failed to send photo to admin {admin_id}: {e}")

        user_states[chat_id] = "pending_admin_approval"
        chat_id = message.chat.id

    elif isinstance(state, dict) and state.get("action").startswith('awaiting_admin_approval_openvpn_'):
        plan_type = state.get("action").split("_")[-1]
        user_states[chat_id] = f"awaiting_admin_approval_openvpn_{plan_type}"
        file_id = message.photo.file_id
        await message.reply_text("عکس تایید پرداخت OpenVPN دریافت شد. منتظر تایید ادمین باشید.")

        for admin_id in ADMIN_IDS:
            await client.send_photo(admin_id, file_id, caption=f"کاربر {chat_id} عکس تایید پرداخت OpenVPN پلن {plan_type} ارسال کرده است. برای تایید، از دستور /approve_openvpn_{chat_id}_{plan_type} استفاده کنید.",
                                    reply_markup=InlineKeyboardMarkup([
                                        [InlineKeyboardButton("تایید", callback_data=f"approve_openvpn_{chat_id}_{plan_type}")],
                                        [InlineKeyboardButton("رد", callback_data=f"reject_openvpn_{chat_id}_{plan_type}")]
                                    ]))
    elif isinstance(state, dict) and state.get("action").startswith('awaiting_admin_approval_v2ray_'):
        plan_type = state.get("action").split("_")[-1]
        user_states[chat_id] = f"awaiting_admin_approval_v2ray_{plan_type}"
        file_id = message.photo.file_id
        await message.reply_text("عکس تایید پرداخت V2ray دریافت شد. منتظر تایید ادمین باشید.")

        for admin_id in ADMIN_IDS:
            await client.send_photo(admin_id, file_id, caption=f"کاربر {chat_id} عکس تایید پرداخت V2ray پلن {plan_type} ارسال کرده است. برای تایید، از دستور /approve_v2ray_{chat_id}_{plan_type} استفاده کنید.",
                                    reply_markup=InlineKeyboardMarkup([
                                        [InlineKeyboardButton("تایید", callback_data=f"approve_v2ray_{chat_id}_{plan_type}")],
                                        [InlineKeyboardButton("رد", callback_data=f"reject_v2ray_{chat_id}_{plan_type}")]
                                    ]))

    else:
        await message.reply_text("لطفاً ابتدا مقدار کیف پول را وارد کنید.")


@app.on_callback_query(filters.regex(r"confirm_\d+|reject_\d+"))
async def handle_admin_response(client, callback_query):
    action, user_id = callback_query.data.split("_")
    user_id = int(user_id)

    if user_id in pending_transactions:
        if action == "confirm":
            amount = pending_transactions[user_id]["amount"]
            cursor.execute(
                "INSERT OR IGNORE INTO wallets (user_id, balance) VALUES (?, ?)", (user_id, 0))
            cursor.execute(
                "UPDATE wallets SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
            conn.commit()

            cursor.execute(
                "SELECT referrer_id FROM referrals WHERE user_id = ?", (user_id,))
            referrer_id = cursor.fetchone()
            if referrer_id:
                referrer_id = referrer_id[0]
                cursor.execute(
                    "INSERT OR IGNORE INTO wallets (user_id, balance) VALUES (?, ?)", (referrer_id, 0))
                cursor.execute(
                    "UPDATE wallets SET balance = balance + 10000 WHERE user_id = ?", (referrer_id,))
                conn.commit()
                await client.send_message(chat_id=referrer_id, text="یک کاربر از زیر مجموعه شما خرید انجام داده است. 10000 تومان به کیف پول شما اضافه شد.")

            await client.send_message(chat_id=user_id, text=f"مبلغ {amount} به کیف پول شما اضافه شد.")
            await callback_query.message.reply_text(f"مبلغ {amount} برای کاربر {user_id} تایید شد و به کیف پول اضافه شد.")
            del pending_transactions[user_id]
            user_states[user_id] = None
        elif action == "reject":
            await client.send_message(chat_id=user_id, text="درخواست شما برای افزودن مبلغ به کیف پول رد شد.")
            await callback_query.message.reply_text(f"درخواست کاربر {user_id} رد شد.")
            del pending_transactions[user_id]
            user_states[user_id] = None
    else:
        await callback_query.message.reply_text("درخواست پیدا نشد.")


@app.on_callback_query(filters.regex("shop_v2ray"))
async def shop_v2ray(client, callback_query):
    cursor.execute("""
        SELECT v2ray_plans.id, v2ray_plans.name, v2ray_plans.price, COUNT(configs.id) AS available_count
        FROM v2ray_plans
        LEFT JOIN configs ON v2ray_plans.id = configs.plan_id AND configs.plan_type = 'v2ray' AND configs.status = 'available'
        GROUP BY v2ray_plans.id
    """)
    openvpn_plans = cursor.fetchall()

    buttons = []
    for plan in openvpn_plans:
        plan_id, plan_name, plan_price, available_count = plan
        if available_count > 0:
            button_text = f"{plan_name} - {plan_price} تومان (موجود)"
            callback_data = f"shop_plan_v2ray_{plan_id}"
        else:
            button_text = f"{plan_name} - {plan_price} تومان (ناموجود)"
            callback_data = f"disabled_{plan_id}"

        buttons.append([InlineKeyboardButton(
            button_text, callback_data=callback_data)])

    buttons.append([InlineKeyboardButton(
        "برگشت به خانه", callback_data="go_home")])

    new_text = "لطفا پلن کانفیگ V2ray را انتخاب کنید:"
    if callback_query.message.text != new_text:
        await callback_query.message.edit_text(
            new_text,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    else:
        await callback_query.answer("هیچ تغییری در پیام وجود ندارد.")


@app.on_callback_query(filters.regex(r"disabled_(\d+)"))
async def disabled_button(client, callback_query):
    await callback_query.answer("این پلن در حال حاضر موجود نیست.", show_alert=True)


@app.on_callback_query(filters.regex(r"shop_plan_openvpn_(\d+)"))
async def process_buy_config_open(client, callback_query):
    user_id = callback_query.from_user.id
    plan_id = int(callback_query.data.split('_')[-1])
    cursor.execute("SELECT balance FROM wallets WHERE user_id = ?", (user_id,))
    user_wallet = cursor.fetchone()

    plan_price = get_plan_price(plan_id, "openvpn")

    if user_wallet and user_wallet[0] >= plan_price:
        user_states[user_id] = {
            "action": f"confirm_purchase_openvpn_{plan_id}", "plan_id": plan_id, "plan_price": plan_price}

        await callback_query.message.reply_text(
            f"موجودی کیف پول شما کافی است. آیا مایل به خرید این پلن با قیمت {plan_price} تومان هستید؟",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "بله", callback_data=f"confirm_purchase_openvpn_{plan_id}")],
                [InlineKeyboardButton("خیر", callback_data="cancel_purchase")]
            ])
        )
    else:
        user_states[user_id] = {
            "action": f"awaiting_admin_approval_openvpn_{plan_id}", "plan_id": plan_id}

        await callback_query.message.reply_text("موجودی کیف پول شما کافی نیست.برای خرید کانفیگ به شماره کارت زیر واریز کنید و عکس پرداخت رو ارسال کنید و یا موجودی کیف پول خود را افزایش دهید❤️🙏🏻\n1234-5678-9876-5432\nیزدانی")


@app.on_callback_query(filters.regex(r"confirm_purchase_openvpn_(\d+)"))
async def confirm_purchase_openvpn(client, callback_query):
    user_id = callback_query.from_user.id
    plan_id = int(callback_query.data.split('_')[-1])
    user_state = user_states.get(user_id)

    if user_state and user_state["action"] == f"confirm_purchase_openvpn_{plan_id}":
        plan_price = user_state["plan_price"]
        cursor.execute(
            "UPDATE wallets SET balance = balance - ? WHERE user_id = ?", (plan_price, user_id))
        conn.commit()

        cursor.execute(
            "SELECT id, config_text FROM configs WHERE plan_id = ? AND plan_type = 'openvpn' AND status = 'available' LIMIT 1", (plan_id,))
        config_row = cursor.fetchone()

        if config_row:
            config_id, config_text = config_row
            cursor.execute(
                "UPDATE configs SET status = 'sold' WHERE id = ?", (config_id,))
            conn.commit()

            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(config_text)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")
            bio = io.BytesIO()
            img.save(bio, format='PNG')
            bio.seek(0)

            await client.send_photo(
                chat_id=user_id,
                photo=bio,
                caption=f"خرید شما موفقیت‌آمیز بود. این هم کانفیگ شما:\n{config_text}"
            )

            del user_states[user_id]
            await callback_query.message.delete()
        else:
            await callback_query.message.reply_text("متأسفانه هیچ کانفیگ موجودی برای این پلن وجود ندارد.")
    else:
        await callback_query.message.reply_text("تأیید خرید نامعتبر است یا منقضی شده است.")


@app.on_callback_query(filters.regex("shop_openvpn"))
async def shop_openvpn(client, callback_query):
    cursor.execute("""
        SELECT openvpn_plans.id, openvpn_plans.name, openvpn_plans.price, COUNT(configs.id) AS available_count
        FROM openvpn_plans
        LEFT JOIN configs ON openvpn_plans.id = configs.plan_id AND configs.plan_type = 'openvpn' AND configs.status = 'available'
        GROUP BY openvpn_plans.id
    """)
    openvpn_plans = cursor.fetchall()

    buttons = []
    for plan in openvpn_plans:
        plan_id, plan_name, plan_price, available_count = plan
        if available_count > 0:
            button_text = f"{plan_name} - {plan_price} تومان (موجود)"
            callback_data = f"shop_plan_openvpn_{plan_id}"
        else:
            button_text = f"{plan_name} - {plan_price} تومان (ناموجود)"
            callback_data = f"disabled_{plan_id}"

        buttons.append([InlineKeyboardButton(
            button_text, callback_data=callback_data)])

    buttons.append([InlineKeyboardButton(
        "برگشت به خانه", callback_data="go_home")])

    new_text = "لطفا پلن کانفیگ OpenVPN را انتخاب کنید:"
    if callback_query.message.text != new_text:
        await callback_query.message.edit_text(
            new_text,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    else:
        await callback_query.answer("هیچ تغییری در پیام وجود ندارد.")


@app.on_callback_query(filters.regex(r"disabled_(\d+)"))
async def disabled_button(client, callback_query):
    await callback_query.answer("این پلن در حال حاضر موجود نیست.", show_alert=True)


@app.on_callback_query(filters.regex(r"shop_plan_v2ray_(\d+)"))
async def process_buy_config_v2ray(client, callback_query):
    user_id = callback_query.from_user.id
    plan_id = int(callback_query.data.split('_')[-1])

    cursor.execute("SELECT balance FROM wallets WHERE user_id = ?", (user_id,))
    user_wallet = cursor.fetchone()

    if user_wallet and user_wallet[0] >= get_plan_price(plan_id, "v2ray"):
        plan_price = get_plan_price(plan_id, "v2ray")
        user_states[user_id] = {
            "action": f"confirm_purchase_v2ray_{plan_id}", "plan_id": plan_id, "plan_price": plan_price}

        await callback_query.message.reply_text(
            f"موجودی کیف پول شما کافی است. آیا مایل به خرید این پلن با قیمت {
                plan_price} تومان هستید؟",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "بله", callback_data=f"confirm_purchase_v2ray_{plan_id}")],
                [InlineKeyboardButton("خیر", callback_data="cancel_purchase")]
            ])
        )
    else:
        user_states[user_id] = {
            "action": f"awaiting_admin_approval_v2ray_{plan_id}", "plan_id": plan_id}
        await callback_query.message.reply_text("موجودی کیف پول شما کافی نیست.برای خرید کانفیگ به شماره کارت زیر واریز کنید و عکس پرداخت رو ارسال کنید و یا موجودی کیف پول خود را افزایش دهید❤️🙏🏻\n1234-5678-9876-5432\nیزدانی")


@app.on_callback_query(filters.regex(r"confirm_purchase_v2ray_(\d+)"))
async def confirm_purchase_v2ray(client, callback_query):
    user_id = callback_query.from_user.id
    plan_id = int(callback_query.data.split('_')[-1])

    if user_id in user_states:
        plan_price = user_states[user_id]["plan_price"]

        cursor.execute(
            "UPDATE wallets SET balance = balance - ? WHERE user_id = ?", (plan_price, user_id))
        conn.commit()

        cursor.execute(
            "SELECT id, config_text FROM configs WHERE plan_id = ? AND plan_type = 'v2ray' AND status = 'available' LIMIT 1",
            (plan_id,))
        config_row = cursor.fetchone()

        if config_row:
            config_id, config_text = config_row

            cursor.execute(
                "UPDATE configs SET status = 'sold' WHERE id = ?", (config_id,))
            conn.commit()

            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(config_text)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white")

            await client.send_photo(user_id, qr_img, caption=f"کانفیگ V2Ray شما:\n{config_text}")

            await callback_query.answer("خرید تایید شد و کانفیگ برای شما ارسال شد.", show_alert=True)
            await client.send_message(user_id, "خرید شما تایید شد و کانفیگ V2Ray برای شما ارسال شد.")

            if user_id in user_states:
                del user_states[user_id]
        else:
            await callback_query.answer("هیچ کانفیگی برای این پلن موجود نیست.", show_alert=True)
    else:
        await callback_query.answer("خطای ناشناخته رخ داده است.", show_alert=True)


def get_plan_price(plan_id, plan_type):
    if plan_type == "v2ray":
        cursor.execute(
            "SELECT price FROM v2ray_plans WHERE id = ?", (plan_id,))
    else:
        cursor.execute(
            "SELECT price FROM openvpn_plans WHERE id = ?", (plan_id,))

    plan = cursor.fetchone()
    return plan[0] if plan else None


@app.on_callback_query(filters.regex("cancel_purchase"))
async def cancel_purchase(client, callback_query):
    user_id = callback_query.from_user.id
    if user_id in user_states:
        del user_states[user_id]
    await callback_query.answer("خرید لغو شد.", show_alert=True)
    await callback_query.message.delete()


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


@app.on_callback_query(filters.regex(r"approve_openvpn_(\d+)_(\d+)"))
async def approve_openvpn_payment(client, callback_query):
    admin_id = callback_query.from_user.id
    user_chat_id = int(callback_query.data.split('_')[2])
    plan_id = int(callback_query.data.split('_')[3])
    if(user_chat_id in user_states):
        if admin_id in ADMIN_IDS:
            try:
                cursor.execute("SELECT id, config_text FROM configs WHERE plan_id = ? AND plan_type = ? AND status = 'available' LIMIT 1",
                            (plan_id, 'openvpn'))

                config_row = cursor.fetchone()

                if config_row:
                    config_id, config_text = config_row

                    cursor.execute(
                        "UPDATE configs SET status = 'sold' WHERE id = ?", (config_id,))
                    conn.commit()

                    await client.send_message(user_chat_id, config_text)

                    await callback_query.answer("پرداخت تایید شد و کانفیگ برای کاربر ارسال شد.", show_alert=True)
                    await client.send_message(user_chat_id, "پرداخت شما تایید شد و کانفیگ OpenVPN برای شما ارسال شد.")

                    if user_chat_id in user_states:
                        del user_states[user_chat_id]
                        await callback_query.message.delete()
                else:
                    await callback_query.answer("هیچ کانفیگی برای این پلن موجود نیست.", show_alert=True)
            except Exception as e:
                await callback_query.answer(f"خطایی رخ داد: {str(e)}", show_alert=True)
        else:
            await callback_query.answer("شما اجازه این کار را ندارید.", show_alert=True)


@app.on_callback_query(filters.regex(r"approve_v2ray_(\d+)_(\d+)"))
async def approve_v2ray_payment(client, callback_query):
    admin_id = callback_query.from_user.id
    user_chat_id = int(callback_query.data.split('_')[2])
    plan_id = int(callback_query.data.split('_')[3])
    if(user_chat_id in user_states):
        if admin_id in ADMIN_IDS:
            try:
                cursor.execute("SELECT id, config_text FROM configs WHERE plan_id = ? AND plan_type = ? AND status = 'available' LIMIT 1",
                            (plan_id, 'v2ray'))

                config_row = cursor.fetchone()

                if config_row:
                    config_id, config_text = config_row

                    cursor.execute(
                        "UPDATE configs SET status = 'sold' WHERE id = ?", (config_id,))
                    conn.commit()

                    await client.send_message(user_chat_id, config_text)

                    await callback_query.answer("پرداخت تایید شد و کانفیگ برای کاربر ارسال شد.", show_alert=True)
                    await client.send_message(user_chat_id, "پرداخت شما تایید شد و کانفیگ V2ray برای شما ارسال شد.")

                    if user_chat_id in user_states:
                        del user_states[user_chat_id]
                        await callback_query.message.delete()
                else:
                    await callback_query.answer("هیچ کانفیگی برای این پلن موجود نیست.", show_alert=True)
            except Exception as e:
                await callback_query.answer(f"خطایی رخ داد: {str(e)}", show_alert=True)
        else:
            await callback_query.answer("شما اجازه این کار را ندارید.", show_alert=True)
    else:
        await callback_query.answer("عملیات یا تایید یا رد شده توسط فرد دیگیری با منقضی شده.", show_alert=True)
        


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


@app.on_callback_query(filters.regex("add_config"))
async def add_config(client, callback_query):
    chat_id = callback_query.from_user.id
    if chat_id in ADMIN_IDS:
        user_states[chat_id] = "adding_licenses"
        await callback_query.message.reply_text("لطفا لیست کانفیگ‌ها را ارسال کنید. هر کانفیگ در یک خط باشد:")
    else:
        await callback_query.answer("شما ادمین نیستید ⛔", show_alert=True)


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
        await callback_query.message.reply_text("شما وارد بخش مدیریت فایل‌های کانفیگ شدید.\nلطفاً یک فایل OVP ارسال کنید.",
                                                reply_markup=InlineKeyboardMarkup([
                                                    [InlineKeyboardButton(
                                                        "مشاهده لیست فایل‌های OVP", callback_data="view_configs")],
                                                    [InlineKeyboardButton(
                                                        "اضافه کردن فایل OVP", callback_data="inster_open_file")]
                                                ]))
    else:
        await callback_query.answer("شما ادمین نیستید ⛔", show_alert=True)


@app.on_callback_query(filters.regex("inster_open_file"))
async def add_config_file(client, callback_query):
    chat_id = callback_query.from_user.id
    if chat_id in ADMIN_IDS:
        user_states[chat_id] = "managing_configs"
        print('injast')
        print(user_states[chat_id])
        await callback_query.message.reply_text("لطفاً فایل کانفیگ مورد نظر را ارسال کنید.")
    else:
        await callback_query.answer("شما ادمین نیستید ⛔", show_alert=True)


@app.on_message(filters.document & filters.private)
async def handle_document(client, message):
    chat_id = message.chat.id
    print(user_states.get(chat_id))
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
            file_id = config_file[0]
            file_name = config_file[1]

            if not file_id or not file_name:
                continue
            try:
                await client.send_document(chat_id, file_id, caption=file_name)
            except Exception as e:
                print(f"Failed to send document: {e}")

    else:
        await callback_query.message.reply_text("هیچ فایل کانفیگی برای دانلود موجود نیست.")


app.run()
