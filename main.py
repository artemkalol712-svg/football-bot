"""
Football Bet Bot + Mini App — единый файл для Render.
"""
import asyncio, random, sqlite3, io, os
from datetime import datetime, timedelta
from PIL import Image
import aiohttp
from aiogram import Bot, Dispatcher, F
from aiogram.types import (Message, CallbackQuery, InlineKeyboardMarkup,
    InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton,
    BufferedInputFile, InputMediaPhoto, WebAppInfo)
from aiogram.filters import Command, CommandObject
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ParseMode, ChatType
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from aiogram.utils.web_app import safe_parse_webapp_init_data
import httpx

BOT_TOKEN = os.getenv("BOT_TOKEN", "8513235718:AAGc58HC53i4XxcMBG81MFcAPgBarF8HbWY")
BOT_USERNAME = "Chealofficial_bot"
OWNERS = {8488322314, 6595977966, 6766512894}
CHANNEL_LINK = "https://t.me/OfficialBotcheal"
CHANNEL_USERNAME = "OfficialBotcheal"
CASINO_LINK = "https://t.me/+PhaJ23EE_Y0wNTli"
DONATE_OWNER_ID = 6595977966
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://football-bot-40g0.onrender.com")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY", "6caa83b5d7af4e5ca1a3949b244bd68b")
FOOTBALL_BASE = "https://api.football-data.org/v4"
DB_PATH = os.getenv("DB_PATH", "/data/roulette_bot.db")
try:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
except (PermissionError, OSError):
    DB_PATH = "/tmp/roulette_bot.db"
    os.makedirs("/tmp", exist_ok=True)

CHARACTER_IMAGE_URL = "https://images.meme-arsenal.com/1b33706ef743ada8f45708d260f40436.jpg"
MAP_IMAGE_URL = "https://i.postimg.cc/CMDXYrB0/IMG-20240916-112931-570.jpg"
TRAVEL_IMAGE_URL = "https://files.libertycity.ru/download/gtasa_scripts/thumbs/2020-02/prokatitsja-v-taksi-obnovlenie-ot-13-03_1686003481_741979.webp"
DICE_IMAGE_URL = "https://media.istockphoto.com/id/157169484/ru/фото/холмистый-the-dice.jpg?s=612x612"
STATS_IMAGE_URL = "https://cs4.gtavicecity.ru/screenshots/9a0d4/2024-03/original/13aa905112cf59f62da0cfcbfa8a424253ae0ec0/1384961-gallery9.jpg"
PM_IMAGE_URL = "https://avatars.mds.yandex.net/get-altay/5104421/2a000001816f40d0bb714bb37486b32b9ee8/orig"

CITY_ARRIVAL_IMAGES = {
    "арзамас":"https://quto.ru/thumb/908x0/filters:quality(75)/imgs/2024/06/21/10/6509765/223fa5d780ffb35da7fdc5dff00b702dd094169f.jpg",
    "батырево":"https://avatars.mds.yandex.net/get-altay/16497373/2a000001991941273ac9e0df546b151267e2/orig",
    "нижнегородск":"https://avatars.mds.yandex.net/get-marketcms/944743/img-0cdf5e73-8a39-4d82-a60c-a9e0dca9b3d8.jpeg/optimize",
    "рублёвка":"https://avatars.dzeninfra.ru/get-zen_doc/271828/pub_65f5aec5c52dae7a47731790_65f5aefdf6ad8d2b7145c7f4/scale_1200",
    "лыткарино":"http://ic.pics.livejournal.com/nawepodmoskovie/73348260/377906/377906_original.jpg",
    "южный":"https://drugoigorod.ru/wp-content/uploads/2018/07/055.jpg",
}
TAXI_PHOTOS = {"rent":"https://www.gtabase.com/images/gta-san-andreas/vehicles/taxi.jpg",
    "car":"https://www.gtabase.com/images/gta-san-andreas/vehicles/taxi.jpg",
    "passenger":"https://www.gtabase.com/images/gta-san-andreas/vehicles/taxi.jpg",
    "destination":TRAVEL_IMAGE_URL}
TAXI_ORDERS = {1:{"name":"Эконом","min_payout":1_000_000_000,"max_payout":20_000_000_000,"seconds":65,"emoji":"🚕"},
    2:{"name":"Комфорт","min_payout":8_000_000_000,"max_payout":30_000_000_000,"seconds":70,"emoji":"🚙"},
    3:{"name":"Бизнес","min_payout":10_000_000_000,"max_payout":40_000_000_000,"seconds":100,"emoji":"🚘"}}
TAXI_RENT_PRICE = 20_000_000_000
TAXI_RENT_MINUTES = 15
TAXI_COLLECT_MIN = 50_000_000_000
TAXI_COLLECT_CAP = 1_000_000_000_000
TAXI_COLLECT_COOLDOWN = timedelta(hours=12)
TAXI_STARS_GOAL = 105
TAXI_STARS_REWARD = 80_000_000_000
taxi_order_locks = set()
taxi_collect_last = {}
TAXI_EVENTS = [
    {"text":"🚦 Пробка","stars":-1},{"text":"🚧 Объехал яму","stars":1},
    {"text":"🎵 Хорошая музыка","stars":1},{"text":"💨 Превысил скорость","stars":-1},
    {"text":"🗣️ Нагрубил","stars":-2},{"text":"🎁 Помог с багажом","stars":2}]
BONUS_MIN = 1_000_000_000
BONUS_MAX = 18_000_000_000
REFERRAL_BONUS = 15_000_000_000
START_BALANCE = 10_000_000_000
BONUS_COOLDOWN = timedelta(minutes=25)
CLICKER_COOLDOWN = timedelta(hours=2)
CLICKER_MAX_CLICKS = 150
CLICKER_REWARD = 100_000_000
SLOT_COOLDOWN = 2
DEFAULT_WARDROBE_SLOTS = 5
ACTIVITY_REWARD = 55_000_000_000
CITIES = {"рублёвка":{"travel_time":40,"name":"Рублёвка"},"лыткарино":{"travel_time":50,"name":"Лыткарино"},
    "арзамас":{"travel_time":35,"name":"Арзамас"},"батырево":{"travel_time":30,"name":"Батырево"},
    "южный":{"travel_time":45,"name":"Южный"},"нижнегородск":{"travel_time":60,"name":"Нижнегородск"}}
RED_NUMBERS = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
BLACK_NUMBERS = {2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35}
DOZEN_1 = set(range(1,13)); DOZEN_2 = set(range(13,25)); DOZEN_3 = set(range(25,37))
drop_data = {"active":False,"city":None,"amount":0,"expires_at":None,"claimed":False,"creator_id":None}
number_games = {}; contest_data = {}; next_contest_id = 1
banned_users = set(); teacher_sessions = {}; dice_games = {}; rebus_sessions = {}
last_slot_time = {}; donation_requests = {}; next_donation_id = 1
avatar_cache = {}; avatar_generation_lock = {}; BOT_STOPPED = {"value":False}
_character_cache = {"img":None,"loaded":False}; pm_states = {}
MARKET_COMMISSION = 0.15
PM_DAILY_LIMIT_SET = 25; PM_DAILY_LIMIT_HOUSE = 30
REBUS_WORDS = [{"word":"КОТ","letters":["К","О","Т"]},{"word":"ДОМ","letters":["Д","О","М"]},
    {"word":"ЛЕС","letters":["Л","Е","С"]},{"word":"ИГРА","letters":["И","Г","Р","А"]},
    {"word":"СТОЛ","letters":["С","Т","О","Л"]},{"word":"ВОДА","letters":["В","О","Д","А"]},
    {"word":"МОРЕ","letters":["М","О","Р","Е"]},{"word":"ГОРА","letters":["Г","О","Р","А"]},
    {"word":"КИНО","letters":["К","И","Н","О"]},{"word":"БАНК","letters":["Б","А","Н","К"]}]
REBUS_BLOCKLIST = {"БИЗ","Я","БОНУС","РАБОТА","ПОМОЩЬ","МЕНЮ","ЗАКУПКИ","КАРТА","НАСТРОЙКИ",
    "НАЗАД","ШКАФ","ПРОМОКОД","ДОНАТ","СТАТА","ТОП","БАНК","СЛОТ","РУЛ","КОСТИ","КЛИКЕР","ТАКСИ"}

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
app = FastAPI()

def get_db_connection():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def column_exists(cursor, t, c):
    cursor.execute(f"PRAGMA table_info({t})")
    return c in [x[1] for x in cursor.fetchall()]

def init_db():
    conn = get_db_connection(); c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, nick TEXT UNIQUE,
        balance INTEGER DEFAULT 0, last_bonus TEXT, referrer_id INTEGER, registered_at TEXT,
        city TEXT DEFAULT 'рублёвка', travel_end_time TEXT, referals_count INTEGER DEFAULT 0,
        is_banned INTEGER DEFAULT 0, wardrobe_slots INTEGER DEFAULT 5, top_visible INTEGER DEFAULT 1,
        username TEXT, taxi_rent_until TEXT, taxi_earnings INTEGER DEFAULT 0,
        total_taxi_rides INTEGER DEFAULT 0, taxi_current_order INTEGER DEFAULT NULL,
        taxi_order_end TEXT, taxi_stars INTEGER DEFAULT 0, taxi_stars_started TEXT,
        taxi_stars_claimed INTEGER DEFAULT 0, taxi_collect_accum INTEGER DEFAULT 0)''')
    for col, ct in [("top_visible","INTEGER DEFAULT 1"),("wardrobe_slots","INTEGER DEFAULT 5"),
        ("username","TEXT"),("taxi_rent_until","TEXT"),("taxi_earnings","INTEGER DEFAULT 0"),
        ("total_taxi_rides","INTEGER DEFAULT 0"),("taxi_current_order","INTEGER DEFAULT NULL"),
        ("taxi_order_end","TEXT"),("taxi_stars","INTEGER DEFAULT 0"),
        ("taxi_stars_started","TEXT"),("taxi_stars_claimed","INTEGER DEFAULT 0"),
        ("taxi_collect_accum","INTEGER DEFAULT 0")]:
        if not column_exists(c,'users',col):
            try: c.execute(f"ALTER TABLE users ADD COLUMN {col} {ct}")
            except: pass
    c.execute('CREATE TABLE IF NOT EXISTS settings (user_id INTEGER PRIMARY KEY, confirm_transfer INTEGER DEFAULT 1)')
    c.execute('CREATE TABLE IF NOT EXISTS clicker (user_id INTEGER PRIMARY KEY, clicks INTEGER DEFAULT 0, last_reset TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS bank (user_id INTEGER PRIMARY KEY, deposit INTEGER DEFAULT 0, deposit_time TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS roulette_images (number INTEGER PRIMARY KEY, file_id TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS promocodes (name TEXT PRIMARY KEY, amount INTEGER, activations_left INTEGER, total_activations INTEGER, creator_id INTEGER, created_at TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS checks (check_id TEXT PRIMARY KEY, amount INTEGER, activations_left INTEGER, total_activations INTEGER, creator_id INTEGER, created_at TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS check_activations (check_id TEXT, user_id INTEGER, PRIMARY KEY (check_id, user_id))')
    c.execute('CREATE TABLE IF NOT EXISTS gifts (gift_id TEXT PRIMARY KEY, amount INTEGER, activations_left INTEGER, creator_id INTEGER, created_at TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS market_items (id INTEGER PRIMARY KEY, name TEXT, price INTEGER, file_id TEXT, created_by INTEGER, created_at TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS donate_items (id INTEGER PRIMARY KEY, name TEXT, file_id TEXT, created_by INTEGER, created_at TEXT)')
    c.execute("CREATE TABLE IF NOT EXISTS houses (id INTEGER PRIMARY KEY, price INTEGER, file_id TEXT, name TEXT DEFAULT '', created_by INTEGER, created_at TEXT)")
    if not column_exists(c,'houses','name'):
        try: c.execute("ALTER TABLE houses ADD COLUMN name TEXT DEFAULT ''")
        except: pass
    c.execute('CREATE TABLE IF NOT EXISTS wardrobe (user_id INTEGER, slot INTEGER, item_type TEXT, item_id INTEGER, item_name TEXT, file_id TEXT, price INTEGER DEFAULT 0, PRIMARY KEY (user_id, slot))')
    for col, ct in [("file_id","TEXT"),("price","INTEGER DEFAULT 0")]:
        if not column_exists(c,'wardrobe',col):
            try: c.execute(f"ALTER TABLE wardrobe ADD COLUMN {col} {ct}")
            except: pass
    c.execute('CREATE TABLE IF NOT EXISTS equipped_outfit (user_id INTEGER PRIMARY KEY, file_id TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS equipped_house (user_id INTEGER PRIMARY KEY, file_id TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS taxi_orders (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, order_type INTEGER, earnings INTEGER DEFAULT 0, completed INTEGER DEFAULT 0, created_at TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS chat_stats (chat_id INTEGER, user_id INTEGER, roul_won INTEGER DEFAULT 0, roul_lost INTEGER DEFAULT 0, dice_won INTEGER DEFAULT 0, dice_lost INTEGER DEFAULT 0, slot_won INTEGER DEFAULT 0, slot_lost INTEGER DEFAULT 0, PRIMARY KEY (chat_id, user_id))')
    c.execute('CREATE TABLE IF NOT EXISTS command_stats (chat_id INTEGER, user_id INTEGER, command TEXT, count INTEGER DEFAULT 0, PRIMARY KEY (chat_id, user_id, command))')
    c.execute('CREATE TABLE IF NOT EXISTS contest_sets (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, price INTEGER DEFAULT 0, file_id TEXT, created_at TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS contest_houses (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, price INTEGER DEFAULT 0, file_id TEXT, created_at TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS pm_items (id INTEGER PRIMARY KEY AUTOINCREMENT, seller_id INTEGER, kind TEXT, item_name TEXT, file_id TEXT, price INTEGER, sold INTEGER DEFAULT 0, created_at TEXT, wardrobe_slot INTEGER DEFAULT NULL)')
    c.execute('CREATE TABLE IF NOT EXISTS pm_daily (kind TEXT PRIMARY KEY, sold_today INTEGER DEFAULT 0, day_start TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS bot_usage (user_id INTEGER PRIMARY KEY, total INTEGER DEFAULT 0, updated_at TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS bot_settings (key TEXT PRIMARY KEY, value TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS top3_payouts (id INTEGER PRIMARY KEY AUTOINCREMENT, week_start TEXT, user_id INTEGER, total INTEGER, amount INTEGER, paid_at TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS top_images (kind TEXT PRIMARY KEY, file_id TEXT)')
    c.execute('''CREATE TABLE IF NOT EXISTS football_bets (id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, fixture_id INTEGER, competition TEXT, home_team TEXT, away_team TEXT,
        pick TEXT, amount INTEGER, coefficient REAL, placed_at TEXT, status TEXT DEFAULT 'pending',
        result TEXT, payout INTEGER DEFAULT 0)''')
    conn.commit(); conn.close()

init_db()

def format_balance(n):
    try: return f"₽{n:,}".replace(",",".")
    except: return f"₽{n}"

def parse_amount(s):
    s = s.lower().strip().replace("ё","е").replace("ë","е")
    s = s.replace("кккк","000000000000").replace("ккк","000000000").replace("кк","000000").replace("к","000")
    return int(s)

def get_full_keyboard():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🎁 бонус")],
        [KeyboardButton(text="📦 меню"),KeyboardButton(text="🛒 закупки")],
        [KeyboardButton(text="🔄"),KeyboardButton(text="помощь")]], resize_keyboard=True)

def get_menu_keyboard():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🎫 промокод"),KeyboardButton(text="💎 донат"),KeyboardButton(text="📦 шкаф")],
        [KeyboardButton(text="💼 работа"),KeyboardButton(text="🗺️ карта"),KeyboardButton(text="🔗 рефералка")],
        [KeyboardButton(text="🏢 бизнес"),KeyboardButton(text="🏦 банк"),KeyboardButton(text="⚙️ настройки")],
        [KeyboardButton(text="⚽ футбол",web_app=WebAppInfo(url=WEBAPP_URL))],
        [KeyboardButton(text="◀️ назад")]], resize_keyboard=True)

def get_shop_keyboard():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="👕 маркет сетов"),KeyboardButton(text="🏠 дом")],
        [KeyboardButton(text="🛒 маркет игроков")],[KeyboardButton(text="◀️ назад")]], resize_keyboard=True)

def get_nick_link(uid, nick): return f"<a href='tg://user?id={uid}'>{nick}</a>"
def is_private(m): return m.chat.type == ChatType.PRIVATE
def is_admin(uid): return uid in OWNERS

async def check_stopped(m):
    if not BOT_STOPPED["value"]: return False
    if m.from_user.id in OWNERS: return False
    await m.answer("⛔ Бот остановлен"); return True

async def check_banned(m):
    uid = m.from_user.id
    if uid in OWNERS: return False
    if uid in banned_users:
        await m.answer("⛔ Ты забанен"); return True
    return False

async def check_subscribed(uid):
    try:
        chat = await bot.get_chat(f"@{CHANNEL_USERNAME}")
        mem = await bot.get_chat_member(chat_id=chat.id, user_id=uid)
        return mem.status in ["member","administrator","creator","restricted"]
    except: return True

async def user_exists(uid):
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE user_id = ?", (uid,))
    r = c.fetchone(); conn.close(); return bool(r)

async def update_username(uid, un):
    if not un: return
    try:
        conn = get_db_connection(); c = conn.cursor()
        c.execute("UPDATE users SET username = ? WHERE user_id = ?", (un.lower().lstrip('@'), uid))
        conn.commit(); conn.close()
    except: pass

def track_command(cid, uid, cmd):
    if not cmd: return
    try:
        conn = get_db_connection(); c = conn.cursor()
        c.execute("INSERT INTO command_stats (chat_id, user_id, command, count) VALUES (?,?,?,1) ON CONFLICT(chat_id,user_id,command) DO UPDATE SET count = count + 1", (cid, uid, cmd.lower()))
        conn.commit(); conn.close()
    except: pass

def _bump_usage(uid):
    if not uid or uid in OWNERS: return
    try:
        conn = get_db_connection(); c = conn.cursor()
        c.execute("INSERT INTO bot_usage (user_id,total,updated_at) VALUES (?,1,?) ON CONFLICT(user_id) DO UPDATE SET total = total + 1, updated_at = excluded.updated_at", (uid, datetime.now().isoformat()))
        conn.commit(); conn.close()
    except: pass

def add_to_wardrobe(c, uid, itype, iid, iname, fid, price):
    c.execute("SELECT wardrobe_slots FROM users WHERE user_id = ?", (uid,))
    row = c.fetchone(); slots = row[0] if row else DEFAULT_WARDROBE_SLOTS
    c.execute("SELECT slot FROM wardrobe WHERE user_id = ?", (uid,))
    used = {r[0] for r in c.fetchall()}
    free = next((s for s in range(1, slots+1) if s not in used), None)
    if free is None:
        free = slots + 1
        c.execute("UPDATE users SET wardrobe_slots = ? WHERE user_id = ?", (free, uid))
    c.execute("INSERT INTO wardrobe (user_id,slot,item_type,item_id,item_name,file_id,price) VALUES (?,?,?,?,?,?,?)",
        (uid, free, itype, iid, iname, fid, price or 0))

class RegStates(StatesGroup):
    waiting_nick = State(); waiting_new_nick = State()
class DonateImageState(StatesGroup):
    waiting_image = State()
class HouseImageState(StatesGroup):
    waiting_image = State()
class BankDepositState(StatesGroup):
    waiting_amount = State()
class PromoCodeState(StatesGroup):
    waiting_input = State()
class TeacherState(StatesGroup):
    waiting_answer = State()
class RebusState(StatesGroup):
    waiting_answer = State()
class PMAddState(StatesGroup):
    waiting_price = State()
class TopPhotoState(StatesGroup):
    waiting_balance = State(); waiting_ref = State()

async def cmd_start(m: Message, state: FSMContext):
    uid = m.from_user.id
    await update_username(uid, m.from_user.username)
    _bump_usage(uid)
    args = m.text.split(); ref = None
    if len(args) > 1:
        a = args[1]
        if a.startswith("gift_"): await handle_gift_activation(m, a); return
        elif a.startswith("check_"): await handle_check_activation(m, a); return
        elif a.startswith("contesthouse_"): await handle_contest_deeplink(m, a.replace("contesthouse_","")); return
        elif a.startswith("contest_"): await handle_contest_deeplink(m, a.replace("contest_","")); return
        elif a.startswith("cs_"): await handle_contest_deeplink(m, a.replace("cs_","")); return
        elif a.startswith("ch_"): await handle_contest_deeplink(m, a.replace("ch_","")); return
        elif a.startswith("ref_"):
            try: ref = int(a.split("_")[1])
            except: pass
    if await user_exists(uid):
        await send_profile(m, uid); return
    if ref: await state.update_data(referrer_id=ref)
    await state.set_state(RegStates.waiting_nick)
    await m.answer("Придумай никнейм:")

@dp.message(RegStates.waiting_nick)
async def process_nick(m: Message, state: FSMContext):
    uid = m.from_user.id; nick = m.text.strip()
    if not nick: await m.answer("Ник не может быть пустым"); return
    un = (m.from_user.username or "").lower().lstrip('@') if m.from_user.username else None
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE nick = ?", (nick,))
    if c.fetchone():
        await m.answer("❌ Ник занят"); conn.close(); return
    data = await state.get_data(); ref = data.get("referrer_id")
    now = datetime.now().isoformat()
    c.execute("INSERT INTO users (user_id,nick,balance,referrer_id,registered_at,city,wardrobe_slots,top_visible,username) VALUES (?,?,?,?,?,?,?,?,?)",
        (uid, nick, START_BALANCE, ref, now, "рублёвка", DEFAULT_WARDROBE_SLOTS, 1, un))
    c.execute("INSERT INTO settings (user_id,confirm_transfer) VALUES (?,1)", (uid,))
    conn.commit()
    if ref:
        c.execute("SELECT balance,nick FROM users WHERE user_id = ?", (ref,))
        r = c.fetchone()
        if r:
            nb = r[0] + REFERRAL_BONUS
            c.execute("UPDATE users SET balance = ?, referals_count = referals_count + 1 WHERE user_id = ?", (nb, ref))
            conn.commit()
            try: await bot.send_message(ref, f"🎉 По твоей ссылке зашёл {nick}!\n+{format_balance(REFERRAL_BONUS)}")
            except: pass
    conn.close(); await state.clear(); await send_profile(m, uid)

@dp.message(F.text.lower() == "📦 меню")
async def menu_cmd(m: Message):
    if not is_private(m): return
    if await check_stopped(m) or await check_banned(m): return
    _bump_usage(m.from_user.id)
    await m.answer("📦 Меню", reply_markup=get_menu_keyboard())

@dp.message(F.text.lower() == "🛒 закупки")
async def shop_cmd(m: Message):
    if not is_private(m): return
    if await check_stopped(m) or await check_banned(m): return
    _bump_usage(m.from_user.id)
    await m.answer("🛒 Закупки", reply_markup=get_shop_keyboard())

@dp.message(F.text.lower() == "◀️ назад")
async def back_cmd(m: Message):
    if not is_private(m): return
    await m.answer("◀️ Назад", reply_markup=get_full_keyboard())

@dp.message(F.text.lower() == "я")
async def me_cmd(m: Message):
    if await check_stopped(m) or await check_banned(m): return
    uid = m.from_user.id
    if not await user_exists(uid):
        await m.answer("Сначала /start"); return
    await update_username(uid, m.from_user.username)
    _bump_usage(uid); await send_profile(m, uid)

@dp.message(F.text.lower() == "🔄")
async def refresh_cmd(m: Message):
    if await check_stopped(m) or await check_banned(m): return
    uid = m.from_user.id
    avatar_cache.pop(uid, None); await send_profile(m, uid)

@dp.message(F.text.lower().in_(["🎁 бонус","бонус"]))
async def bonus_cmd(m: Message):
    if await check_stopped(m) or await check_banned(m): return
    uid = m.from_user.id; _bump_usage(uid)
    if not await check_subscribed(uid):
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="📢 Канал", url=CHANNEL_LINK)],
            [InlineKeyboardButton(text="✅ Проверить", callback_data="check_bonus_sub")]])
        await m.answer(f"❌ Подпишись!\n{CHANNEL_LINK}", reply_markup=kb); return
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT balance,last_bonus FROM users WHERE user_id = ?", (uid,))
    u = c.fetchone(); conn.close()
    if not u: await m.answer("Сначала /start"); return
    bal, lbs = u; now = datetime.now()
    lb = datetime.fromisoformat(lbs) if lbs else None
    if lb and now - lb < BONUS_COOLDOWN:
        rem = BONUS_COOLDOWN - (now - lb)
        await m.answer(f"⏳ Через {rem.seconds//60} мин"); return
    bonus = random.randint(BONUS_MIN, BONUS_MAX); nb = bal + bonus
    conn = get_db_connection(); c = conn.cursor()
    c.execute("UPDATE users SET balance = ?, last_bonus = ? WHERE user_id = ?", (nb, now.isoformat(), uid))
    conn.commit(); conn.close()
    await m.answer(f"✅ Бонус +{format_balance(bonus)}\n💳 {format_balance(nb)}",
        reply_markup=get_full_keyboard() if is_private(m) else None)

@dp.callback_query(F.data == "check_bonus_sub")
async def check_bonus_cb(cb: CallbackQuery):
    if await check_subscribed(cb.from_user.id):
        await cb.message.delete()
        await cb.message.answer("✅ Подписка есть! Пиши бонус")
    else:
        await cb.answer("❌ Не подписан", show_alert=True)

@dp.message(F.text.lower() == "🔗 рефералка")
async def ref_cmd(m: Message):
    if await check_stopped(m) or await check_banned(m): return
    uid = m.from_user.id
    if not await user_exists(uid): await m.answer("Сначала /start"); return
    _bump_usage(uid)
    link = f"https://t.me/{BOT_USERNAME}?start=ref_{uid}"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔗 Поделиться", url=f"https://t.me/share/url?url={link}&text=Играй")],
        [InlineKeyboardButton(text="📋 Скопировать", callback_data="copy_link")]])
    await m.answer(f"🔗 Твоя ссылка:\n\n`{link}`\n\n💰 За реферала: {format_balance(REFERRAL_BONUS)}",
        reply_markup=kb, parse_mode=ParseMode.MARKDOWN)

@dp.callback_query(F.data == "copy_link")
async def copy_link_cb(cb: CallbackQuery):
    await cb.answer(f"Ссылка: https://t.me/{BOT_USERNAME}?start=ref_{cb.from_user.id}", show_alert=True)

RUL_ALIASES = {
    "красное":"кра","красный":"кра","красная":"кра","крас":"кра","кра":"кра",
    "чёрное":"чер","черное":"чер","чёрный":"чер","черный":"чер","чер":"чер","чёр":"чер",
    "чётное":"чет","четное":"чет","чётный":"чет","чет":"чет","чёт":"чет",
    "нечётное":"неч","нечетное":"неч","нечётный":"неч","нечет":"неч","неч":"неч",
    "больше":"бол","бол":"бол","меньше":"мал","мал":"мал",
    "ноль":"0","нуль":"0","зеро":"0","0":"0",
    "1-12":"d1","д1":"d1","13-24":"d2","д2":"d2","25-36":"d3","д3":"d3",
    "ряд1":"r1","ряд2":"r2","ряд3":"r3","r1":"r1","r2":"r2","r3":"r3"}

def _normalize_rul(word):
    w = word.lower().strip()
    if w.isdigit() and 1 <= int(w) <= 36: return w
    if w in RUL_ALIASES: return RUL_ALIASES[w]
    for p in ("столб","столбец","col","с"):
        if w.startswith(p):
            t = w[len(p):]
            if t.isdigit() and 1 <= int(t) <= 12: return f"c{int(t)}"
    return None

def parse_rul_bet(parts):
    if len(parts) < 3: return None, None
    bt = None
    for i in range(1, min(4, len(parts))):
        bt = _normalize_rul(parts[i])
        if bt: break
    if not bt: return None, None
    ams = parts[-1].lower().strip().replace("ё","е").replace("ë","е")
    if ams in ("все","алл","all","всё"): return bt, "ALL"
    try:
        a = parse_amount(ams)
        if a <= 0: return None, None
        return bt, a
    except: return None, None

def _row_numbers(row):
    if row < 1 or row > 3: return set()
    return {n for n in range(1,37) if (n - row) % 3 == 0}

def _col_numbers(col):
    if col < 1 or col > 12: return set()
    return {col*3-2, col*3-1, col*3}

@dp.message(F.text.lower().startswith("рул"))
async def rul_bet(m: Message):
    if await check_stopped(m) or await check_banned(m): return
    if is_private(m):
        await m.answer("Ставки только в чатах"); return
    uid = m.from_user.id; _bump_usage(uid)
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT nick,balance FROM users WHERE user_id = ?", (uid,))
    u = c.fetchone(); conn.close()
    if not u: await m.answer("Сначала /start"); return
    parts = m.text.lower().split()
    if len(parts) < 3: await m.answer("❌ Пример: рулетка чёрное 1000000"); return
    bt, ba = parse_rul_bet(parts)
    if bt is None: await m.answer("❌ Неверный тип/сумма"); return
    if ba == "ALL": ba = u[1]
    if ba <= 0: await m.answer("❌ Ставка > 0"); return
    if u[1] < ba: await m.answer(f"❌ Не хватает. Баланс: {format_balance(u[1])}"); return
    rn = random.randint(0, 36); win = False; wa = 0
    if bt == "кра": win = rn in RED_NUMBERS; wa = ba*2 if win else 0
    elif bt == "чер": win = rn in BLACK_NUMBERS; wa = ba*2 if win else 0
    elif bt == "чет": win = rn != 0 and rn % 2 == 0; wa = ba*2 if win else 0
    elif bt == "неч": win = rn != 0 and rn % 2 == 1; wa = ba*2 if win else 0
    elif bt == "бол": win = 19 <= rn <= 36; wa = ba*2 if win else 0
    elif bt == "мал": win = 1 <= rn <= 18; wa = ba*2 if win else 0
    elif bt == "0": win = rn == 0; wa = ba*36 if win else 0
    elif bt == "d1": win = rn in DOZEN_1; wa = ba*3 if win else 0
    elif bt == "d2": win = rn in DOZEN_2; wa = ba*3 if win else 0
    elif bt == "d3": win = rn in DOZEN_3; wa = ba*3 if win else 0
    elif bt == "r1": win = rn in _row_numbers(1); wa = ba*3 if win else 0
    elif bt == "r2": win = rn in _row_numbers(2); wa = ba*3 if win else 0
    elif bt == "r3": win = rn in _row_numbers(3); wa = ba*3 if win else 0
    elif bt.startswith("c"):
        try: col = int(bt[1:])
        except: col = 0
        nums = _col_numbers(col)
        if nums: win = rn in nums; wa = ba*10 if win else 0
    elif bt.isdigit() and 1 <= int(bt) <= 36:
        win = rn == int(bt); wa = ba*36 if win else 0
    nb = u[1] - ba
    if win: nb += wa
    conn = get_db_connection(); c = conn.cursor()
    c.execute("UPDATE users SET balance = ? WHERE user_id = ?", (nb, uid))
    conn.commit()
    c.execute("SELECT file_id FROM roulette_images WHERE number = ?", (rn,))
    ir = c.fetchone(); conn.close()
    cap = f"{get_nick_link(uid, u[0])}, {'🎉 выиграл ' + format_balance(wa) if win else '❌ проиграл ' + format_balance(ba)}\nБаланс: {format_balance(nb)}"
    if ir and ir[0]: await m.answer_photo(photo=ir[0], caption=cap, parse_mode=ParseMode.HTML)
    else: await m.answer(cap, parse_mode=ParseMode.HTML)

@dp.message(F.text.regexp(r"(?i)^ряд\s*[123]\s+\S+"))
async def row_cmd(m: Message):
    if await check_stopped(m) or await check_banned(m): return
    if is_private(m): await m.answer("Только в чатах"); return
    uid = m.from_user.id; parts = m.text.lower().split()
    row_s = parts[0].replace("ряд","").strip()
    if row_s not in ("1","2","3"): await m.answer("❌ Только ряд1/2/3"); return
    row = int(row_s)
    try: amount = parse_amount(parts[1])
    except: await m.answer("❌ Сумма"); return
    if amount <= 0: return
    _bump_usage(uid)
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT nick,balance FROM users WHERE user_id = ?", (uid,))
    u = c.fetchone(); conn.close()
    if not u: await m.answer("Сначала /start"); return
    if u[1] < amount: await m.answer(f"❌ Баланс: {format_balance(u[1])}"); return
    rn = random.randint(0, 36); win = rn in _row_numbers(row)
    wa = amount*3 if win else 0; nb = u[1] - amount + wa
    conn = get_db_connection(); c = conn.cursor()
    c.execute("UPDATE users SET balance = ? WHERE user_id = ?", (nb, uid))
    conn.commit()
    c.execute("SELECT file_id FROM roulette_images WHERE number = ?", (rn,))
    ir = c.fetchone(); conn.close()
    cap = f"{get_nick_link(uid, u[0])}, РЯД {row} {'🎯 +' + format_balance(wa) if win else '❌ -' + format_balance(amount)}\nБаланс: {format_balance(nb)}"
    if ir and ir[0]: await m.answer_photo(photo=ir[0], caption=cap, parse_mode=ParseMode.HTML)
    else: await m.answer(cap, parse_mode=ParseMode.HTML)

@dp.message(F.text.lower().startswith("слот"))
async def slot_cmd(m: Message):
    if await check_stopped(m) or await check_banned(m): return
    if is_private(m): await m.answer("Только в чатах"); return
    uid = m.from_user.id; _bump_usage(uid)
    if uid in last_slot_time and (datetime.now() - last_slot_time[uid]).total_seconds() < SLOT_COOLDOWN:
        await m.answer("⏳ Подожди"); return
    parts = m.text.split()
    if len(parts) < 2: await m.answer("❌ слот 1000000"); return
    try: amount = parse_amount(parts[1])
    except: await m.answer("❌ Сумма"); return
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT balance,nick FROM users WHERE user_id = ?", (uid,))
    u = c.fetchone(); conn.close()
    if not u: await m.answer("Сначала /start"); return
    if u[0] < amount: await m.answer(f"❌ Баланс: {format_balance(u[0])}"); return
    last_slot_time[uid] = datetime.now()
    sm = await m.answer_dice(emoji="🎰"); await asyncio.sleep(3.1)
    if sm.dice.value in {1,22,43,64}:
        wa = int(amount*14.5); nb = u[0] + wa
        conn = get_db_connection(); c = conn.cursor()
        c.execute("UPDATE users SET balance = ? WHERE user_id = ?", (nb, uid)); conn.commit(); conn.close()
        await m.answer(f"{get_nick_link(uid,u[1])}, 🎉 ДЖЕКПОТ! +{format_balance(wa)}\nБаланс: {format_balance(nb)}", parse_mode=ParseMode.HTML)
    else:
        nb = u[0] - amount
        conn = get_db_connection(); c = conn.cursor()
        c.execute("UPDATE users SET balance = ? WHERE user_id = ?", (nb, uid)); conn.commit(); conn.close()
        await m.answer(f"{get_nick_link(uid,u[1])}, ❌ -{format_balance(amount)}\nБаланс: {format_balance(nb)}", parse_mode=ParseMode.HTML)

async def download_image_by_file_id(fid):
    f = await bot.get_file(fid)
    b = await bot.download_file(f.file_path)
    return io.BytesIO(b.getvalue())

async def get_character_image():
    if _character_cache["loaded"]: return _character_cache["img"]
    _character_cache["loaded"] = True
    for fn in ("character.png","character.jpg","character.webp"):
        if os.path.exists(fn):
            try:
                img = Image.open(fn).convert("RGBA")
                _character_cache["img"] = img; return img
            except: pass
    try:
        timeout = aiohttp.ClientTimeout(total=15, connect=10)
        async with aiohttp.ClientSession(timeout=timeout) as s:
            async with s.get(CHARACTER_IMAGE_URL) as r:
                d = await r.read()
                img = Image.open(io.BytesIO(d)).convert("RGBA")
                _character_cache["img"] = img; return img
    except Exception as e: print(f"char: {e}")
    _character_cache["img"] = None; return None

def remove_white_bg(img, th=230):
    img = img.convert("RGBA"); px = img.load(); w, h = img.size
    for x in range(w):
        for y in range(h):
            r, g, b, a = px[x, y]
            if r > th and g > th and b > th: px[x, y] = (255,255,255,0)
    return img

def crop_to_aspect(img, ts):
    tw, th = ts; tr = tw/th; w, h = img.size; cr = w/h
    if cr > tr:
        nw = int(h*tr); xo = (w-nw)//2; img = img.crop((xo,0,xo+nw,h))
    elif cr < tr:
        nh = int(w/tr); yo = (h-nh)//2; img = img.crop((0,yo,w,yo+nh))
    return img.resize(ts, Image.Resampling.LANCZOS)

def overlay(bg, ov, pos=(0,0)):
    r = bg.copy(); r.paste(ov, pos, ov if ov.mode == 'RGBA' else None); return r

def is_white_bg(img):
    try:
        img = img.convert("RGBA"); w, h = img.size; s = []
        for (px,py) in [(0,0),(w-1,0),(0,h-1),(w-1,h-1),(w//2,0),(w//2,h-1),(0,h//2),(w-1,h//2)]:
            r, g, b, a = img.getpixel((px,py))
            s.append(a < 50 or (r > 230 and g > 230 and b > 230))
        return sum(s) >= len(s)*0.75
    except: return False

async def fid_is_white_bg(fid):
    try:
        d = await download_image_by_file_id(fid)
        return is_white_bg(Image.open(d).convert("RGBA"))
    except: return False

async def create_profile_image(uid):
    if uid not in avatar_generation_lock:
        avatar_generation_lock[uid] = asyncio.Lock()
    async with avatar_generation_lock[uid]:
        if uid in avatar_cache: return avatar_cache[uid]
        conn = get_db_connection(); c = conn.cursor()
        c.execute("SELECT file_id FROM equipped_outfit WHERE user_id = ?", (uid,))
        o = c.fetchone()
        c.execute("SELECT file_id FROM equipped_house WHERE user_id = ?", (uid,))
        h = c.fetchone(); conn.close()
        oi = None; hi = None
        if o and o[0]:
            try: oi = Image.open(await download_image_by_file_id(o[0])).convert("RGBA")
            except: oi = None
        if h and h[0]:
            try: hi = Image.open(await download_image_by_file_id(h[0])).convert("RGBA")
            except: hi = None
        if oi and hi:
            try:
                if is_white_bg(oi): oc = remove_white_bg(oi, 230)
                else: oc = oi
                ts = oc.size; bg = crop_to_aspect(hi, ts)
                comb = overlay(bg, oc, (0,0))
                buf = io.BytesIO(); comb.save(buf, format='PNG'); buf.seek(0)
                rf = BufferedInputFile(buf.getvalue(), filename="profile.png")
                avatar_cache[uid] = rf; return rf
            except: pass
        if oi:
            buf = io.BytesIO(); oi.save(buf, format='PNG'); buf.seek(0)
            rf = BufferedInputFile(buf.getvalue(), filename="profile.png")
            avatar_cache[uid] = rf; return rf
        ch = await get_character_image()
        if ch is None:
            if hi:
                buf = io.BytesIO(); hi.save(buf, format='PNG'); buf.seek(0)
                rf = BufferedInputFile(buf.getvalue(), filename="profile.png")
                avatar_cache[uid] = rf; return rf
            return None
        ts = ch.size
        bg = crop_to_aspect(hi, ts) if hi else Image.new('RGBA', ts, (0,0,0,0))
        cno = remove_white_bg(ch, 230).resize(ts, Image.Resampling.LANCZOS)
        res = overlay(bg, cno, (0,0))
        buf = io.BytesIO(); res.save(buf, format='PNG'); buf.seek(0)
        rf = BufferedInputFile(buf.getvalue(), filename="profile.png")
        avatar_cache[uid] = rf; return rf

async def send_profile(m, uid):
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT nick,balance,city FROM users WHERE user_id = ?", (uid,))
    u = c.fetchone(); conn.close()
    if not u: await m.answer("Сначала /start"); return
    nick, bal, city = u
    cn = CITIES.get(city, {}).get("name", "Рублёвка")
    txt = f"{get_nick_link(uid, nick)} | {format_balance(bal)} | 📍{cn}"
    try:
        img = await create_profile_image(uid)
        if img:
            await m.answer_photo(photo=img, caption=txt, parse_mode=ParseMode.HTML,
                reply_markup=get_full_keyboard() if is_private(m) else None); return
    except Exception as e: print(f"profile: {e}")
    await m.answer(txt, parse_mode=ParseMode.HTML,
        reply_markup=get_full_keyboard() if is_private(m) else None)
@dp.message(Command("удалить"))
async def del_cmd(m: Message, cmd: CommandObject):
    uid = m.from_user.id
    if not is_admin(uid): return
    if (cmd.args or "").strip().lower() not in ("я","me","self"):
        await m.answer("❌ /удалить я"); return
    conn = get_db_connection(); c = conn.cursor()
    c.execute("DELETE FROM equipped_outfit WHERE user_id = ?", (uid,))
    conn.commit(); conn.close()
    avatar_cache.pop(uid, None)
    await m.answer("✅ Снят сет"); await send_profile(m, uid)

@dp.message(Command("удалить_дом_я"))
async def del_house_cmd(m: Message):
    uid = m.from_user.id
    if not is_admin(uid): return
    conn = get_db_connection(); c = conn.cursor()
    c.execute("DELETE FROM equipped_house WHERE user_id = ?", (uid,))
    conn.commit(); conn.close()
    avatar_cache.pop(uid, None)
    await m.answer("✅ Снят дом"); await send_profile(m, uid)

@dp.message(F.text.lower() == "📦 шкаф")
async def wardrobe_menu(m: Message):
    if await check_stopped(m) or await check_banned(m): return
    _bump_usage(m.from_user.id); uid = m.from_user.id
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT wardrobe_slots FROM users WHERE user_id = ?", (uid,))
    sr = c.fetchone()
    if not sr: await m.answer("Сначала /start"); conn.close(); return
    total = max(sr[0], DEFAULT_WARDROBE_SLOTS)
    c.execute("SELECT slot,item_name,item_id,file_id FROM wardrobe WHERE user_id = ? ORDER BY slot", (uid,))
    items = c.fetchall()
    c.execute("SELECT file_id FROM equipped_outfit WHERE user_id = ?", (uid,))
    eq = c.fetchone()
    c.execute("SELECT file_id FROM equipped_house WHERE user_id = ?", (uid,))
    eqh = c.fetchone(); conn.close()
    txt = f"📦 ШКАФ ({len(items)}/{total})\n\n"
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for s in range(1, total+1):
        row = [it for it in items if it[0] == s]
        if row:
            _, name, iid, fid = row[0]
            kb.inline_keyboard.append([InlineKeyboardButton(text=f"👕 {name} (#{s})", callback_data=f"wear_{s}")])
        else:
            kb.inline_keyboard.append([InlineKeyboardButton(text=f"📦 Пусто #{s}", callback_data=f"empty_{s}")])
    if eq and eq[0]:
        kb.inline_keyboard.append([InlineKeyboardButton(text="🎒 Надетый сет в шкаф", callback_data="stash_outfit")])
    if eqh and eqh[0]:
        kb.inline_keyboard.append([InlineKeyboardButton(text="🎒 Надетый дом в шкаф", callback_data="stash_house")])
    kb.inline_keyboard.append([InlineKeyboardButton(text="❌ Закрыть", callback_data="close_wardrobe")])
    await m.answer(txt, parse_mode=ParseMode.HTML, reply_markup=kb)

@dp.message(F.text.lower() == "шкаф")
async def wardrobe_text(m: Message): await wardrobe_menu(m)

@dp.callback_query(F.data.startswith("empty_"))
async def empty_cb(cb: CallbackQuery):
    s = int(cb.data.split("_")[1]); uid = cb.from_user.id
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT file_id FROM equipped_outfit WHERE user_id = ?", (uid,))
    eq = c.fetchone()
    c.execute("SELECT file_id FROM equipped_house WHERE user_id = ?", (uid,))
    eqh = c.fetchone(); conn.close()
    rows = []
    if eq and eq[0]:
        rows.append([InlineKeyboardButton(text="👕 Сет в лот", callback_data=f"stash_outfit_slot_{s}")])
    if eqh and eqh[0]:
        rows.append([InlineKeyboardButton(text="🏠 Дом в лот", callback_data=f"stash_house_slot_{s}")])
    if not rows: await cb.answer("Пусто"); return
    rows.append([InlineKeyboardButton(text="❌ Отмена", callback_data="noop")])
    await cb.message.answer(f"📦 Лот #{s} пуст. Что положить?", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
    await cb.answer()

@dp.callback_query(F.data == "noop")
async def noop_cb(cb: CallbackQuery): await cb.answer()

@dp.callback_query(F.data.startswith("stash_outfit"))
async def stash_outfit(cb: CallbackQuery):
    uid = cb.from_user.id; parts = cb.data.split("_")
    tslot = int(parts[3]) if len(parts) >= 4 and parts[2] == "slot" else None
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT file_id FROM equipped_outfit WHERE user_id = ?", (uid,))
    eq = c.fetchone()
    if not eq or not eq[0]:
        await cb.answer("❌ Нечего класть", show_alert=True); conn.close(); return
    fid = eq[0]
    c.execute("SELECT id,name,price FROM market_items WHERE file_id = ?", (fid,))
    info = c.fetchone()
    if info: iid, iname, iprice = info
    else:
        c.execute("SELECT id,name,price FROM contest_sets WHERE file_id = ?", (fid,))
        ic = c.fetchone()
        if ic: iid, iname, iprice = ic
        else:
            c.execute("SELECT item_id,item_name,price FROM wardrobe WHERE user_id = ? AND file_id = ? LIMIT 1", (uid, fid))
            i2 = c.fetchone()
            iid, iname, iprice = i2 if i2 else (0, "Сет", 0)
    c.execute("SELECT wardrobe_slots FROM users WHERE user_id = ?", (uid,))
    slots = max(c.fetchone()[0], DEFAULT_WARDROBE_SLOTS)
    c.execute("SELECT slot FROM wardrobe WHERE user_id = ?", (uid,))
    used = {r[0] for r in c.fetchall()}
    if tslot:
        if tslot in used:
            await cb.answer("❌ Занято", show_alert=True); conn.close(); return
        s = tslot
    else:
        s = next((x for x in range(1, slots+1) if x not in used), None)
        if s is None:
            s = slots + 1
            c.execute("UPDATE users SET wardrobe_slots = ? WHERE user_id = ?", (s, uid))
    c.execute("INSERT INTO wardrobe (user_id,slot,item_type,item_id,item_name,file_id,price) VALUES (?,?,?,?,?,?,?)",
        (uid, s, 'market', iid, iname, fid, iprice or 0))
    c.execute("DELETE FROM equipped_outfit WHERE user_id = ?", (uid,))
    conn.commit(); conn.close()
    avatar_cache.pop(uid, None)
    await cb.answer(f"✅ '{iname}' в шкафу", show_alert=True)
    try: await cb.message.delete()
    except: pass

@dp.callback_query(F.data.startswith("stash_house"))
async def stash_house(cb: CallbackQuery):
    uid = cb.from_user.id; parts = cb.data.split("_")
    tslot = int(parts[3]) if len(parts) >= 4 and parts[2] == "slot" else None
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT file_id FROM equipped_house WHERE user_id = ?", (uid,))
    eqh = c.fetchone()
    if not eqh or not eqh[0]:
        await cb.answer("❌ Нечего класть", show_alert=True); conn.close(); return
    fid = eqh[0]
    c.execute("SELECT id,name,price FROM houses WHERE file_id = ?", (fid,))
    info = c.fetchone()
    if info: hid, hname, hprice = info
    else:
        c.execute("SELECT id,name,price FROM contest_houses WHERE file_id = ?", (fid,))
        ic = c.fetchone()
        if ic: hid, hname, hprice = ic
        else:
            c.execute("SELECT item_id,item_name,price FROM wardrobe WHERE user_id = ? AND file_id = ? LIMIT 1", (uid, fid))
            i2 = c.fetchone()
            hid, hname, hprice = i2 if i2 else (0, "Дом", 0)
    hname = hname or f"Дом #{hid}"
    c.execute("SELECT wardrobe_slots FROM users WHERE user_id = ?", (uid,))
    slots = max(c.fetchone()[0], DEFAULT_WARDROBE_SLOTS)
    c.execute("SELECT slot FROM wardrobe WHERE user_id = ?", (uid,))
    used = {r[0] for r in c.fetchall()}
    if tslot:
        if tslot in used:
            await cb.answer("❌ Занято", show_alert=True); conn.close(); return
        s = tslot
    else:
        s = next((x for x in range(1, slots+1) if x not in used), None)
        if s is None:
            s = slots + 1
            c.execute("UPDATE users SET wardrobe_slots = ? WHERE user_id = ?", (s, uid))
    c.execute("INSERT INTO wardrobe (user_id,slot,item_type,item_id,item_name,file_id,price) VALUES (?,?,?,?,?,?,?)",
        (uid, s, 'house', hid, hname, fid, hprice or 0))
    c.execute("DELETE FROM equipped_house WHERE user_id = ?", (uid,))
    conn.commit(); conn.close()
    avatar_cache.pop(uid, None)
    await cb.answer(f"✅ {hname} в шкафу", show_alert=True)
    try: await cb.message.delete()
    except: pass

@dp.callback_query(F.data.startswith("wear_"))
async def wear_cb(cb: CallbackQuery):
    uid = cb.from_user.id
    try: slot = int(cb.data.split("_")[1])
    except: await cb.answer("❌"); return
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT item_name,file_id,item_type FROM wardrobe WHERE user_id = ? AND slot = ?", (uid, slot))
    it = c.fetchone()
    if not it:
        await cb.answer("❌ Не найдено", show_alert=True); conn.close(); return
    name, fid, itype = it
    c.execute("SELECT 1 FROM pm_items WHERE seller_id = ? AND wardrobe_slot = ? AND sold = 0", (uid, slot))
    if c.fetchone():
        await cb.answer("❌ Сними лот сначала", show_alert=True); conn.close(); return
    if itype == 'house':
        c.execute("SELECT file_id FROM equipped_outfit WHERE user_id = ?", (uid,))
        o = c.fetchone()
        if o and o[0] and not await fid_is_white_bg(o[0]):
            await cb.answer("❌ Дом только на сет с белым фоном", show_alert=True); conn.close(); return
        c.execute("SELECT file_id FROM equipped_house WHERE user_id = ?", (uid,))
        oh = c.fetchone()
        if oh and oh[0] and oh[0] != fid:
            c.execute("SELECT id,name,price FROM houses WHERE file_id = ?", (oh[0],))
            oi = c.fetchone()
            if oi: ohid, ohname, ohprice = oi
            else:
                c.execute("SELECT id,name,price FROM contest_houses WHERE file_id = ?", (oh[0],))
                oic = c.fetchone()
                ohid, ohname, ohprice = oic if oic else (0, "Дом", 0)
            ohname = ohname or f"Дом #{ohid}"
            c.execute("SELECT wardrobe_slots FROM users WHERE user_id = ?", (uid,))
            hs = max(c.fetchone()[0], DEFAULT_WARDROBE_SLOTS)
            c.execute("SELECT slot FROM wardrobe WHERE user_id = ?", (uid,))
            hu = {r[0] for r in c.fetchall()}
            hf = next((x for x in range(1, hs+1) if x not in hu), None)
            if hf is None:
                hf = hs + 1
                c.execute("UPDATE users SET wardrobe_slots = ? WHERE user_id = ?", (hf, uid))
            c.execute("INSERT INTO wardrobe (user_id,slot,item_type,item_id,item_name,file_id,price) VALUES (?,?,?,?,?,?,?)",
                (uid, hf, 'house', ohid, ohname, oh[0], ohprice or 0))
        c.execute("INSERT OR REPLACE INTO equipped_house (user_id,file_id) VALUES (?,?)", (uid, fid))
        c.execute("DELETE FROM wardrobe WHERE user_id = ? AND slot = ?", (uid, slot))
        conn.commit(); conn.close(); avatar_cache.pop(uid, None)
        await cb.answer(f"✅ Надел {name}", show_alert=True)
        try: await cb.message.delete()
        except: pass
        await wardrobe_menu(cb.message); return
    c.execute("SELECT file_id FROM equipped_outfit WHERE user_id = ?", (uid,))
    ce = c.fetchone()
    if ce and ce[0] and ce[0] != fid:
        c.execute("SELECT id,name,price FROM market_items WHERE file_id = ?", (ce[0],))
        oi = c.fetchone()
        if oi: oid, oname, oprice = oi
        else:
            c.execute("SELECT id,name,price FROM contest_sets WHERE file_id = ?", (ce[0],))
            oc = c.fetchone()
            if oc: oid, oname, oprice = oc
            else:
                c.execute("SELECT item_id,item_name,price FROM wardrobe WHERE user_id = ? AND file_id = ? LIMIT 1", (uid, ce[0]))
                o = c.fetchone()
                oid, oname, oprice = o if o else (0, "Сет", 0)
        c.execute("SELECT wardrobe_slots FROM users WHERE user_id = ?", (uid,))
        slots = max(c.fetchone()[0], DEFAULT_WARDROBE_SLOTS)
        c.execute("SELECT slot FROM wardrobe WHERE user_id = ?", (uid,))
        used = {r[0] for r in c.fetchall()}
        fs = next((s for s in range(1, slots+1) if s not in used and s != slot), None)
        if fs is None:
            fs = slots + 1
            c.execute("UPDATE users SET wardrobe_slots = ? WHERE user_id = ?", (fs, uid))
        c.execute("INSERT INTO wardrobe (user_id,slot,item_type,item_id,item_name,file_id,price) VALUES (?,?,?,?,?,?,?)",
            (uid, fs, 'market', oid, oname, ce[0], oprice or 0))
        if not await fid_is_white_bg(fid):
            c.execute("SELECT file_id FROM equipped_house WHERE user_id = ?", (uid,))
            eh = c.fetchone()
            if eh and eh[0]:
                c.execute("SELECT id,name,price FROM houses WHERE file_id = ?", (eh[0],))
                hi = c.fetchone()
                if hi: hhid, hname2, hprice = hi
                else:
                    c.execute("SELECT id,name,price FROM contest_houses WHERE file_id = ?", (eh[0],))
                    hic = c.fetchone()
                    hhid, hname2, hprice = hic if hic else (0, "Дом", 0)
                hname2 = hname2 or f"Дом #{hhid}"
                c.execute("SELECT wardrobe_slots FROM users WHERE user_id = ?", (uid,))
                hs = max(c.fetchone()[0], DEFAULT_WARDROBE_SLOTS)
                c.execute("SELECT slot FROM wardrobe WHERE user_id = ?", (uid,))
                hu = {r[0] for r in c.fetchall()}
                hf = next((s for s in range(1, hs+1) if s not in hu), None)
                if hf is None:
                    hf = hs + 1
                    c.execute("UPDATE users SET wardrobe_slots = ? WHERE user_id = ?", (hf, uid))
                c.execute("INSERT INTO wardrobe (user_id,slot,item_type,item_id,item_name,file_id,price) VALUES (?,?,?,?,?,?,?)",
                    (uid, hf, 'house', hhid, hname2, eh[0], hprice or 0))
                c.execute("DELETE FROM equipped_house WHERE user_id = ?", (uid,))
    c.execute("INSERT OR REPLACE INTO equipped_outfit (user_id,file_id) VALUES (?,?)", (uid, fid))
    c.execute("DELETE FROM wardrobe WHERE user_id = ? AND slot = ?", (uid, slot))
    conn.commit(); conn.close(); avatar_cache.pop(uid, None)
    await cb.answer(f"✅ Надел {name}", show_alert=True)
    try: await cb.message.delete()
    except: pass
    await wardrobe_menu(cb.message)

@dp.callback_query(F.data == "close_wardrobe")
async def close_wd(cb: CallbackQuery):
    await cb.message.delete(); await cb.answer()

@dp.message(F.text.lower() == "продажа")
async def sale_cmd(m: Message):
    if await check_stopped(m) or await check_banned(m): return
    uid = m.from_user.id
    if not await user_exists(uid): await m.answer("Сначала /start"); return
    _bump_usage(uid)
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT slot,item_name,price FROM wardrobe WHERE user_id = ?", (uid,))
    items = c.fetchall(); conn.close()
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for s, name, price in items:
        kb.inline_keyboard.append([InlineKeyboardButton(text=f"🎁 {name} — {format_balance(int((price or 0)*0.35))}", callback_data=f"sell_{s}")])
    if not kb.inline_keyboard: await m.answer("❌ Нечего продавать"); return
    kb.inline_keyboard.append([InlineKeyboardButton(text="❌ Закрыть", callback_data="close_sale")])
    await m.answer("💸 Что продать? (35%)", reply_markup=kb)

@dp.callback_query(F.data.startswith("sell_"))
async def sell_cb(cb: CallbackQuery):
    uid = cb.from_user.id; s = int(cb.data.split("_")[1])
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT item_name,price FROM wardrobe WHERE user_id = ? AND slot = ?", (uid, s))
    row = c.fetchone()
    if not row:
        await cb.answer("❌", show_alert=True); conn.close(); return
    name, price = row; sp = int((price or 0)*0.35)
    c.execute("DELETE FROM pm_items WHERE seller_id = ? AND wardrobe_slot = ? AND sold = 0", (uid, s))
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (sp, uid))
    c.execute("DELETE FROM wardrobe WHERE user_id = ? AND slot = ?", (uid, s))
    conn.commit(); conn.close()
    await cb.answer(f"✅ +{format_balance(sp)}", show_alert=True)
    try: await cb.message.delete()
    except: pass

@dp.callback_query(F.data == "close_sale")
async def close_sale_cb(cb: CallbackQuery):
    await cb.message.delete(); await cb.answer()

def get_market_items():
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT id,name,price,file_id FROM market_items ORDER BY id")
    r = c.fetchall(); conn.close(); return r

def get_houses():
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT id,price,file_id,name FROM houses ORDER BY id")
    r = c.fetchall(); conn.close(); return r

@dp.message(Command("добавить_сет"))
async def add_set_cmd(m: Message):
    if not is_admin(m.from_user.id): return
    if not m.reply_to_message or not m.reply_to_message.photo:
        await m.answer("❌ Ответь на фото: /добавить_сет 1 5000000000 Название"); return
    args = m.text.split(maxsplit=3)
    if len(args) < 4: await m.answer("❌ /добавить_сет [id] [цена] [название]"); return
    try: iid = int(args[1]); price = parse_amount(args[2]); name = args[3].strip("'\"")
    except Exception as e: await m.answer(f"❌ {e}"); return
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT MAX(id) FROM market_items")
    mx = c.fetchone()[0] or 0
    if iid != mx + 1:
        await m.answer(f"❌ ID должен быть {mx + 1}"); conn.close(); return
    fid = m.reply_to_message.photo[-1].file_id
    c.execute("INSERT INTO market_items (id,name,price,file_id,created_by,created_at) VALUES (?,?,?,?,?,?)",
        (iid, name, price, fid, m.from_user.id, datetime.now().isoformat()))
    conn.commit(); conn.close()
    await m.answer(f"✅ Сет #{iid}: {name} — {format_balance(price)}")

@dp.message(F.text.lower() == "👕 маркет сетов")
async def market_cmd(m: Message):
    if await check_stopped(m) or await check_banned(m): return
    _bump_usage(m.from_user.id)
    items = get_market_items()
    if not items: await m.answer("👕 Маркет пуст"); return
    await show_market(m, 0, items)

def market_kb(i, total, iid, price):
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    nav = []
    if i > 0: nav.append(InlineKeyboardButton(text="◀️", callback_data=f"mp_{i}"))
    if i < total-1: nav.append(InlineKeyboardButton(text="▶️", callback_data=f"mn_{i}"))
    if nav: kb.inline_keyboard.append(nav)
    kb.inline_keyboard.append([InlineKeyboardButton(text="💰 Купить", callback_data=f"mbuy_{iid}")])
    kb.inline_keyboard.append([InlineKeyboardButton(text="❌ Закрыть", callback_data="close_market")])
    return kb

async def show_market(m, i, items):
    if i < 0: i = 0
    if i >= len(items): i = len(items)-1
    iid, name, price, fid = items[i]
    await m.answer_photo(photo=fid, caption=f"👕 {name}\n💰 {format_balance(price)}",
        reply_markup=market_kb(i, len(items), iid, price))

@dp.callback_query(F.data.regexp(r"^mp_\d+$"))
async def mkt_prev(cb: CallbackQuery):
    i = int(cb.data.split("_")[1]); items = get_market_items()
    ni = max(0, i-1); iid, name, price, fid = items[ni]
    try:
        await cb.message.edit_media(media=InputMediaPhoto(media=fid, caption=f"👕 {name}\n💰 {format_balance(price)}"),
            reply_markup=market_kb(ni, len(items), iid, price))
    except: pass
    await cb.answer()

@dp.callback_query(F.data.regexp(r"^mn_\d+$"))
async def mkt_next(cb: CallbackQuery):
    i = int(cb.data.split("_")[1]); items = get_market_items()
    ni = min(len(items)-1, i+1); iid, name, price, fid = items[ni]
    try:
        await cb.message.edit_media(media=InputMediaPhoto(media=fid, caption=f"👕 {name}\n💰 {format_balance(price)}"),
            reply_markup=market_kb(ni, len(items), iid, price))
    except: pass
    await cb.answer()

@dp.callback_query(F.data.startswith("mbuy_"))
async def mkt_buy(cb: CallbackQuery):
    uid = cb.from_user.id; iid = int(cb.data.split("_")[1])
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id = ?", (uid,))
    u = c.fetchone()
    if not u: await cb.answer("Сначала /start", show_alert=True); conn.close(); return
    c.execute("SELECT name,price,file_id FROM market_items WHERE id = ?", (iid,))
    it = c.fetchone()
    if not it: await cb.answer("Не найден", show_alert=True); conn.close(); return
    name, price, fid = it
    if u[0] < price:
        await cb.answer(f"❌ Нужно {format_balance(price)}", show_alert=True); conn.close(); return
    nb = u[0] - price
    c.execute("UPDATE users SET balance = ? WHERE user_id = ?", (nb, uid))
    add_to_wardrobe(c, uid, 'market', iid, name, fid, price)
    conn.commit(); conn.close(); avatar_cache.pop(uid, None)
    await cb.answer("✅ Куплено!", show_alert=True)
    try: await cb.message.delete()
    except: pass

@dp.callback_query(F.data == "close_market")
async def mkt_close(cb: CallbackQuery):
    await cb.message.delete(); await cb.answer()

@dp.message(Command("удалить_маркет"))
async def del_market(m: Message):
    if not is_admin(m.from_user.id): return
    args = m.text.split()
    if len(args) < 2: return
    try: iid = int(args[1])
    except: return
    conn = get_db_connection(); c = conn.cursor()
    c.execute("DELETE FROM market_items WHERE id = ?", (iid,))
    conn.commit(); conn.close()
    await m.answer(f"✅ #{iid} удалён")

@dp.message(Command("изменить_цену"))
async def ch_price(m: Message):
    if not is_admin(m.from_user.id): return
    args = m.text.split()
    if len(args) < 3: return
    try: iid = int(args[1]); price = parse_amount(args[2])
    except: return
    conn = get_db_connection(); c = conn.cursor()
    c.execute("UPDATE market_items SET price = ? WHERE id = ?", (price, iid))
    conn.commit(); conn.close()
    await m.answer(f"✅ #{iid} → {format_balance(price)}")

@dp.message(F.text.lower() == "🏠 дом")
async def house_menu(m: Message):
    if await check_stopped(m) or await check_banned(m): return
    _bump_usage(m.from_user.id); uid = m.from_user.id
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT file_id FROM equipped_house WHERE user_id = ?", (uid,))
    r = c.fetchone(); conn.close()
    if r and r[0]:
        hfid = r[0]
        conn = get_db_connection(); c = conn.cursor()
        c.execute("SELECT price,name FROM houses WHERE file_id = ?", (hfid,))
        hd = c.fetchone(); conn.close()
        price = hd[0] if hd else 0; hname = hd[1] if hd and hd[1] else "Мой дом"
        sp = int(price*0.35)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💰 Продать дом", callback_data=f"shsell_{hfid[:10]}")],
            [InlineKeyboardButton(text="🏠 Магазин", callback_data="hshop")],
            [InlineKeyboardButton(text="❌ Закрыть", callback_data="close_house")]])
        await m.answer_photo(photo=hfid, caption=f"🏠 {hname}\n💰 Куплен: {format_balance(price)}\n💸 Продать: {format_balance(sp)}", reply_markup=kb)
    else: await show_hshop(m, 0)

def house_kb(i, total, hid):
    kb = InlineKeyboardMarkup(inline_keyboard=[]); nav = []
    if i > 0: nav.append(InlineKeyboardButton(text="◀️", callback_data=f"hp_{i}"))
    if i < total-1: nav.append(InlineKeyboardButton(text="▶️", callback_data=f"hn_{i}"))
    if nav: kb.inline_keyboard.append(nav)
    kb.inline_keyboard.append([InlineKeyboardButton(text="💰 Купить", callback_data=f"hbuy_{hid}")])
    kb.inline_keyboard.append([InlineKeyboardButton(text="❌ Закрыть", callback_data="close_house")])
    return kb

async def show_hshop(m, i, edit=False):
    items = get_houses()
    if not items: await m.answer("🏠 Магазин пуст"); return
    if i < 0: i = 0
    if i >= len(items): i = len(items)-1
    hid, price, fid, hname = items[i]
    cap = f"🏠 ДОМ #{hid}" + (f" — {hname}" if hname else "") + f"\n💰 {format_balance(price)}"
    kb = house_kb(i, len(items), hid)
    if edit:
        try: await m.edit_media(InputMediaPhoto(media=fid, caption=cap), reply_markup=kb)
        except: await m.edit_caption(caption=cap, reply_markup=kb)
    else: await m.answer_photo(photo=fid, caption=cap, reply_markup=kb)

@dp.callback_query(F.data == "hshop")
async def hshop_cb(cb: CallbackQuery):
    await show_hshop(cb.message, 0); await cb.answer()

@dp.callback_query(F.data.regexp(r"^hp_\d+$"))
async def hp_cb(cb: CallbackQuery):
    await show_hshop(cb.message, int(cb.data.split("_")[1])-1, True); await cb.answer()

@dp.callback_query(F.data.regexp(r"^hn_\d+$"))
async def hn_cb(cb: CallbackQuery):
    await show_hshop(cb.message, int(cb.data.split("_")[1])+1, True); await cb.answer()

@dp.callback_query(F.data.startswith("hbuy_"))
async def hbuy_cb(cb: CallbackQuery):
    uid = cb.from_user.id; hid = int(cb.data.split("_")[1])
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id = ?", (uid,))
    u = c.fetchone()
    if not u: await cb.answer("Сначала /start", show_alert=True); conn.close(); return
    c.execute("SELECT price,file_id,name FROM houses WHERE id = ?", (hid,))
    h = c.fetchone()
    if not h: await cb.answer("Не найден", show_alert=True); conn.close(); return
    price, fid, hname = h
    if u[0] < price:
        await cb.answer(f"❌ Нужно {format_balance(price)}", show_alert=True); conn.close(); return
    nb = u[0] - price; dn = hname or f"Дом #{hid}"
    c.execute("UPDATE users SET balance = ? WHERE user_id = ?", (nb, uid))
    add_to_wardrobe(c, uid, 'house', hid, dn, fid, price)
    conn.commit(); conn.close(); avatar_cache.pop(uid, None)
    await cb.answer("✅ Куплено!", show_alert=True)
    try: await cb.message.delete()
    except: pass

@dp.callback_query(F.data.startswith("shsell_"))
async def shsell_cb(cb: CallbackQuery):
    uid = cb.from_user.id
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT file_id FROM equipped_house WHERE user_id = ?", (uid,))
    ch = c.fetchone()
    if not ch or not ch[0]: await cb.answer("❌ Нет дома", show_alert=True); conn.close(); return
    c.execute("SELECT price FROM houses WHERE file_id = ?", (ch[0],))
    hd = c.fetchone(); sp = int((hd[0] if hd else 0)*0.35)
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (sp, uid))
    c.execute("DELETE FROM equipped_house WHERE user_id = ?", (uid,))
    conn.commit(); conn.close(); avatar_cache.pop(uid, None)
    await cb.answer(f"✅ +{format_balance(sp)}", show_alert=True)
    try: await cb.message.delete()
    except: pass

@dp.callback_query(F.data == "close_house")
async def close_h_cb(cb: CallbackQuery):
    await cb.message.delete(); await cb.answer()

@dp.message(Command("дом"))
async def add_house_cmd(m: Message, state: FSMContext):
    if not is_admin(m.from_user.id): return
    args = m.text.split(maxsplit=3)
    if len(args) < 3: await m.answer("❌ /дом [id] [цена] [название]"); return
    try:
        hid = int(args[1]); price = parse_amount(args[2])
        name = args[3].strip("'\"") if len(args) >= 4 else ""
    except Exception as e: await m.answer(f"❌ {e}"); return
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT MAX(id) FROM houses")
    mx = c.fetchone()[0] or 0; conn.close()
    if hid != mx+1: await m.answer(f"❌ ID должен быть {mx+1}"); return
    await state.update_data(hid=hid, price=price, hname=name)
    await state.set_state(HouseImageState.waiting_image)
    await m.answer(f"📸 Фото дома #{hid}")

@dp.message(HouseImageState.waiting_image)
async def save_house_img(m: Message, state: FSMContext):
    if not m.photo: await m.answer("❌ Фото"); return
    d = await state.get_data(); fid = m.photo[-1].file_id
    conn = get_db_connection(); c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO houses (id,price,file_id,name,created_by,created_at) VALUES (?,?,?,?,?,?)",
        (d["hid"], d["price"], fid, d.get("hname",""), m.from_user.id, datetime.now().isoformat()))
    conn.commit(); conn.close(); await state.clear()
    await m.answer(f"✅ Дом #{d['hid']} добавлен")

@dp.message(Command("удалить_дом"))
async def del_house_cmd(m: Message):
    if not is_admin(m.from_user.id): return
    args = m.text.split()
    if len(args) < 2: return
    try: hid = int(args[1])
    except: return
    conn = get_db_connection(); c = conn.cursor()
    c.execute("DELETE FROM houses WHERE id = ?", (hid,))
    conn.commit(); conn.close()
    await m.answer(f"✅ #{hid} удалён")

@dp.message(Command("изменить_цену_дома"))
async def ch_hprice(m: Message, cmd: CommandObject):
    if not is_admin(m.from_user.id): return
    args = (cmd.args or "").split()
    if len(args) < 2: return
    try: hid = int(args[0]); price = parse_amount(args[1])
    except: return
    conn = get_db_connection(); c = conn.cursor()
    c.execute("UPDATE houses SET price = ? WHERE id = ?", (price, hid))
    conn.commit(); conn.close()
    await m.answer(f"✅ #{hid} → {format_balance(price)}")

def pm_kb():
    sl, hl = pm_limits()
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"👕 Сеты ({sl}/{PM_DAILY_LIMIT_SET})", callback_data="pm_sets_0")],
        [InlineKeyboardButton(text=f"🏠 Дома ({hl}/{PM_DAILY_LIMIT_HOUSE})", callback_data="pm_houses_0")],
        [InlineKeyboardButton(text="➕ Продать сет", callback_data="pm_add_set")],
        [InlineKeyboardButton(text="➕ Продать дом", callback_data="pm_add_house")],
        [InlineKeyboardButton(text="📦 Мои лоты", callback_data="pm_mylots")],
        [InlineKeyboardButton(text="❌ Закрыть", callback_data="close_pm")]])

def pm_limits():
    conn = get_db_connection(); c = conn.cursor(); now = datetime.now()
    for kind in ("set","house"):
        c.execute("SELECT sold_today,day_start FROM pm_daily WHERE kind = ?", (kind,))
        row = c.fetchone()
        if not row:
            c.execute("INSERT INTO pm_daily (kind,sold_today,day_start) VALUES (?,0,?)", (kind, now.isoformat()))
        else:
            try: ds = datetime.fromisoformat(row[1])
            except: ds = None
            if ds is None or (now - ds) >= timedelta(hours=24):
                c.execute("UPDATE pm_daily SET sold_today = 0, day_start = ? WHERE kind = ?", (now.isoformat(), kind))
    conn.commit()
    c.execute("SELECT kind,sold_today FROM pm_daily")
    r = {x[0]: x[1] for x in c.fetchall()}; conn.close()
    return (max(0, PM_DAILY_LIMIT_SET - int(r.get("set",0))),
            max(0, PM_DAILY_LIMIT_HOUSE - int(r.get("house",0))))

def pm_inc(kind):
    conn = get_db_connection(); c = conn.cursor()
    c.execute("UPDATE pm_daily SET sold_today = sold_today + 1 WHERE kind = ?", (kind,))
    conn.commit(); conn.close()

@dp.message(F.text.lower() == "🛒 маркет игроков")
async def pm_cmd(m: Message):
    if await check_stopped(m) or await check_banned(m): return
    uid = m.from_user.id
    if not await user_exists(uid): await m.answer("Сначала /start"); return
    _bump_usage(uid)
    try: await m.answer_photo(photo=PM_IMAGE_URL, caption="🛒 МАРКЕТ ИГРОКОВ", reply_markup=pm_kb())
    except: await m.answer("🛒 МАРКЕТ ИГРОКОВ", reply_markup=pm_kb())

@dp.callback_query(F.data == "close_pm")
async def close_pm_cb(cb: CallbackQuery):
    try: await cb.message.delete()
    except: pass
    await cb.answer()

async def pm_show_list(m, kind, page, edit=False):
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT id,seller_id,item_name,file_id,price FROM pm_items WHERE kind = ? AND sold = 0 AND wardrobe_slot IS NOT NULL ORDER BY id DESC", (kind,))
    rows_all = c.fetchall()
    rows = []
    for r in rows_all:
        c.execute("SELECT 1 FROM wardrobe w JOIN pm_items p ON p.seller_id = w.user_id AND p.wardrobe_slot = w.slot WHERE p.id = ?", (r[0],))
        if c.fetchone(): rows.append(r)
    conn.close()
    if not rows:
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="pm_back")]])
        if edit:
            try: await m.edit_caption(caption="🛒 Нет лотов", reply_markup=kb)
            except: pass
        else: await m.answer("🛒 Нет лотов", reply_markup=kb)
        return
    total = len(rows)
    if page < 0: page = 0
    if page >= total: page = total-1
    lot_id, seller_id, name, fid, price = rows[page]
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT nick FROM users WHERE user_id = ?", (seller_id,))
    sr = c.fetchone(); conn.close()
    sn = sr[0] if sr else str(seller_id)
    cap = f"{'👕' if kind == 'set' else '🏠'} {name}\n💰 {format_balance(price)}\n👤 {get_nick_link(seller_id, sn)}\n📄 {page+1}/{total}"
    kb_rows = []; nav = []
    if page > 0: nav.append(InlineKeyboardButton(text="◀️", callback_data=f"pm_{kind}s_{page-1}"))
    if page < total-1: nav.append(InlineKeyboardButton(text="▶️", callback_data=f"pm_{kind}s_{page+1}"))
    if nav: kb_rows.append(nav)
    kb_rows.append([InlineKeyboardButton(text="💰 Купить", callback_data=f"pm_buy_{lot_id}")])
    kb_rows.append([InlineKeyboardButton(text="◀️ Назад", callback_data="pm_back")])
    kb = InlineKeyboardMarkup(inline_keyboard=kb_rows)
    if edit and fid:
        try: await m.edit_media(InputMediaPhoto(media=fid, caption=cap, parse_mode=ParseMode.HTML), reply_markup=kb); return
        except: pass
    if fid: await m.answer_photo(photo=fid, caption=cap, parse_mode=ParseMode.HTML, reply_markup=kb)
    else: await m.answer(cap, parse_mode=ParseMode.HTML, reply_markup=kb)

@dp.callback_query(F.data == "pm_back")
async def pm_back_cb(cb: CallbackQuery):
    try: await cb.message.delete()
    except: pass
    await cb.message.answer("🛒 МАРКЕТ ИГРОКОВ", reply_markup=pm_kb())
    await cb.answer()

@dp.callback_query(F.data.startswith("pm_sets_"))
async def pm_sets_cb(cb: CallbackQuery):
    try: await cb.message.delete()
    except: pass
    await pm_show_list(cb.message, "set", int(cb.data.split("_")[2]))
    await cb.answer()

@dp.callback_query(F.data.startswith("pm_houses_"))
async def pm_houses_cb(cb: CallbackQuery):
    try: await cb.message.delete()
    except: pass
    await pm_show_list(cb.message, "house", int(cb.data.split("_")[2]))
    await cb.answer()

async def pm_picker(cb: CallbackQuery, kind):
    uid = cb.from_user.id
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT slot,item_name,item_type FROM wardrobe WHERE user_id = ? ORDER BY slot", (uid,))
    rows = c.fetchall()
    c.execute("SELECT wardrobe_slot FROM pm_items WHERE seller_id = ? AND sold = 0 AND wardrobe_slot IS NOT NULL", (uid,))
    used = {r[0] for r in c.fetchall()}; conn.close()
    kb_rows = []
    for s, name, it in rows:
        if s in used: continue
        if kind == "house" and it != 'house': continue
        if kind == "set" and it == 'house': continue
        emoji = "🏠" if it == 'house' else "👕"
        kb_rows.append([InlineKeyboardButton(text=f"{emoji} {name} (#{s})", callback_data=f"pm_pick_{kind}_{s}")])
    kb_rows.append([InlineKeyboardButton(text="❌ Отмена", callback_data="pm_back")])
    if len(kb_rows) == 1:
        await cb.answer("Нет предметов", show_alert=True); return
    title = "👕 Выбери СЕТ:" if kind == "set" else "🏠 Выбери ДОМ:"
    await cb.message.answer(title, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows))

@dp.callback_query(F.data == "pm_add_set")
async def pm_add_set_cb(cb: CallbackQuery, state: FSMContext):
    await pm_picker(cb, "set"); await cb.answer()

@dp.callback_query(F.data == "pm_add_house")
async def pm_add_house_cb(cb: CallbackQuery, state: FSMContext):
    await pm_picker(cb, "house"); await cb.answer()

@dp.callback_query(F.data.startswith("pm_pick_"))
async def pm_pick_cb(cb: CallbackQuery, state: FSMContext):
    parts = cb.data.split("_"); kind = parts[2]; s = int(parts[3])
    uid = cb.from_user.id
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT item_name,file_id,price FROM wardrobe WHERE user_id = ? AND slot = ?", (uid, s))
    row = c.fetchone()
    if not row: await cb.answer("❌", show_alert=True); conn.close(); return
    name, fid, _ = row; conn.close()
    pm_states[uid] = {"kind": kind, "slot": s, "name": name, "file_id": fid}
    await cb.message.answer(f"{name}\n\n💰 Напиши цену:")
    await state.set_state(PMAddState.waiting_price)
    await cb.answer()

@dp.message(PMAddState.waiting_price)
async def pm_price_msg(m: Message, state: FSMContext):
    uid = m.from_user.id; st = pm_states.get(uid)
    if not st: await state.clear(); return
    try:
        price = parse_amount(m.text.strip())
        if price <= 0: raise ValueError
    except: await m.answer("❌ Цена"); return
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT 1 FROM wardrobe WHERE user_id = ? AND slot = ?", (uid, st["slot"]))
    if not c.fetchone():
        await m.answer("❌ Предмет исчез"); conn.close(); pm_states.pop(uid, None); await state.clear(); return
    c.execute("INSERT INTO pm_items (seller_id,kind,item_name,file_id,price,created_at,wardrobe_slot) VALUES (?,?,?,?,?,?,?)",
        (uid, st["kind"], st["name"], st["file_id"], price, datetime.now().isoformat(), st["slot"]))
    conn.commit(); conn.close()
    pm_states.pop(uid, None); await state.clear()
    await m.answer(f"✅ Лот: {st['name']} за {format_balance(price)}")
    await m.answer("🛒 МАРКЕТ ИГРОКОВ", reply_markup=pm_kb())

@dp.callback_query(F.data.startswith("pm_buy_"))
async def pm_buy_cb(cb: CallbackQuery):
    lot_id = int(cb.data.split("_")[2]); buyer_id = cb.from_user.id
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT seller_id,kind,item_name,file_id,price,sold,wardrobe_slot FROM pm_items WHERE id = ?", (lot_id,))
    row = c.fetchone()
    if not row: await cb.answer("❌ Не найден", show_alert=True); conn.close(); return
    seller_id, kind, name, fid, price, sold, wslot = row
    if sold: await cb.answer("❌ Продан", show_alert=True); conn.close(); return
    if seller_id == buyer_id: await cb.answer("❌ Твой лот", show_alert=True); conn.close(); return
    if wslot is not None:
        c.execute("SELECT 1 FROM wardrobe WHERE user_id = ? AND slot = ?", (seller_id, wslot))
        if not c.fetchone():
            c.execute("UPDATE pm_items SET sold = 1 WHERE id = ?", (lot_id,))
            conn.commit(); conn.close(); await cb.answer("❌ Недоступен", show_alert=True); return
    sl, hl = pm_limits()
    if kind == "set" and sl <= 0: await cb.answer("❌ Лимит сетов", show_alert=True); conn.close(); return
    if kind == "house" and hl <= 0: await cb.answer("❌ Лимит домов", show_alert=True); conn.close(); return
    c.execute("SELECT balance FROM users WHERE user_id = ?", (buyer_id,))
    b = c.fetchone()
    if not b: await cb.answer("Сначала /start", show_alert=True); conn.close(); return
    if b[0] < price: await cb.answer(f"❌ Нужно {format_balance(price)}", show_alert=True); conn.close(); return
    comm = int(price*MARKET_COMMISSION); sg = price - comm
    c.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (price, buyer_id))
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (sg, seller_id))
    c.execute("UPDATE pm_items SET sold = 1 WHERE id = ?", (lot_id,))
    if wslot is not None:
        c.execute("DELETE FROM wardrobe WHERE user_id = ? AND slot = ?", (seller_id, wslot))
    itype = 'market' if kind == 'set' else 'house'
    add_to_wardrobe(c, buyer_id, itype, lot_id, name, fid, price)
    conn.commit(); conn.close(); pm_inc(kind); avatar_cache.pop(buyer_id, None)
    await cb.answer("✅ Куплено!", show_alert=True)
    await cb.message.answer(f"✅ КУПЛЕНО: {name}\n💰 {format_balance(price)}")
    try: await bot.send_message(seller_id, f"💸 Лот продан!\n{name}\n+{format_balance(sg)} (минус 15%)")
    except: pass

@dp.callback_query(F.data == "pm_mylots")
async def pm_mylots_cb(cb: CallbackQuery):
    uid = cb.from_user.id
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT id,kind,item_name,price,sold FROM pm_items WHERE seller_id = ? ORDER BY id DESC", (uid,))
    rows = c.fetchall(); conn.close()
    if not rows: await cb.answer("Нет лотов", show_alert=True); return
    txt = "📦 МОИ ЛОТЫ\n\n"
    for lid, k, n, p, s in rows:
        e = "👕" if k == "set" else "🏠"; st = "🟢" if not s else "🔴"
        txt += f"#{lid} {e} {n} — {format_balance(p)} {st}\n"
    await cb.message.answer(txt); await cb.answer()

@dp.message(F.text.lower() == "банк")
async def bank_cmd(m: Message):
    if await check_stopped(m) or await check_banned(m): return
    uid = m.from_user.id; _bump_usage(uid)
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id = ?", (uid,))
    u = c.fetchone()
    if not u: await m.answer("Сначала /start"); conn.close(); return
    bal = u[0]
    c.execute("SELECT deposit,deposit_time FROM bank WHERE user_id = ?", (uid,))
    b = c.fetchone(); conn.close()
    txt = f"🏦 БАНК\n💳 Баланс: {format_balance(bal)}\n"
    if b and b[0] > 0:
        d, dts = b; dt = datetime.fromisoformat(dts)
        if datetime.now() >= dt + timedelta(hours=24):
            i = int(d*0.1)
            txt += f"💰 Вклад: {format_balance(d)}\n📈 +{format_balance(i)}\n💵 Итого: {format_balance(d+i)}"
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💵 Положить", callback_data="bank_dep")],
                [InlineKeyboardButton(text="💰 Забрать + проценты", callback_data="bank_wd")]])
        else:
            tl = (dt + timedelta(hours=24)) - datetime.now()
            txt += f"💰 Вклад: {format_balance(d)}\n⏳ {tl.seconds//3600}ч {(tl.seconds%3600)//60}мин"
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💵 Положить", callback_data="bank_dep")],
                [InlineKeyboardButton(text="⏳ Ожидание", callback_data="bank_pend")]])
    else:
        txt += "\n💰 Нет вклада\n💡 Вклад 10% на 24ч"
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="💵 Положить", callback_data="bank_dep")]])
    await m.answer(txt, reply_markup=kb)

@dp.callback_query(F.data == "bank_dep")
async def bank_dep_cb(cb: CallbackQuery, state: FSMContext):
    uid = cb.from_user.id
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id = ?", (uid,))
    bal = c.fetchone()[0]; conn.close()
    md = bal // 2
    if md < 1_000_000: await cb.answer("❌ Мин. 1.000.000", show_alert=True); return
    await cb.message.answer(f"💵 Сумма (макс {format_balance(md)}):")
    await state.set_state(BankDepositState.waiting_amount)
    await cb.answer()

@dp.message(BankDepositState.waiting_amount)
async def bank_dep_msg(m: Message, state: FSMContext):
    if await check_banned(m): return
    uid = m.from_user.id
    try: amount = parse_amount(m.text.strip())
    except: await m.answer("❌ Сумма"); return
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id = ?", (uid,))
    bal = c.fetchone()[0]; md = bal // 2
    if amount < 1_000_000 or amount > md:
        await m.answer(f"❌ От 1.000.000 до {format_balance(md)}"); conn.close(); return
    nb = bal - amount
    c.execute("UPDATE users SET balance = ? WHERE user_id = ?", (nb, uid))
    c.execute("INSERT OR REPLACE INTO bank (user_id,deposit,deposit_time) VALUES (?,?,?)",
        (uid, amount, datetime.now().isoformat()))
    conn.commit(); conn.close()
    await m.answer(f"✅ Вклад: {format_balance(amount)}\n💰 Через 24ч: {format_balance(int(amount*1.1))}",
        reply_markup=get_full_keyboard() if is_private(m) else None)
    await state.clear()

@dp.callback_query(F.data == "bank_wd")
async def bank_wd_cb(cb: CallbackQuery):
    uid = cb.from_user.id
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT deposit,deposit_time FROM bank WHERE user_id = ?", (uid,))
    b = c.fetchone()
    if not b or b[0] == 0: await cb.answer("❌ Нет вклада", show_alert=True); conn.close(); return
    d, dts = b; dt = datetime.fromisoformat(dts)
    if datetime.now() < dt + timedelta(hours=24):
        await cb.answer("❌ Ещё не готов", show_alert=True); conn.close(); return
    i = int(d*0.1); total = d + i
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (total, uid))
    c.execute("DELETE FROM bank WHERE user_id = ?", (uid,))
    conn.commit()
    c.execute("SELECT balance FROM users WHERE user_id = ?", (uid,))
    nb = c.fetchone()[0]; conn.close()
    await cb.message.edit_text(f"✅ Снято!\n💰 {format_balance(d)}\n📈 +{format_balance(i)}\n💵 Итого: {format_balance(total)}\n💳 {format_balance(nb)}")
    await cb.answer()

@dp.callback_query(F.data == "bank_pend")
async def bank_pend_cb(cb: CallbackQuery): await cb.answer("⏳ Ещё не готово", show_alert=True)

def gen_math():
    op = random.choice(["+","-","*","/"])
    if op == "+":
        a, b = random.randint(1,100), random.randint(1,100)
        return {"p":f"{a} + {b}","c":a+b,"w":a+b+random.randint(-5,5)}
    if op == "-":
        a, b = random.randint(1,100), random.randint(1,100)
        if a < b: a, b = b, a
        return {"p":f"{a} - {b}","c":a-b,"w":a-b+random.randint(-5,5)}
    if op == "*":
        a, b = random.randint(1,20), random.randint(1,10)
        return {"p":f"{a} × {b}","c":a*b,"w":a*b+random.randint(-5,5)}
    b = random.randint(1,20); ans = random.randint(1,20); a = b*ans
    return {"p":f"{a} ÷ {b}","c":ans,"w":ans+random.randint(-5,5)}

def gen_rebus():
    d = random.choice(REBUS_WORDS); L = d["letters"].copy(); random.shuffle(L)
    return {"word":d["word"],"s":" ".join(L)}

@dp.message(F.text.lower() == "💼 работа")
async def work_cmd(m: Message):
    if not is_private(m): return
    if await check_stopped(m) or await check_banned(m): return
    _bump_usage(m.from_user.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🖱️ Кликер", callback_data="cli_start")],
        [InlineKeyboardButton(text="👨‍🏫 Учитель", callback_data="tch_start")],
        [InlineKeyboardButton(text="🧩 Ребусы", callback_data="reb_start")],
        [InlineKeyboardButton(text="🚕 Такси", callback_data="taxi_open")],
        [InlineKeyboardButton(text="❌ Закрыть", callback_data="close_work")]])
    await m.answer("💼 РАБОТА", reply_markup=kb)

@dp.callback_query(F.data == "cli_start")
async def cli_start_cb(cb: CallbackQuery):
    uid = cb.from_user.id
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT clicks FROM clicker WHERE user_id = ?", (uid,))
    r = c.fetchone(); conn.close()
    clicks = r[0] if r else 0
    if clicks >= CLICKER_MAX_CLICKS:
        conn = get_db_connection(); c = conn.cursor()
        c.execute("UPDATE clicker SET clicks = 0 WHERE user_id = ?", (uid,))
        conn.commit(); conn.close(); clicks = 0
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🖱️ Клик ({clicks}/{CLICKER_MAX_CLICKS})", callback_data="cli_click")],
        [InlineKeyboardButton(text="❌ Закрыть", callback_data="close_work")]])
    await cb.message.edit_text(f"🖱️ КЛИКЕР\nКликов: {clicks}/{CLICKER_MAX_CLICKS}\n+{format_balance(CLICKER_REWARD)}", reply_markup=kb)
    await cb.answer()

@dp.callback_query(F.data == "cli_click")
async def cli_click_cb(cb: CallbackQuery):
    uid = cb.from_user.id
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT clicks FROM clicker WHERE user_id = ?", (uid,))
    r = c.fetchone(); clicks = r[0] if r else 0
    if clicks >= CLICKER_MAX_CLICKS:
        await cb.answer("❌ Лимит", show_alert=True); conn.close(); return
    nc = clicks + 1
    if r: c.execute("UPDATE clicker SET clicks = ? WHERE user_id = ?", (nc, uid))
    else: c.execute("INSERT INTO clicker (user_id,clicks) VALUES (?,?)", (uid, nc))
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (CLICKER_REWARD, uid))
    conn.commit()
    c.execute("SELECT balance FROM users WHERE user_id = ?", (uid,))
    nb = c.fetchone()[0]; conn.close()
    await cb.answer(f"✅ +{format_balance(CLICKER_REWARD)}")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🖱️ Клик ({nc}/{CLICKER_MAX_CLICKS})", callback_data="cli_click")],
        [InlineKeyboardButton(text="❌ Закрыть", callback_data="close_work")]])
    await cb.message.edit_text(f"🖱️ КЛИКЕР\nКликов: {nc}/{CLICKER_MAX_CLICKS}\n💳 {format_balance(nb)}", reply_markup=kb)

@dp.callback_query(F.data == "tch_start")
async def tch_start_cb(cb: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да", callback_data="tch_yes")],
        [InlineKeyboardButton(text="❌ Нет", callback_data="close_work")]])
    await cb.message.edit_text("👨‍🏫 УЧИТЕЛЬ\n+2.5ккк за верный, -1.5ккк за ошибку\n4 ошибки — конец", reply_markup=kb)
    await cb.answer()

@dp.callback_query(F.data == "tch_yes")
async def tch_yes_cb(cb: CallbackQuery, state: FSMContext):
    uid = cb.from_user.id
    q = gen_math(); ic = random.choice([True, False])
    da = q["c"] if ic else q["w"]
    teacher_sessions[uid] = {"q":q, "ic":ic, "cc":0, "wc":0}
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Правильно", callback_data="tch_ok"),
         InlineKeyboardButton(text="❌ Неверно", callback_data="tch_no")],
        [InlineKeyboardButton(text="❌ Закончить", callback_data="close_work")]])
    await cb.message.edit_text(f"👨‍🏫 Ученик: {q['p']}\nОтвет: {da}\n\nПравильно?", reply_markup=kb)
    await state.set_state(TeacherState.waiting_answer)
    await cb.answer()

@dp.callback_query(F.data.startswith("tch_"))
async def tch_ans_cb(cb: CallbackQuery, state: FSMContext):
    if cb.data in ("tch_start","tch_yes"): return
    uid = cb.from_user.id; at = cb.data.split("_")[1]
    s = teacher_sessions.get(uid)
    if not s: await cb.answer("❌ Сессия", show_alert=True); await state.clear(); return
    uc = at == "ok"; ic = s["ic"]
    conn = get_db_connection(); c = conn.cursor()
    if uc == ic:
        r = 2_500_000_000
        c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (r, uid))
        s["cc"] = s.get("cc",0) + 1; msg = f"✅ +{format_balance(r)}"
    else:
        p = 1_500_000_000
        c.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (p, uid))
        s["wc"] = s.get("wc",0) + 1; msg = f"❌ -{format_balance(p)}"
    conn.commit(); conn.close()
    await cb.answer(msg, show_alert=True)
    if s.get("wc",0) >= 4:
        await cb.message.edit_text(f"❌ 4 ошибки. Конец.\n💰 Заработано: {format_balance(s.get('cc',0)*2_500_000_000)}")
        teacher_sessions.pop(uid, None); await state.clear(); return
    q = gen_math(); ic2 = random.choice([True, False]); da = q["c"] if ic2 else q["w"]
    teacher_sessions[uid] = {"q":q,"ic":ic2,"cc":s.get("cc",0),"wc":s.get("wc",0)}
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Правильно", callback_data="tch_ok"),
         InlineKeyboardButton(text="❌ Неверно", callback_data="tch_no")],
        [InlineKeyboardButton(text="❌ Закончить", callback_data="close_work")]])
    await cb.message.edit_text(f"👨‍🏫 Ученик: {q['p']}\nОтвет: {da}\n\nПравильно?", reply_markup=kb)
    await state.set_state(TeacherState.waiting_answer)

@dp.callback_query(F.data == "reb_start")
async def reb_start_cb(cb: CallbackQuery, state: FSMContext):
    uid = cb.from_user.id; r = gen_rebus()
    rebus_sessions[uid] = {"word":r["word"],"cc":0,"wc":0}
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Закончить", callback_data="close_work")]])
    await cb.message.edit_text(f"🧩 РЕБУСЫ\nСобери:\n<code>{r['s']}</code>\n\n+1ккк за верный", parse_mode=ParseMode.HTML, reply_markup=kb)
    await state.set_state(RebusState.waiting_answer); await cb.answer()

@dp.message(RebusState.waiting_answer)
async def reb_ans(m: Message, state: FSMContext):
    if not is_private(m): return
    if await check_banned(m): return
    uid = m.from_user.id; ans = m.text.strip().upper()
    if ans in REBUS_BLOCKLIST:
        rebus_sessions.pop(uid, None); await state.clear(); return
    s = rebus_sessions.get(uid)
    if not s: return
    if ans == s["word"]:
        conn = get_db_connection(); c = conn.cursor()
        c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (1_000_000_000, uid))
        conn.commit(); conn.close()
        cc = s.get("cc",0) + 1
        if cc >= 6:
            await m.answer(f"🎉 6 верных! Конец.\n💰 +{format_balance(6_000_000_000)}")
            rebus_sessions.pop(uid, None); await state.clear(); return
        r = gen_rebus()
        rebus_sessions[uid] = {"word":r["word"],"cc":cc,"wc":s.get("wc",0)}
        await m.answer(f"✅ +1ккк\n\nСледующий:\n<code>{r['s']}</code>\n\nПравильных: {cc}/6", parse_mode=ParseMode.HTML)
    else:
        wc = s.get("wc",0) + 1
        if wc >= 6:
            await m.answer("❌ 6 ошибок. Конец."); rebus_sessions.pop(uid, None); await state.clear(); return
        r = gen_rebus()
        rebus_sessions[uid] = {"word":r["word"],"cc":s.get("cc",0),"wc":wc}
        await m.answer(f"❌ Ответ: <b>{s['word']}</b>\n\nНовый:\n<code>{r['s']}</code>\n\nОшибок: {wc}/6", parse_mode=ParseMode.HTML)

@dp.callback_query(F.data == "close_work")
async def close_work_cb(cb: CallbackQuery, state: FSMContext):
    try: await cb.message.delete()
    except: pass
        await state.clear(); await cb.answer()
def _pdt(v):
    if not v: return None
    try: return datetime.fromisoformat(str(v))
    except: return None

def taxi_left(uid):
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT taxi_rent_until FROM users WHERE user_id = ?", (uid,))
    r = c.fetchone(); conn.close()
    if not r or not r[0]: return 0
    u = _pdt(r[0])
    if not u: return 0
    return int((u - datetime.now()).total_seconds())

@dp.callback_query(F.data == "taxi_open")
async def taxi_open_cb(cb: CallbackQuery):
    uid = cb.from_user.id
    if not await user_exists(uid): await cb.answer("Сначала /start", show_alert=True); return
    try: await cb.message.delete()
    except: pass
    await show_taxi(cb.message, uid)

async def show_taxi(m, uid):
    left = taxi_left(uid)
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT balance,taxi_earnings,taxi_current_order,taxi_stars FROM users WHERE user_id = ?", (uid,))
    u = c.fetchone(); conn.close()
    if not u: await m.answer("Сначала /start"); return
    bal, earn, cur, stars = u
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    if left <= 0:
        kb.inline_keyboard.append([InlineKeyboardButton(text=f"🚗 Арендовать ({format_balance(TAXI_RENT_PRICE)})", callback_data="taxi_rent")])
        txt = f"🚕 ТАКСИ\n❌ Нет аренды\n💰 {format_balance(TAXI_RENT_PRICE)} / 15мин\n🌟 {stars}/105"
    else:
        mm, ss = divmod(left, 60)
        txt = f"🚕 ТАКСИ\n⏳ {mm}м {ss}с\n💰 {format_balance(earn or 0)}\n🌟 {stars}/105\n"
        if cur: txt += f"\n🚗 Заказ #{cur} в процессе"
        else:
            txt += "\n✅ Можно брать заказ"
            kb.inline_keyboard.append([InlineKeyboardButton(text="🚕 Взять заказ", callback_data="taxi_take")])
        kb.inline_keyboard.append([InlineKeyboardButton(text="💰 Забрать заработок", callback_data="taxi_collect")])
    kb.inline_keyboard.append([InlineKeyboardButton(text="🔄 Обновить", callback_data="taxi_refresh")])
    await m.answer(txt, reply_markup=kb)

@dp.callback_query(F.data == "taxi_rent")
async def taxi_rent_cb(cb: CallbackQuery):
    uid = cb.from_user.id
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id = ?", (uid,))
    u = c.fetchone(); conn.close()
    if not u or u[0] < TAXI_RENT_PRICE:
        await cb.answer(f"❌ Нужно {format_balance(TAXI_RENT_PRICE)}", show_alert=True); return
    until = datetime.now() + timedelta(minutes=TAXI_RENT_MINUTES)
    conn = get_db_connection(); c = conn.cursor()
    c.execute("UPDATE users SET balance = balance - ?, taxi_rent_until = ?, taxi_earnings = 0 WHERE user_id = ?",
        (TAXI_RENT_PRICE, until.isoformat(), uid))
    conn.commit(); conn.close()
    await cb.answer("✅ Аренда активирована!")
    try: await cb.message.delete()
    except: pass
    await show_taxi(cb.message, uid)

@dp.callback_query(F.data == "taxi_take")
async def taxi_take_cb(cb: CallbackQuery):
    uid = cb.from_user.id
    if taxi_left(uid) <= 0: await cb.answer("❌ Аренда не активна", show_alert=True); return
    b = []
    for oid, o in TAXI_ORDERS.items():
        b.append([InlineKeyboardButton(text=f"{o['emoji']} {o['name']} ({o['seconds']}с)", callback_data=f"taxi_ord_{oid}")])
    await cb.message.answer("🚕 Заказ:", reply_markup=InlineKeyboardMarkup(inline_keyboard=b))
    await cb.answer()

@dp.callback_query(F.data.startswith("taxi_ord_"))
async def taxi_process_cb(cb: CallbackQuery):
    uid = cb.from_user.id
    try: oid = int(cb.data.split("_")[2])
    except: await cb.answer("❌"); return
    if oid not in TAXI_ORDERS: await cb.answer("❌"); return
    if uid in taxi_order_locks: await cb.answer("⏳ Уже выполняется", show_alert=True); return
    if taxi_left(uid) <= 0: await cb.answer("❌ Аренда не активна", show_alert=True); return
    order = TAXI_ORDERS[oid]
    payout = random.randint(order["min_payout"], order["max_payout"])
    taxi_order_locks.add(uid)
    try:
        conn = get_db_connection(); c = conn.cursor()
        c.execute("UPDATE users SET taxi_current_order = ? WHERE user_id = ?", (oid, uid))
        conn.commit(); conn.close()
        await cb.answer(f"🚗 Заказ принят! {order['seconds']}с")
        await asyncio.sleep(order["seconds"])
        conn = get_db_connection(); c = conn.cursor()
        c.execute("UPDATE users SET taxi_earnings = COALESCE(taxi_earnings,0) + ?, taxi_current_order = NULL WHERE user_id = ?",
            (payout, uid))
        c.execute("INSERT INTO taxi_orders (user_id,order_type,earnings,completed,created_at) VALUES (?,?,?,1,?)",
            (uid, oid, payout, datetime.now().isoformat()))
        conn.commit(); conn.close()
        try: await bot.send_message(uid, f"✅ Заказ выполнен! +{format_balance(payout)}")
        except: pass
    finally:
        taxi_order_locks.discard(uid)

@dp.callback_query(F.data == "taxi_collect")
async def taxi_collect_cb(cb: CallbackQuery):
    uid = cb.from_user.id; last = taxi_collect_last.get(uid)
    if last and datetime.now() - last < TAXI_COLLECT_COOLDOWN:
        await cb.answer("⏳ Рано", show_alert=True); return
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT taxi_earnings FROM users WHERE user_id = ?", (uid,))
    r = c.fetchone(); earn = int(r[0] or 0) if r else 0
    if earn < TAXI_COLLECT_MIN:
        await cb.answer(f"❌ Мин. {format_balance(TAXI_COLLECT_MIN)}", show_alert=True); conn.close(); return
    take = min(earn, TAXI_COLLECT_CAP)
    c.execute("UPDATE users SET balance = balance + ?, taxi_earnings = taxi_earnings - ? WHERE user_id = ?", (take, take, uid))
    conn.commit(); conn.close()
    taxi_collect_last[uid] = datetime.now()
    await cb.answer(f"💰 +{format_balance(take)}", show_alert=True)
    try: await cb.message.delete()
    except: pass

@dp.callback_query(F.data == "taxi_refresh")
async def taxi_refresh_cb(cb: CallbackQuery):
    try: await cb.message.delete()
    except: pass
    await show_taxi(cb.message, cb.from_user.id); await cb.answer()

@dp.message(F.text.lower() == "карта")
async def map_cmd(m: Message):
    if await check_stopped(m) or await check_banned(m): return
    uid = m.from_user.id
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT city,travel_end_time FROM users WHERE user_id = ?", (uid,))
    u = c.fetchone(); conn.close()
    if not u: await m.answer("Сначала /start"); return
    cc, tet = u
    if tet:
        te = datetime.fromisoformat(tet)
        if datetime.now() < te:
            rem = (te - datetime.now()).seconds
            await m.answer(f"🚗 В пути! {rem//60}мин {rem%60}сек"); return
    _bump_usage(uid)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚗 Рублёвка", callback_data="trv_рублёвка"),
         InlineKeyboardButton(text="🚗 Лыткарино", callback_data="trv_лыткарино")],
        [InlineKeyboardButton(text="🚗 Арзамас", callback_data="trv_арзамас"),
         InlineKeyboardButton(text="🚗 Батырево", callback_data="trv_батырево")],
        [InlineKeyboardButton(text="🚗 Южный", callback_data="trv_южный"),
         InlineKeyboardButton(text="🚗 Нижнегородск", callback_data="trv_нижнегородск")]])
    cn = CITIES.get(cc, {}).get("name", "Рублёвка")
    await m.answer_photo(photo=MAP_IMAGE_URL, caption=f"🗺️ КАРТА\n📍 Ты в: {cn}", reply_markup=kb)

@dp.callback_query(F.data.startswith("trv_"))
async def travel_cb(cb: CallbackQuery):
    uid = cb.from_user.id
    ck = cb.data.split("_", 1)[1]
    cd = CITIES.get(ck)
    if not cd: await cb.answer("❌"); return
    te = datetime.now() + timedelta(seconds=cd["travel_time"])
    conn = get_db_connection(); c = conn.cursor()
    c.execute("UPDATE users SET city = ?, travel_end_time = ? WHERE user_id = ?", (ck, te.isoformat(), uid))
    conn.commit(); conn.close()
    await cb.message.delete()
    await cb.message.answer_photo(photo=TRAVEL_IMAGE_URL, caption=f"🚗 Едем в {cd['name']}\n⏱ {cd['travel_time']} сек")
    await asyncio.sleep(cd["travel_time"])
    conn = get_db_connection(); c = conn.cursor()
    c.execute("UPDATE users SET travel_end_time = NULL WHERE user_id = ?", (uid,))
    conn.commit(); conn.close()
    img = CITY_ARRIVAL_IMAGES.get(ck, MAP_IMAGE_URL)
    try: await cb.message.answer_photo(photo=img, caption=f"📍 Прибыл в {cd['name']}!")
    except: await cb.message.answer(f"📍 Прибыл в {cd['name']}!")

@dp.message(F.text.lower() == "🎫 промокод")
async def promo_cmd(m: Message, state: FSMContext):
    if await check_stopped(m) or await check_banned(m): return
    uid = m.from_user.id; _bump_usage(uid)
    if not await check_subscribed(uid):
        await m.answer(f"❌ Подпишись: {CHANNEL_LINK}"); return
    await m.answer("📝 Введи промокод:")
    await state.set_state(PromoCodeState.waiting_input)

@dp.message(PromoCodeState.waiting_input)
async def promo_act(m: Message, state: FSMContext):
    if await check_banned(m): return
    uid = m.from_user.id; text = m.text.strip()
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT amount,activations_left FROM promocodes WHERE name = ?", (text,))
    pc = c.fetchone()
    if not pc or pc[1] <= 0:
        await m.answer("❌ Промокод не найден"); conn.close(); await state.clear(); return
    c.execute("UPDATE promocodes SET activations_left = activations_left - 1 WHERE name = ?", (text,))
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (pc[0], uid))
    conn.commit(); conn.close()
    await m.answer(f"🍻 +{format_balance(pc[0])}")
    await state.clear()

@dp.message(Command("промо"))
async def create_promo(m: Message):
    if not is_admin(m.from_user.id): return
    args = m.text.split()
    if len(args) < 4: await m.answer("❌ /промо имя сумма активаций"); return
    name = args[1]
    try: amount = parse_amount(args[2]); ac = int(args[3])
    except: return
    conn = get_db_connection(); c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO promocodes (name,amount,activations_left,total_activations,creator_id,created_at) VALUES (?,?,?,?,?,?)",
        (name, amount, ac, ac, m.from_user.id, datetime.now().isoformat()))
    conn.commit(); conn.close()
    await m.answer(f"🎫 {name} создан!")

async def handle_gift_activation(m, gid):
    uid = m.from_user.id
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT amount,activations_left FROM gifts WHERE gift_id = ?", (gid,))
    g = c.fetchone()
    if not g or g[1] <= 0:
        await m.answer("❌ Недействителен"); conn.close(); return
    c.execute("UPDATE gifts SET activations_left = 0 WHERE gift_id = ?", (gid,))
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (g[0], uid))
    conn.commit(); conn.close()
    await m.answer(f"🎉 +{format_balance(g[0])}", reply_markup=get_full_keyboard())

async def handle_check_activation(m, cid):
    uid = m.from_user.id
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT 1 FROM check_activations WHERE check_id = ? AND user_id = ?", (cid, uid))
    if c.fetchone():
        await m.answer("❌ Ты уже активировал этот чек"); conn.close(); return
    c.execute("SELECT amount,activations_left,creator_id FROM checks WHERE check_id = ?", (cid,))
    ch = c.fetchone()
    if not ch or ch[1] <= 0:
        await m.answer("❌ Чек недействителен"); conn.close(); return
    amount, _, creator = ch
    c.execute("UPDATE checks SET activations_left = activations_left - 1 WHERE check_id = ?", (cid,))
    c.execute("INSERT OR IGNORE INTO check_activations (check_id,user_id) VALUES (?,?)", (cid, uid))
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, uid))
    c.execute("SELECT nick FROM users WHERE user_id = ?", (uid,))
    nr = c.fetchone(); nick = nr[0] if nr else str(uid)
    conn.commit(); conn.close()
    await m.answer(f"🎉 Чек активирован! +{format_balance(amount)}", reply_markup=get_full_keyboard())
    if creator:
        try: await bot.send_message(creator, f"🧾 ЧЕК АКТИВИРОВАН\n👤 {get_nick_link(uid, nick)}\n💰 {format_balance(amount)}", parse_mode=ParseMode.HTML)
        except: pass

async def handle_contest_deeplink(m, cid_str):
    try: cid = int(cid_str)
    except: return
    c_data = contest_data.get(cid)
    if not c_data: await m.answer("❌ Конкурс не найден"); return
    uid = m.from_user.id
    if uid in c_data["taken_by"]: await m.answer("❌ Уже забирал"); return
    conn = get_db_connection(); c = conn.cursor()
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (c_data["amount"], uid))
    conn.commit(); conn.close()
    c_data["taken_by"].add(uid)
    await m.answer(f"🎁 +{format_balance(c_data['amount'])}")

@dp.message(Command("подарок"))
async def create_gift_cmd(m: Message):
    if not is_admin(m.from_user.id): return
    args = m.text.split()
    if len(args) < 2: return
    try: amount = parse_amount(args[1])
    except: return
    gid = f"gift_{int(datetime.now().timestamp())}"
    conn = get_db_connection(); c = conn.cursor()
    c.execute("INSERT INTO gifts (gift_id,amount,activations_left,creator_id,created_at) VALUES (?,?,1,?,?)",
        (gid, amount, m.from_user.id, datetime.now().isoformat()))
    conn.commit(); conn.close()
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="💰 Активировать", url=f"https://t.me/{BOT_USERNAME}?start={gid}")]])
    await m.answer(f"🎁 {format_balance(amount)}", reply_markup=kb)

@dp.message(Command("чек"))
async def create_check_cmd(m: Message):
    if not is_admin(m.from_user.id): return
    args = m.text.split()
    if len(args) < 3: await m.answer("❌ /чек сумма активаций"); return
    try: amount = parse_amount(args[1]); ac = int(args[2])
    except: return
    cid = f"check_{int(datetime.now().timestamp())}"
    conn = get_db_connection(); c = conn.cursor()
    c.execute("INSERT INTO checks (check_id,amount,activations_left,total_activations,creator_id,created_at) VALUES (?,?,?,?,?,?)",
        (cid, amount, ac, ac, m.from_user.id, datetime.now().isoformat()))
    conn.commit(); conn.close()
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="💰 Активировать", url=f"https://t.me/{BOT_USERNAME}?start={cid}")]])
    text = f"🧾 ЧЕК!\n💰 {format_balance(amount)}\n🎟 {ac} активаций"
    try:
        await bot.send_message(f"@{CHANNEL_USERNAME}", text, reply_markup=kb)
        await m.answer("✅ Чек опубликован!")
    except: await m.answer(f"⚠️ Не опубликовано.\n\n{text}", reply_markup=kb)

@dp.message(Command("конкурс"))
async def create_contest(m: Message):
    global next_contest_id
    if not is_admin(m.from_user.id): return
    if not m.reply_to_message or not m.reply_to_message.photo:
        await m.answer("❌ Ответь на фото"); return
    args = m.text.split(maxsplit=3)
    if len(args) < 4: return
    try:
        amount = parse_amount(args[1]); iid = int(args[2]); txt = args[3]
    except: return
    fid = m.reply_to_message.photo[-1].file_id
    cid = next_contest_id; next_contest_id += 1
    contest_data[cid] = {"amount":amount,"item_id":iid,"text":txt,"file_id":fid,"taken_by":set(),"type":"set"}
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🎁 Забрать", url=f"https://t.me/{BOT_USERNAME}?start=contest_{cid}")]])
    await m.answer_photo(photo=fid, caption=f"🎉 КОНКУРС #{cid}\n\n{txt}\n💰 {format_balance(amount)}", reply_markup=kb)

transfer_words = ["кинуть","дать","передать","скинуть","перевести"]

async def find_user(ident):
    ident = ident.strip().lstrip('@').lower()
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT user_id,nick FROM users WHERE LOWER(nick) = ?", (ident,))
    r = c.fetchone()
    if not r:
        c.execute("SELECT user_id,nick FROM users WHERE LOWER(username) = ?", (ident,))
        r = c.fetchone()
    if not r and ident.isdigit():
        c.execute("SELECT user_id,nick FROM users WHERE user_id = ?", (int(ident),))
        r = c.fetchone()
    conn.close(); return r

@dp.message(F.text.lower().split()[0].in_(transfer_words))
async def transfer_cmd(m: Message):
    if await check_stopped(m) or await check_banned(m): return
    uid = m.from_user.id; parts = m.text.split()
    target = None; ams = None
    if m.reply_to_message:
        target = m.reply_to_message.from_user
        if len(parts) >= 2: ams = parts[1]
    else:
        if len(parts) >= 3:
            found = await find_user(parts[1])
            if found:
                target = type('obj',(object,),{'id':found[0],'nick':found[1]}); ams = parts[2]
    if not target or not ams:
        await m.answer("❌ Пример: перевести @ник 1000000\nИли ответь на сообщение"); return
    try: amount = parse_amount(ams)
    except: await m.answer("❌ Сумма"); return
    if amount <= 0 or target.id == uid: await m.answer("❌ Ошибка"); return
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id = ?", (uid,))
    s = c.fetchone()
    c.execute("SELECT balance FROM users WHERE user_id = ?", (target.id,))
    r = c.fetchone()
    if not s or not r: await m.answer("❌ Кто-то не зарегистрирован"); conn.close(); return
    if s[0] < amount: await m.answer("❌ Недостаточно"); conn.close(); return
    c.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, uid))
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, target.id))
    conn.commit(); conn.close()
    await m.answer(f"✅ Переведено {format_balance(amount)}")
    try: await bot.send_message(target.id, f"💸 Ты получил {format_balance(amount)}")
    except: pass

@dp.message(F.text.lower().startswith("кости"))
async def dice_cmd(m: Message):
    if await check_stopped(m) or await check_banned(m): return
    if is_private(m): await m.answer("Только в чатах"); return
    uid = m.from_user.id; _bump_usage(uid)
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT nick,balance FROM users WHERE user_id = ?", (uid,))
    s = c.fetchone(); conn.close()
    if not s: await m.answer("Сначала /start"); return
    if not m.reply_to_message: await m.answer("❌ Ответь на сообщение игрока"); return
    parts = m.text.split()
    if len(parts) < 2: return
    try: amount = parse_amount(parts[1])
    except: return
    if amount <= 0 or s[1] < amount: await m.answer("❌ Сумма"); return
    opp = m.reply_to_message.from_user
    if opp.id == uid: await m.answer("❌ С собой"); return
    gid = f"{uid}_{opp.id}_{int(datetime.now().timestamp())}"
    dice_games[gid] = {"challenger":uid,"opponent":opp.id,"amount":amount,"chat_id":m.chat.id}
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Принять", callback_data=f"dacc_{gid}"),
         InlineKeyboardButton(text="❌ Отказ", callback_data=f"ddec_{gid}")]])
    await m.reply_photo(photo=DICE_IMAGE_URL, caption=f"🎲 {get_nick_link(uid, s[0])} вызывает!\n💰 {format_balance(amount)}", parse_mode=ParseMode.HTML, reply_markup=kb)

@dp.callback_query(F.data.startswith("dacc_"))
async def dice_acc_cb(cb: CallbackQuery):
    gid = cb.data.replace("dacc_",""); g = dice_games.get(gid)
    if not g or cb.from_user.id != g["opponent"]: await cb.answer("❌"); return
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id IN (?,?)", (g["challenger"], g["opponent"]))
    bals = [r[0] for r in c.fetchall()]
    if min(bals) < g["amount"]:
        await cb.answer("❌ Недостаточно"); del dice_games[gid]; conn.close(); return
    c.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (g["amount"], g["challenger"]))
    c.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (g["amount"], g["opponent"]))
    conn.commit(); conn.close()
    try: await cb.message.delete()
    except: pass
    c1 = await bot.send_dice(g["chat_id"]); await asyncio.sleep(4)
    c2 = await bot.send_dice(g["chat_id"]); await asyncio.sleep(4)
    v1, v2 = c1.dice.value, c2.dice.value
    conn = get_db_connection(); c = conn.cursor()
    if v1 > v2:
        c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (g["amount"]*2, g["challenger"]))
        winner = g["challenger"]
    elif v2 > v1:
        c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (g["amount"]*2, g["opponent"]))
        winner = g["opponent"]
    else:
        c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (g["amount"], g["challenger"]))
        c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (g["amount"], g["opponent"]))
        winner = None
    conn.commit(); conn.close()
    if winner:
        await bot.send_message(g["chat_id"], f"🏆 Победил {get_nick_link(winner,'игрок')}! +{format_balance(g['amount']*2)}", parse_mode=ParseMode.HTML)
    else: await bot.send_message(g["chat_id"], "🤝 Ничья")
    del dice_games[gid]

@dp.callback_query(F.data.startswith("ddec_"))
async def dice_dec_cb(cb: CallbackQuery):
    gid = cb.data.replace("ddec_","")
    if gid in dice_games: del dice_games[gid]
    try: await cb.message.delete()
    except: pass
    await cb.answer("❌ Отказ")

@dp.message(F.text.regexp(r"(?i)^число\s+\S+"))
async def number_cmd(m: Message):
    if await check_stopped(m) or await check_banned(m): return
    uid = m.from_user.id
    if not await user_exists(uid): await m.answer("Сначала /start"); return
    parts = m.text.split()
    if len(parts) < 2: return
    try: amount = parse_amount(parts[1])
    except: return
    if amount <= 0: return
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id = ?", (uid,))
    u = c.fetchone()
    if not u or u[0] < amount: await m.answer("❌ Недостаточно"); conn.close(); return
    c.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, uid))
    conn.commit(); conn.close()
    secret = random.randint(1, 100)
    number_games[m.chat.id] = {"secret":secret,"prize":amount,"creator":uid,"active":True}
    _bump_usage(uid)
    await m.answer(f"🎲 ИГРА «ЧИСЛО»\n💰 Приз: {format_balance(amount)}\n\nУгадай 1-100")

@dp.message(F.text.regexp(r"^\d+$"))
async def guess_num(m: Message):
    if m.chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP): return
    g = number_games.get(m.chat.id)
    if not g or not g.get("active") or not m.from_user: return
    try: guess = int(m.text)
    except: return
    if not 1 <= guess <= 100: return
    if m.from_user.id == g["creator"]: return
    if guess == g["secret"]:
        amount = g["prize"]; g["active"] = False
        number_games.pop(m.chat.id, None)
        conn = get_db_connection(); c = conn.cursor()
        c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, m.from_user.id))
        conn.commit(); conn.close()
        await m.reply(f"🎉 Угадал {g['secret']}! +{format_balance(amount)}")
    else:
        await m.reply("♨ тепло" if abs(guess - g["secret"]) <= 20 else "❄ холодно")

@dp.message(F.text.lower() == "топ")
async def top_cmd(m: Message):
    if await check_stopped(m) or await check_banned(m): return
    _bump_usage(m.from_user.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏆 Топ по балансу", callback_data="top_bal_1")],
        [InlineKeyboardButton(text="👥 Топ рефералов", callback_data="top_ref_1")]])
    await m.answer("🏆 ТОП:", reply_markup=kb)

@dp.callback_query(F.data.startswith("top_bal_"))
async def top_bal_cb(cb: CallbackQuery):
    page = int(cb.data.split("_")[2]); pp = 5
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT user_id,nick,balance FROM users WHERE top_visible = 1 ORDER BY balance DESC")
    us = c.fetchall(); conn.close()
    txt = f"🏆 ТОП БАЛАНСА\n\n"
    for i, (uid, nick, b) in enumerate(us[(page-1)*pp:page*pp], start=(page-1)*pp+1):
        txt += f"{i}. {get_nick_link(uid, nick)} — {format_balance(b)}\n"
    try: await cb.message.edit_text(txt, parse_mode=ParseMode.HTML)
    except: pass
    await cb.answer()

@dp.callback_query(F.data.startswith("top_ref_"))
async def top_ref_cb(cb: CallbackQuery):
    page = int(cb.data.split("_")[2]); pp = 5
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT user_id,nick,referals_count FROM users WHERE top_visible = 1 ORDER BY referals_count DESC")
    us = c.fetchall(); conn.close()
    txt = f"👥 ТОП РЕФЕРАЛОВ\n\n"
    for i, (uid, nick, cnt) in enumerate(us[(page-1)*pp:page*pp], start=(page-1)*pp+1):
        txt += f"{i}. {get_nick_link(uid, nick)} — {cnt}\n"
    try: await cb.message.edit_text(txt, parse_mode=ParseMode.HTML)
    except: pass
    await cb.answer()

@dp.message(F.text.lower() == "стата")
async def stats_cmd(m: Message):
    if await check_stopped(m) or await check_banned(m): return
    uid = m.from_user.id; _bump_usage(uid)
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT roul_won,roul_lost,dice_won,dice_lost,slot_won,slot_lost FROM chat_stats WHERE chat_id = ? AND user_id = ?",
        (m.chat.id, uid))
    r = c.fetchone(); conn.close()
    if not r: r = (0,0,0,0,0,0)
    txt = (f"❌ Проигрыши:\n• Рулетка: {format_balance(r[1])}\n• Кости: {format_balance(r[3])}\n• Слоты: {format_balance(r[5])}\n\n"
           f"🏆 Победы:\n• Рулетка: {format_balance(r[0])}\n• Кости: {format_balance(r[2])}\n• Слоты: {format_balance(r[4])}")
    try: await m.answer_photo(photo=STATS_IMAGE_URL, caption=txt)
    except: await m.answer(txt)

@dp.message(F.text.lower() == "⚽ футбол")
async def football_cb(m: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⚽ Открыть ставки", web_app=WebAppInfo(url=WEBAPP_URL))]])
    await m.answer("⚽ Футбольные ставки:", reply_markup=kb)

@dp.message(F.text.lower() == "помощь")
async def help_cmd(m: Message):
    await m.answer("""🎰 ПОМОЩЬ
• я — профиль
• бонус — раз в 25 мин
• рул [тип] [сумма] — рулетка
• ряд1/ряд2/ряд3 [сумма] — ряды (x3)
• слот [сумма] — слоты
• кости [сумма] — в ответ
• число [сумма] — игра
• карта — путешествие
• банк — вклады
• шкаф — вещи
• ⚽ футбол — Mini App""", reply_markup=get_full_keyboard() if is_private(m) else None)

@dp.message(Command("стоп"))
async def stop_bot_cmd(m: Message, cmd: CommandObject):
    if not is_admin(m.from_user.id): return
    if (cmd.args or "").strip().lower() != "бот":
        await m.answer("❌ /стоп бот"); return
    BOT_STOPPED["value"] = True
    await m.answer("🛑 Бот остановлен")

@dp.message(Command("старт"))
async def start_bot_cmd(m: Message, cmd: CommandObject):
    if not is_admin(m.from_user.id): return
    if (cmd.args or "").strip().lower() != "бот":
        await m.answer("❌ /старт бот"); return
    BOT_STOPPED["value"] = False
    await m.answer("✅ Бот запущен")

@dp.message(Command("выдать_себе"))
async def give_self_cmd(m: Message):
    if not is_admin(m.from_user.id): return
    args = m.text.split()
    if len(args) < 2: return
    try: amount = parse_amount(args[1])
    except: return
    uid = m.from_user.id
    conn = get_db_connection(); c = conn.cursor()
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, uid))
    conn.commit()
    c.execute("SELECT balance FROM users WHERE user_id = ?", (uid,))
    nb = c.fetchone()[0]; conn.close()
    await m.answer(f"✅ +{format_balance(amount)}\n💳 {format_balance(nb)}")

@dp.message(Command("выдать"))
async def give_cmd(m: Message):
    if not is_admin(m.from_user.id): return
    if not m.reply_to_message: return
    args = m.text.split()
    if len(args) < 2: return
    try: amount = parse_amount(args[1])
    except: return
    uid = m.reply_to_message.from_user.id
    conn = get_db_connection(); c = conn.cursor()
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, uid))
    conn.commit(); conn.close()
    await m.answer(f"✅ +{format_balance(amount)}")

@dp.message(Command("всем"))
async def all_cmd(m: Message):
    if not is_admin(m.from_user.id): return
    args = m.text.split()
    if len(args) < 2: return
    try: amount = parse_amount(args[1])
    except: return
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    us = c.fetchall()
    for (uid,) in us:
        c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, uid))
    conn.commit(); conn.close()
    for (uid,) in us:
        try: await bot.send_message(uid, f"🎁 Всем по {format_balance(amount)}!")
        except: pass
    await m.answer(f"✅ {len(us)} игрокам")

@dp.message(Command("бан"))
async def ban_cmd(m: Message):
    if not is_admin(m.from_user.id): return
    args = m.text.split()
    if len(args) < 2: return
    t = args[1].replace("@","").strip()
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT user_id,nick FROM users WHERE LOWER(nick) = LOWER(?) OR LOWER(username) = LOWER(?)", (t, t))
    tgt = c.fetchone()
    if not tgt: await m.answer("❌ Не найден"); conn.close(); return
    c.execute("UPDATE users SET is_banned = 1 WHERE user_id = ?", (tgt[0],))
    conn.commit(); conn.close()
    banned_users.add(tgt[0])
    await m.answer(f"✅ {tgt[1]} забанен")

@dp.message(Command("разбан"))
async def unban_cmd(m: Message):
    if not is_admin(m.from_user.id): return
    args = m.text.split()
    if len(args) < 2: return
    t = args[1].replace("@","").strip()
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT user_id,nick FROM users WHERE LOWER(nick) = LOWER(?) OR LOWER(username) = LOWER(?)", (t, t))
    tgt = c.fetchone()
    if not tgt: await m.answer("❌ Не найден"); conn.close(); return
    c.execute("UPDATE users SET is_banned = 0 WHERE user_id = ?", (tgt[0],))
    conn.commit(); conn.close()
    banned_users.discard(tgt[0])
    await m.answer(f"✅ {tgt[1]} разбанен")

@dp.message(Command("дроп"))
async def drop_cmd(m: Message):
    if not is_admin(m.from_user.id): return
    args = m.text.split()
    if len(args) < 2: return
    try: amount = parse_amount(args[1])
    except: return
    global drop_data
    rc = random.choice(list(CITIES.keys()))
    drop_data = {"active":True,"city":rc,"amount":amount,
        "expires_at":datetime.now()+timedelta(hours=2),"claimed":False,"creator_id":m.from_user.id}
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    us = c.fetchall(); conn.close()
    for (uid,) in us:
        try: await bot.send_message(uid, f"🎁 ДРОП: {format_balance(amount)}")
        except: pass
    await m.answer(f"✅ Дроп в {rc}: {format_balance(amount)}")

@dp.message(F.text.lower() == "дропчик")
async def claim_drop(m: Message):
    if await check_stopped(m) or await check_banned(m): return
    uid = m.from_user.id
    global drop_data
    if not drop_data["active"] or drop_data["claimed"]:
        await m.answer("❌ Нет дропа"); return
    if datetime.now() > drop_data["expires_at"]:
        drop_data["active"] = False
        await m.answer("❌ Истёк"); return
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT city FROM users WHERE user_id = ?", (uid,))
    u = c.fetchone(); conn.close()
    if not u or u[0] == drop_data["city"]:
        await m.answer("❌ Не в твоём городе"); return
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🎁 Забрать", callback_data="open_drop")]])
    await m.answer("🎁 НАШЁЛ ДРОП!", reply_markup=kb)

@dp.callback_query(F.data == "open_drop")
async def open_drop_cb(cb: CallbackQuery):
    uid = cb.from_user.id
    global drop_data
    if not drop_data["active"] or drop_data["claimed"]:
        await cb.answer("❌"); return
    amount = drop_data["amount"]
    drop_data["active"] = False; drop_data["claimed"] = True
    conn = get_db_connection(); c = conn.cursor()
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, uid))
    conn.commit(); conn.close()
    try: await cb.message.delete()
    except: pass
    await cb.message.answer(f"🎉 +{format_balance(amount)}")

@dp.message(Command("бэкап"))
async def backup_cmd(m: Message):
    if not is_admin(m.from_user.id): return
    try:
        conn = get_db_connection()
        conn.execute("PRAGMA wal_checkpoint(FULL)"); conn.commit(); conn.close()
        if not os.path.exists(DB_PATH):
            await m.answer("❌ БД не найдена"); return
        with open(DB_PATH, "rb") as f: data = f.read()
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        fname = f"backup_{stamp}.db"
        await m.answer_document(document=BufferedInputFile(data, filename=fname),
            caption=f"📦 БЭКАП\n📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n📁 {fname}\n📊 {len(data)/1024:.1f} КБ\n\n💡 Ответь на файл: /загрузить_бэкап")
    except Exception as e: await m.answer(f"❌ {e}")

@dp.message(Command("загрузить_бэкап"))
async def restore_cmd(m: Message):
    if not is_admin(m.from_user.id): return
    if not m.reply_to_message or not m.reply_to_message.document:
        await m.answer("❌ Ответь на файл .db"); return
    doc = m.reply_to_message.document
    fname = doc.file_name or ""
    if not fname.lower().endswith(".db"):
        await m.answer("❌ Только .db"); return
    try:
        await m.answer("⏳ Загружаю...")
        f = await bot.get_file(doc.file_id)
        data = (await bot.download_file(f.file_path)).getvalue()
        test = DB_PATH + ".test"
        with open(test, "wb") as fp: fp.write(data)
        try:
            t = sqlite3.connect(test); t.execute("SELECT 1 FROM sqlite_master LIMIT 1"); t.close()
        except Exception as e:
            os.remove(test); await m.answer(f"❌ Повреждён: {e}"); return
        for s in ("-wal","-shm"):
            p = DB_PATH + s
            if os.path.exists(p):
                try: os.remove(p)
                except: pass
        os.replace(test, DB_PATH)
        avatar_cache.clear()
        _character_cache["img"] = None; _character_cache["loaded"] = False
        banned_users.clear()
        conn = get_db_connection(); c = conn.cursor()
        c.execute("SELECT user_id FROM users WHERE is_banned = 1")
        for (uid,) in c.fetchall(): banned_users.add(uid)
        conn.close()
        await m.answer(f"✅ БЭКАП ЗАГРУЖЕН\n📁 {fname}\n📊 {len(data)/1024:.1f} КБ")
    except Exception as e: await m.answer(f"❌ {e}")

@dp.message(Command("адм"))
async def adm_cmd(m: Message):
    if not is_admin(m.from_user.id): return
    await m.answer("""👑 АДМИН
💾 /бэкап — создать
📥 /загрузить_бэкап — ответом на файл
💰 /выдать_себе [сумма]
💰 /выдать [сумма] — в ответ
💰 /всем [сумма]
🔨 /бан @ник
🔨 /разбан @ник
🎁 /подарок [сумма]
🧾 /чек [сумма] [кол-во]
🎫 /промо [имя] [сумма] [кол-во]
🎲 /конкурс [сумма] [id] [текст]
🎁 /дроп [сумма]
🛑 /стоп бот
✅ /старт бот""")

# ==================== MINI APP ====================
COMPETITIONS_FOOTBALL = {
    "PL":"🏴 Premier League","PD":"🇪🇸 La Liga","BL1":"🇩🇪 Bundesliga",
    "SA":"🇮🇹 Serie A","FL1":"🇫🇷 Ligue 1","DED":"🇳🇱 Eredivisie",
    "PPL":"🇵🇹 Primeira Liga","ELC":"🏴 Championship","CL":"🏆 Champions League",
    "BSA":"🇧🇷 Brasileirão"}

_fb_cache = {}; FB_TTL = 60

async def fb_get(path, params=None):
    key = f"{path}?{params}"; now = datetime.now()
    if key in _fb_cache:
        data, ts = _fb_cache[key]
        if (now-ts).total_seconds() < FB_TTL: return data
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(f"{FOOTBALL_BASE}{path}", headers={"X-Auth-Token":FOOTBALL_API_KEY}, params=params or {})
        if r.status_code == 429: raise Exception("Лимит API")
        if r.status_code == 403: raise Exception("Доступ запрещён")
        if r.status_code == 404: raise Exception("Турнир недоступен")
        r.raise_for_status(); data = r.json()
    _fb_cache[key] = (data, now); return data

async def fb_matches(comp):
    data = await fb_get(f"/competitions/{comp}/matches", {"status":"SCHEDULED,LIVE,IN_PLAY,PAUSED,FINISHED"})
    ms = data.get("matches",[]); now = datetime.utcnow(); res = []
    for m in ms:
        try: utc = datetime.fromisoformat(m["utcDate"].replace("Z","+00:00")).replace(tzinfo=None)
        except: continue
        if abs((utc-now).total_seconds()) < 3*86400: res.append(m)
    return res

async def fb_match(mid): return await fb_get(f"/matches/{mid}")

async def fb_standings(comp):
    try: return await fb_get(f"/competitions/{comp}/standings")
    except: return {"standings":[]}

def calc_odds(hid, aid, st):
    def rk(tid):
        for t in st.get("standings",[]):
            if t.get("type") != "TOTAL": continue
            for row in t.get("table",[]):
                if row["team"]["id"] == tid: return row["position"]
        return 10
    hp = rk(hid); ap = rk(aid); diff = (ap-hp)/10.0
    h = max(0.10, min(0.75, 0.40+0.25*diff))
    a = max(0.10, min(0.75, 0.40-0.25*diff))
    d = max(0.15, 1-h-a); tot = h+a+d
    h /= tot; a /= tot; d /= tot; mg = 1.10
    return {"home":round(1/h*mg,2),"draw":round(1/d*mg,2),"away":round(1/a*mg,2),
        "favorite":"home" if h > a else "away","home_chance":round(h*100,1),
        "draw_chance":round(d*100,1),"away_chance":round(a*100,1)}

def verify_init(init):
    if not init: raise HTTPException(401,"no initData")
    try: return safe_parse_webapp_init_data(token=BOT_TOKEN, init_data=init).user.id
    except: raise HTTPException(401,"invalid")

@app.get("/api/competitions")
async def api_comps(): return COMPETITIONS_FOOTBALL

@app.get("/api/matches")
async def api_matches(competition: str = "PL"):
    try:
        ms = await fb_matches(competition)
        st = await fb_standings(competition)
    except Exception as e: return JSONResponse({"error":str(e)}, status_code=500)
    res = []
    for m in ms:
        h = m["homeTeam"]; a = m["awayTeam"]; odds = calc_odds(h["id"], a["id"], st)
        res.append({"id":m["id"],"competition":m.get("competition",{}).get("name"),
            "utcDate":m["utcDate"],"status":m["status"],"minute":m.get("minute"),
            "home":{"id":h["id"],"name":h.get("shortName") or h.get("name"),"crest":h.get("crest")},
            "away":{"id":a["id"],"name":a.get("shortName") or a.get("name"),"crest":a.get("crest")},
            "score":{"home":m.get("score",{}).get("fullTime",{}).get("home"),
                     "away":m.get("score",{}).get("fullTime",{}).get("away")},
            "odds":odds})
    return {"matches":res}

@app.get("/api/match/{mid}")
async def api_match(mid: int):
    try: return await fb_match(mid)
    except Exception as e: return JSONResponse({"error":str(e)}, status_code=500)

@app.get("/api/my_balance")
async def api_balance(initData: str):
    uid = verify_init(initData)
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT balance,nick FROM users WHERE user_id = ?", (uid,))
    r = c.fetchone(); conn.close()
    return {"balance":r[0] if r else 0,"nick":r[1] if r else "?"}

@app.post("/api/bet")
async def api_bet(req: Request):
    d = await req.json(); uid = verify_init(d.get("initData"))
    mid = int(d.get("matchId")); comp = d.get("competition","")
    pick = d.get("pick"); amount = int(d.get("amount",0)); coef = float(d.get("coefficient",1.0))
    if pick not in ("home","draw","away"):
        return JSONResponse({"ok":False,"error":"Неверный выбор"}, status_code=400)
    if amount < 100_000:
        return JSONResponse({"ok":False,"error":"Минимум 100.000"}, status_code=400)
    try:
        m = await fb_match(mid)
        st = m.get("status","SCHEDULED")
        if st not in ("SCHEDULED","TIMED"):
            return JSONResponse({"ok":False,"error":"Ставки закрыты"}, status_code=400)
        h = m["homeTeam"].get("shortName") or m["homeTeam"].get("name")
        a = m["awayTeam"].get("shortName") or m["awayTeam"].get("name")
    except: h, a = "?","?"
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id = ?", (uid,))
    r = c.fetchone()
    if not r: conn.close(); return JSONResponse({"ok":False,"error":"Сначала /start"}, status_code=400)
    if r[0] < amount: conn.close(); return JSONResponse({"ok":False,"error":"Недостаточно"}, status_code=400)
    c.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, uid))
    c.execute("INSERT INTO football_bets (user_id,fixture_id,competition,home_team,away_team,pick,amount,coefficient,placed_at) VALUES (?,?,?,?,?,?,?,?,?)",
        (uid, mid, comp, h, a, pick, amount, coef, datetime.now().isoformat()))
    conn.commit()
    c.execute("SELECT balance FROM users WHERE user_id = ?", (uid,))
    nb = c.fetchone()[0]; conn.close()
    lbl = "П1" if pick == "home" else "Х" if pick == "draw" else "П2"
    return {"ok":True,"message":f"✅ {amount:,}₽ на {lbl}".replace(",","."),"balance":nb}

@app.get("/api/my_bets")
async def api_bets(initData: str):
    uid = verify_init(initData)
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT fixture_id,home_team,away_team,pick,amount,coefficient,status,payout FROM football_bets WHERE user_id = ? ORDER BY id DESC LIMIT 50", (uid,))
    rs = c.fetchall(); conn.close()
    return {"bets":[{"fixture_id":r[0],"home":r[1],"away":r[2],"pick":r[3],"amount":r[4],
        "coefficient":r[5],"status":r[6],"payout":r[7]} for r in rs]}

FOOTBALL_HTML = r"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<title>⚽ Ставки</title><script src="https://telegram.org/js/telegram-web-app.js"></script>
<style>*{box-sizing:border-box;margin:0;padding:0;font-family:-apple-system,sans-serif}
:root{--bg:#0a0e14;--card:#161d29;--card2:#1c2534;--border:#232e3f;--text:#eaf0ff;--text2:#7d8ba0;--accent:#00e0a4;--accent2:#00b8ff;--gold:#ffb800;--red:#ff3b5c}
body{background:var(--bg);color:var(--text);min-height:100vh;padding-bottom:90px}
.header{position:sticky;top:0;z-index:50;background:rgba(10,14,20,.85);backdrop-filter:blur(20px);padding:14px 16px 10px;border-bottom:1px solid rgba(35,46,63,.6)}
.header-top{display:flex;align-items:center;gap:10px;margin-bottom:10px}
.logo{font-size:20px;font-weight:800;background:linear-gradient(135deg,var(--accent),var(--accent2));-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.balance-pill{margin-left:auto;background:linear-gradient(135deg,rgba(0,224,164,.15),rgba(0,184,255,.1));border:1px solid rgba(0,224,164,.3);padding:6px 12px;border-radius:100px;font-size:13px;font-weight:700;color:var(--accent)}
.tournaments{display:flex;gap:8px;overflow-x:auto;padding:0 16px 4px;scrollbar-width:none}
.tournaments::-webkit-scrollbar{display:none}
.tournaments button{flex-shrink:0;background:rgba(35,46,63,.5);border:1px solid transparent;color:var(--text2);padding:8px 14px;border-radius:100px;font-size:12px;font-weight:600;white-space:nowrap;cursor:pointer}
.tournaments button.active{background:linear-gradient(135deg,var(--accent),var(--accent2));color:#0a0e14}
.tabs{display:flex;gap:6px;padding:12px 16px 4px}
.tabs button{flex:1;background:transparent;border:none;color:var(--text2);padding:10px;font-size:13px;font-weight:600;cursor:pointer;border-bottom:2px solid transparent}
.tabs button.active{color:var(--text);border-bottom-color:var(--accent)}
#content{padding:12px 16px 20px}
.match{background:linear-gradient(160deg,var(--card),var(--card2));border:1px solid var(--border);border-radius:20px;padding:14px;margin-bottom:14px;cursor:pointer}
.match-top{display:flex;justify-content:space-between;margin-bottom:14px;font-size:11px;color:var(--text2)}
.status-live{color:var(--red);font-weight:700}
.status-finished{color:var(--text2)}
.status-sched{color:var(--accent2)}
.teams{display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:10px;margin-bottom:16px}
.team{display:flex;flex-direction:column;align-items:center;gap:8px;text-align:center}
.team img{width:44px;height:44px;object-fit:contain}
.team.fav .team-logo-wrap{border-color:var(--gold)}
.team-logo-wrap{width:56px;height:56px;display:flex;align-items:center;justify-content:center;background:rgba(255,255,255,.03);border-radius:50%;border:2px solid var(--border);position:relative}
.team-logo-wrap img{width:40px;height:40px}
.team-name{font-size:12px;font-weight:700;line-height:1.15}
.score{font-size:26px;font-weight:800;min-width:60px;text-align:center}
.score.vs{font-size:18px;color:var(--text2)}
.odds{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:12px}
.odds button{background:rgba(35,46,63,.6);border:1.5px solid var(--border);color:var(--text);padding:10px 6px;border-radius:14px;cursor:pointer;display:flex;flex-direction:column;align-items:center;gap:3px}
.odds button:disabled{opacity:.4}
.odds button.fav{border-color:rgba(255,184,0,.4);background:rgba(255,184,0,.08)}
.odds-label-pick{font-size:10px;color:var(--text2);font-weight:600}
.odds-coef{font-size:16px;font-weight:800;color:var(--accent)}
.odds button.fav .odds-coef{color:var(--gold)}
.odds-chance{font-size:9px;color:var(--text2)}
.odds-lock{font-size:10px;color:var(--red);font-weight:700}
.loading{text-align:center;padding:40px;color:var(--text2)}
.error{color:var(--red);text-align:center;padding:20px;background:rgba(255,59,92,.06);border-radius:14px}
.empty{text-align:center;padding:60px 20px;color:var(--text2)}
.modal-bg{display:none;position:fixed;inset:0;background:rgba(0,0,0,.75);z-index:100;align-items:flex-end;justify-content:center}
.modal-bg.show{display:flex}
.modal{background:linear-gradient(180deg,var(--card2),var(--card));border-radius:24px 24px 0 0;padding:20px;width:100%;max-width:500px}
.modal-title{font-size:16px;font-weight:700;margin-bottom:8px}
.modal-sub{font-size:12px;color:var(--text2);margin-bottom:16px}
.amount-input{width:100%;background:rgba(10,14,20,.6);border:1.5px solid var(--border);color:var(--text);padding:14px;border-radius:14px;font-size:18px;font-weight:700;outline:none;margin-bottom:12px}
.quick-amounts{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-bottom:16px}
.quick-amounts button{background:rgba(35,46,63,.5);border:1px solid var(--border);color:var(--text2);padding:8px;border-radius:10px;font-size:11px;font-weight:600;cursor:pointer}
.payout-preview{display:flex;justify-content:space-between;background:rgba(0,224,164,.06);border:1px solid rgba(0,224,164,.2);border-radius:12px;padding:12px;margin-bottom:16px}
.payout-preview .label{font-size:11px;color:var(--text2);text-transform:uppercase}
.payout-preview .value{font-size:16px;font-weight:800;color:var(--accent)}
.modal-actions{display:grid;grid-template-columns:1fr 2fr;gap:8px}
.modal-actions button{padding:14px;border-radius:14px;border:none;font-size:14px;font-weight:700;cursor:pointer}
.btn-cancel{background:rgba(35,46,63,.6);color:var(--text2)}
.btn-confirm{background:linear-gradient(135deg,var(--accent),var(--accent2));color:#0a0e14}
.toast{position:fixed;bottom:100px;left:50%;transform:translateX(-50%) translateY(20px);background:linear-gradient(135deg,var(--accent),var(--accent2));color:#0a0e14;padding:12px 22px;border-radius:100px;font-size:13px;font-weight:700;opacity:0;transition:.3s;z-index:200;pointer-events:none}
.toast.show{opacity:1;transform:translateX(-50%) translateY(0)}
.toast.error{background:linear-gradient(135deg,var(--red),#ff6b6b);color:#fff}
.bottom-nav{position:fixed;bottom:0;left:0;right:0;background:rgba(10,14,20,.9);backdrop-filter:blur(20px);border-top:1px solid var(--border);display:flex;padding:8px 0 max(8px,env(safe-area-inset-bottom));z-index:60}
.bottom-nav button{flex:1;background:transparent;border:none;color:var(--text2);padding:8px;font-size:10px;font-weight:600;cursor:pointer;display:flex;flex-direction:column;align-items:center;gap:3px}
.bottom-nav button .icon{font-size:20px}
.bottom-nav button.active{color:var(--accent)}
.detail-header{display:flex;align-items:center;gap:10px;margin-bottom:14px}
.back-btn{width:38px;height:38px;border-radius:50%;background:rgba(35,46,63,.6);border:1px solid var(--border);color:var(--text);font-size:18px;cursor:pointer}
.detail-title{font-size:15px;font-weight:700;flex:1}
.detail-title small{color:var(--text2);font-size:11px;display:block;margin-top:2px}
.detail-score-card{background:linear-gradient(160deg,var(--card),var(--card2));border:1px solid var(--border);border-radius:20px;padding:20px 14px;margin-bottom:14px}
.detail-teams{display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:10px}
.detail-team{display:flex;flex-direction:column;align-items:center;gap:8px;text-align:center}
.detail-score{font-size:36px;font-weight:900;min-width:80px;text-align:center}
.detail-info{display:flex;justify-content:center;gap:10px;margin-top:14px;font-size:11px;color:var(--text2);flex-wrap:wrap}
.detail-info span{background:rgba(35,46,63,.6);padding:4px 10px;border-radius:100px}
.detail-panel{background:linear-gradient(160deg,var(--card),var(--card2));border:1px solid var(--border);border-radius:16px;padding:14px}
.detail-tabs{display:flex;gap:6px;margin-bottom:12px;background:rgba(35,46,63,.4);padding:4px;border-radius:12px}
.detail-tabs button{flex:1;background:transparent;border:none;color:var(--text2);padding:9px;font-size:12px;font-weight:700;cursor:pointer;border-radius:8px}
.detail-tabs button.active{background:var(--card2);color:var(--text)}
</style></head>
<body>
<div class="header"><div class="header-top"><div class="logo">⚽ FOOTBALL BET</div>
<div class="balance-pill" id="balance">₽...</div></div>
<div class="tournaments-wrap"><div class="tournaments" id="tournaments"></div></div></div>
<div class="tabs" id="main-tabs">
<button id="tab-matches" class="active" onclick="showTab('matches')">🔥 Матчи</button>
<button id="tab-bets" onclick="showTab('bets')">🎯 Мои ставки</button></div>
<div id="content"><div class="loading">Загрузка...</div></div>
<div class="modal-bg" id="betModal"><div class="modal">
<div class="modal-title" id="modalTitle">Ставка</div>
<div class="modal-sub" id="modalInfo"></div>
<input class="amount-input" type="number" id="betAmount" value="1000000">
<div class="quick-amounts">
<button onclick="setAmount(1000000)">1М</button>
<button onclick="setAmount(10000000)">10М</button>
<button onclick="setAmount(100000000)">100М</button>
<button onclick="setAmount('all')">MAX</button></div>
<div class="payout-preview"><span class="label">Выигрыш</span>
<span class="value" id="payoutPreview">₽0</span></div>
<div class="modal-actions"><button class="btn-cancel" onclick="closeModal()">Отмена</button>
<button class="btn-confirm" onclick="confirmBet()">Поставить</button></div></div></div>
<div class="toast" id="toast"></div>
<div class="bottom-nav" id="bottom-nav">
<button class="active" data-tab="matches" onclick="showTab('matches')"><span class="icon">⚽</span>Матчи</button>
<button data-tab="bets" onclick="showTab('bets')"><span class="icon">🎯</span>Ставки</button></div>
<script>
const tg = window.Telegram.WebApp; tg.expand(); tg.ready();
const initData = tg.initData;
let currentComp = "PL", currentTab = "matches", currentMatch = null, currentPick = null, currentCoef = 0, balance = 0;
function fmtBalance(n){return "₽"+n.toLocaleString("ru-RU").replace(/,/g,".");}
function toast(msg,err){const t=document.getElementById("toast");t.textContent=msg;t.className="toast show"+(err?" error":"");setTimeout(()=>t.className="toast",2500);}
function fmtTime(iso){return new Date(iso).toLocaleTimeString("ru-RU",{hour:"2-digit",minute:"2-digit"});}
function fmtDate(iso){const d=new Date(iso),t=new Date(),tm=new Date(t);tm.setDate(t.getDate()+1);if(d.toDateString()===t.toDateString())return"Сегодня";if(d.toDateString()===tm.toDateString())return"Завтра";return d.toLocaleDateString("ru-RU",{day:"2-digit",month:"2-digit"});}
function isLive(m){return ["LIVE","IN_PLAY","PAUSED"].includes(m.status);}
function isFinished(m){return m.status==="FINISHED";}
function isScheduled(m){return ["SCHEDULED","TIMED"].includes(m.status);}
function canBet(m){return isScheduled(m);}
function statusLabel(m){if(isLive(m))return`<span class="status-live">🔴 LIVE${m.minute?" "+m.minute+"'":""}</span>`;if(isFinished(m))return'<span class="status-finished">✓ Завершён</span>';return`<span class="status-sched">${fmtDate(m.utcDate)} · ${fmtTime(m.utcDate)}</span>`;}
async function loadBalance(){try{const r=await fetch(`/api/my_balance?initData=${encodeURIComponent(initData)}`);const d=await r.json();balance=d.balance||0;document.getElementById("balance").textContent=fmtBalance(balance);}catch(e){}}
async function loadComps(){const r=await fetch("/api/competitions");const comps=await r.json();const el=document.getElementById("tournaments");el.innerHTML="";let first=true;for(const [code,name] of Object.entries(comps)){const b=document.createElement("button");b.textContent=name;if(first){b.classList.add("active");currentComp=code;first=false;}b.onclick=()=>{document.querySelectorAll("#tournaments button").forEach(x=>x.classList.remove("active"));b.classList.add("active");currentComp=code;showTab(currentTab);};el.appendChild(b);}}
async function loadMatches(){const el=document.getElementById("content");el.innerHTML='<div class="loading">Загрузка...</div>';try{const r=await fetch(`/api/matches?competition=${currentComp}`);const d=await r.json();if(d.error){el.innerHTML=`<div class="error">${d.error}</div>`;return;}if(!d.matches||!d.matches.length){el.innerHTML='<div class="empty">Нет матчей</div>';return;}el.innerHTML="";d.matches.forEach(m=>el.appendChild(renderMatch(m)));}catch(e){el.innerHTML=`<div class="error">${e.message}</div>`;}}
function renderMatch(m){const c=document.createElement("div");c.className="match";const o=m.odds;const fh=o.favorite==="home",fa=o.favorite==="away";const hs=m.score?.home,as_=m.score?.away;const ss=(isLive(m)||isFinished(m))&&hs!==null&&as_!==null;const lk=!canBet(m);
c.innerHTML=`<div class="match-top"><span>${m.competition||""}</span>${statusLabel(m)}</div>
<div class="teams"><div class="team ${fh&&!lk?'fav':''}"><div class="team-logo-wrap"><img src="${m.home.crest}" onerror="this.style.display='none'"></div><div class="team-name">${m.home.name}</div></div>
<div><div class="score ${ss?'':'vs'}">${ss?hs+":"+as_:"VS"}</div>${m.minute&&isLive(m)?`<div style="text-align:center;color:var(--red);font-size:10px;font-weight:700">${m.minute}'</div>`:""}</div>
<div class="team ${fa&&!lk?'fav':''}"><div class="team-logo-wrap"><img src="${m.away.crest}" onerror="this.style.display='none'"></div><div class="team-name">${m.away.name}</div></div></div>
<div class="odds">
<button class="${fh?'fav':''}" data-p="home" ${lk?'disabled':''}><span class="odds-label-pick">П1</span><span class="odds-coef">${o.home.toFixed(2)}</span>${lk?'<span class="odds-lock">🔒</span>':`<span class="odds-chance">${o.home_chance}%</span>`}</button>
<button data-p="draw" ${lk?'disabled':''}><span class="odds-label-pick">Х</span><span class="odds-coef">${o.draw.toFixed(2)}</span>${lk?'<span class="odds-lock">🔒</span>':`<span class="odds-chance">${o.draw_chance}%</span>`}</button>
<button class="${fa?'fav':''}" data-p="away" ${lk?'disabled':''}><span class="odds-label-pick">П2</span><span class="odds-coef">${o.away.toFixed(2)}</span>${lk?'<span class="odds-lock">🔒</span>':`<span class="odds-chance">${o.away_chance}%</span>`}</button></div>`;
c.onclick=(e)=>{if(e.target.closest(".odds button"))return;openDetail(m.id);};
c.querySelectorAll(".odds button").forEach(b=>{if(b.disabled)return;b.onclick=(e)=>{e.stopPropagation();openBet(m,b.dataset.p,o[b.dataset.p]);};});
return c;}
async function openDetail(mid){document.getElementById("main-tabs").style.display="none";document.getElementById("tournaments-wrap").style.display="none";const el=document.getElementById("content");el.innerHTML='<div class="loading">Загрузка...</div>';try{const r=await fetch(`/api/match/${mid}`);const m=await r.json();if(m.error){el.innerHTML=`<div class="error">${m.error}</div>`;return;}renderDetail(m);}catch(e){el.innerHTML=`<div class="error">${e.message}</div>`;}}
function closeDetail(){document.getElementById("main-tabs").style.display="flex";document.getElementById("tournaments-wrap").style.display="block";showTab(currentTab);}
function renderDetail(m){const el=document.getElementById("content");const lv=isLive(m),fn=isFinished(m);const hs=m.score?.fullTime?.home,as_=m.score?.fullTime?.away;const ss=(lv||fn)&&hs!==null&&as_!==null;const h=m.homeTeam||{},a=m.awayTeam||{};
el.innerHTML=`<div class="detail-header"><button class="back-btn" onclick="closeDetail()">←</button><div class="detail-title">${m.competition?.name||""}<small>${m.venue||""}</small></div></div>
<div class="detail-score-card"><div class="detail-teams"><div class="detail-team"><div class="team-logo-wrap"><img src="${h.crest||''}" onerror="this.style.display='none'"></div><div class="team-name">${h.shortName||h.name||''}</div></div>
<div class="detail-score">${ss?hs+":"+as_:"VS"}</div>
<div class="detail-team"><div class="team-logo-wrap"><img src="${a.crest||''}" onerror="this.style.display='none'"></div><div class="team-name">${a.shortName||a.name||''}</div></div></div>
<div class="detail-info"><span>${lv?'🔴 LIVE':fn?'Завершён':fmtDate(m.utcDate)+" "+fmtTime(m.utcDate)}</span>${m.minute?`<span>⏱ ${m.minute}'</span>`:""}</div></div>
<div class="detail-tabs"><button class="active">ℹ️ Инфо</button></div>
<div class="detail-panel"><div style="font-size:12px;color:var(--text2);line-height:1.8">Турнир: <b style="color:var(--text)">${m.competition?.name||"—"}</b><br>Стадион: <b style="color:var(--text)">${m.venue||"—"}</b><br>Дата: <b style="color:var(--text)">${fmtDate(m.utcDate)} ${fmtTime(m.utcDate)}</b></div></div>`;
}
function openBet(match,pick,coef){if(!canBet(match)){toast("Ставки закрыты",true);return;}currentMatch=match;currentPick=pick;currentCoef=coef;
const lbl=pick==="home"?"П1":pick==="draw"?"Х":"П2";const tn=pick==="home"?match.home.name:pick==="draw"?"Ничья":match.away.name;
document.getElementById("modalTitle").textContent=`${lbl} · ${tn}`;document.getElementById("modalInfo").innerHTML=`${match.home.name} — ${match.away.name}<br>Коэф: <b>x${coef.toFixed(2)}</b><br>Баланс: <b>${fmtBalance(balance)}</b>`;
document.getElementById("betAmount").value="1000000";updatePay();document.getElementById("betModal").classList.add("show");}
function updatePay(){const a=parseInt(document.getElementById("betAmount").value)||0;document.getElementById("payoutPreview").textContent=fmtBalance(Math.floor(a*currentCoef));}
document.getElementById("betAmount").addEventListener("input",updatePay);
function setAmount(v){document.getElementById("betAmount").value=v==="all"?balance:v;updatePay();}
function closeModal(){document.getElementById("betModal").classList.remove("show");currentMatch=null;}
async function confirmBet(){const a=parseInt(document.getElementById("betAmount").value);if(!a||a<100000){toast("Мин. 100.000",true);return;}if(a>balance){toast("Недостаточно",true);return;}
try{const r=await fetch("/api/bet",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({initData,matchId:currentMatch.id,pick:currentPick,amount:a,coefficient:currentCoef,competition:currentComp})});const d=await r.json();
if(d.ok){balance=d.balance;document.getElementById("balance").textContent=fmtBalance(balance);closeModal();toast(`✅ Ставка ${fmtBalance(a)}`);}else toast("❌ "+d.error,true);}catch(e){toast("Ошибка",true);}}
async function renderMyBets(){const el=document.getElementById("content");el.innerHTML='<div class="loading">Загрузка...</div>';
try{const r=await fetch(`/api/my_bets?initData=${encodeURIComponent(initData)}`);const d=await r.json();if(!d.bets||!d.bets.length){el.innerHTML='<div class="empty">У тебя нет ставок</div>';return;}
el.innerHTML="";d.bets.forEach(b=>{const lbl=b.pick==="home"?`П1 (${b.home})`:b.pick==="draw"?"Х":`П2 (${b.away})`;let st="⏳ В игре";if(b.status==="won")st=`✅ +${fmtBalance(b.payout)}`;if(b.status==="lost")st="❌ Проигрыш";
const d2=document.createElement("div");d2.className="match";d2.innerHTML=`<div style="font-weight:700;margin-bottom:8px">${b.home} — ${b.away}</div><div style="font-size:12px;color:var(--text2);margin-bottom:6px">${lbl} · ${fmtBalance(b.amount)} · x${b.coefficient.toFixed(2)}</div><div style="font-size:12px;color:var(--accent);font-weight:600">${st}</div>`;el.appendChild(d2);});}catch(e){el.innerHTML=`<div class="error">${e.message}</div>`;}}
function showTab(t){currentTab=t;document.querySelectorAll(".tabs button").forEach(b=>b.classList.remove("active"));document.querySelectorAll(".bottom-nav button").forEach(b=>b.classList.toggle("active",b.dataset.tab===t));const tb=document.getElementById("tab-"+t);if(tb)tb.classList.add("active");if(t==="matches")loadMatches();else renderMyBets();}
loadBalance();loadComps().then(loadMatches);
</script></body></html>"""

@app.get("/", response_class=HTMLResponse)
async def index(): return FOOTBALL_HTML

@app.get("/health")
async def health(): return {"status":"ok"}

# ==================== ФОНОВЫЕ ЗАДАЧИ ====================
async def top3_loop():
    while True:
        try:
            now_utc = datetime.utcnow(); now_msk = now_utc + timedelta(hours=3)
            days = (5 - now_msk.weekday()) % 7
            tgt = now_msk.replace(hour=12,minute=55,second=0,microsecond=0) + timedelta(days=days)
            if tgt <= now_msk: tgt += timedelta(days=7)
            wait = (tgt - now_msk).total_seconds()
            if wait > 0: await asyncio.sleep(min(wait,60)); continue
            conn = get_db_connection(); c = conn.cursor()
            c.execute("SELECT user_id,total FROM bot_usage WHERE user_id NOT IN (SELECT user_id FROM users WHERE is_banned = 1) ORDER BY total DESC LIMIT 3")
            rows = c.fetchall()
            c.execute("SELECT value FROM bot_settings WHERE key = 'top3_amount'")
            r2 = c.fetchone(); amount = int(r2[0]) if r2 else ACTIVITY_REWARD
            for uid, tot in rows:
                if tot <= 0: continue
                c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, uid))
                try: await bot.send_message(uid, f"🏆 Топ-3! +{format_balance(amount)}")
                except: pass
            c.execute("UPDATE bot_usage SET total = 0")
            conn.commit(); conn.close()
            await asyncio.sleep(7*86400)
        except Exception as e: print(f"top3: {e}"); await asyncio.sleep(3600)

async def taxi_reminder_loop():
    while True:
        try:
            now = datetime.now()
            conn = get_db_connection(); c = conn.cursor()
            c.execute("SELECT user_id,taxi_rent_until FROM users WHERE taxi_rent_until IS NOT NULL")
            for uid, us in c.fetchall():
                u = _pdt(us)
                if not u: continue
                left = (u - now).total_seconds()
                if 20 < left < 40:
                    try: await bot.send_message(uid, "⚠️ Аренда закончится через 30 сек!")
                    except: pass
                if left <= 0:
                    c2 = conn.cursor()
                    c2.execute("UPDATE users SET taxi_rent_until = NULL, taxi_current_order = NULL WHERE user_id = ?", (uid,))
                    conn.commit()
                    try: await bot.send_message(uid, "⏰ Аренда закончилась!")
                    except: pass
            conn.close()
        except Exception as e: print(f"taxi: {e}")
        await asyncio.sleep(10)

async def drop_loop():
    while True:
        await asyncio.sleep(7200)
        try:
            global drop_data
            rc = random.choice(list(CITIES.keys()))
            amount = random.randint(50_000_000_000, 110_000_000_000)
            drop_data = {"active":True,"city":rc,"amount":amount,
                "expires_at":datetime.now()+timedelta(hours=2),"claimed":False,"creator_id":None}
            print(f"[AUTO-DROP] {rc}: {amount}")
        except Exception as e: print(f"drop: {e}")

async def football_result_loop():
    while True:
        try:
            conn = get_db_connection(); c = conn.cursor()
            c.execute("SELECT DISTINCT fixture_id FROM football_bets WHERE status = 'pending'")
            ids = [r[0] for r in c.fetchall()]; conn.close()
            for fid in ids:
                try: m = await fb_match(fid)
                except: continue
                if m.get("status") != "FINISHED": continue
                g = m.get("score",{}).get("fullTime",{})
                hs = g.get("home"); as_ = g.get("away")
                if hs is None or as_ is None: continue
                res = "home" if hs > as_ else "away" if hs < as_ else "draw"
                hn = m["homeTeam"].get("shortName") or m["homeTeam"].get("name","?")
                an = m["awayTeam"].get("shortName") or m["awayTeam"].get("name","?")
                conn = get_db_connection(); c = conn.cursor()
                c.execute("SELECT id,user_id,pick,amount,coefficient FROM football_bets WHERE fixture_id = ? AND status = 'pending'", (fid,))
                bets = c.fetchall()
                for bid, uid, pick, amount, coef in bets:
                    if pick == res:
                        pay = int(amount * coef)
                        c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (pay, uid))
                        c.execute("UPDATE football_bets SET status='won',result=?,payout=? WHERE id=?", (res, pay, bid))
                        try: await bot.send_message(uid, f"🏆 ТЫ ВЫИГРАЛ!\n⚽ {hn} {hs}:{as_} {an}\n💰 {format_balance(pay)}", parse_mode=ParseMode.HTML)
                        except: pass
                    else:
                        c.execute("UPDATE football_bets SET status='lost',result=?,payout=0 WHERE id=?", (res, bid))
                        try: await bot.send_message(uid, f"❌ Ставка проиграла\n⚽ {hn} {hs}:{as_} {an}", parse_mode=ParseMode.HTML)
                        except: pass
                conn.commit(); conn.close()
        except Exception as e: print(f"fb: {e}")
        await asyncio.sleep(120)

# ==================== ДИАГНОСТИКА ====================
@dp.message()
async def debug_handler(m: Message):
    print(f"📩 MSG: {m.text} | from {m.from_user.id}", flush=True)

@dp.errors()
async def debug_errors(event):
    print(f"❌ ERROR: {event.exception}", flush=True)
    import traceback
    traceback.print_exception(type(event.exception), event.exception, event.exception.__traceback__)
    return True

# ==================== ЗАПУСК ====================
_started = {"done": False}

@app.on_event("startup")
async def on_startup():
    if _started["done"]: return
    _started["done"] = True
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE is_banned = 1")
    for (uid,) in c.fetchall(): banned_users.add(uid)
    conn.close()
    asyncio.create_task(dp.start_polling(bot))
    asyncio.create_task(top3_loop())
    asyncio.create_task(taxi_reminder_loop())
    asyncio.create_task(drop_loop())
    asyncio.create_task(football_result_loop())
    print("="*50); print("🤖 БОТ + MINI APP запущены"); print("="*50)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
