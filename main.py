import asyncio, random, sqlite3, io, os, sys, traceback
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
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

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
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
taxi_active_rides = {}  # {uid: {"phase": "to_client"|"to_dest", "end_time": iso, "payout": int, "order_type": int, "events": [], "chat_id": int}}
TAXI_EVENTS = [
    {"text":"🚦 Попал в пробку","stars":-1},
    {"text":"🚧 Объехал яму","stars":1},
    {"text":"🎵 Хорошая музыка","stars":1},
    {"text":"💨 Превысил скорость","stars":-1},
    {"text":"🗣️ Нагрубил пассажиру","stars":-2},
    {"text":"🎁 Помог с багажом","stars":2},
    {"text":"😡 Пассажир хамил","stars":-1},
    {"text":"☕ Пассажир угостил кофе","stars":1},
    {"text":"🚨 Полиция остановила","stars":-2},
    {"text":"👍 Пассажир похвалил","stars":2},
]
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
TEACHER_PENALTY = 5_000_000_000
REBUS_LIMIT = 35
REBUS_COOLDOWN = timedelta(hours=3)
rebus_usage = {}

# ========= СХЕМЫ (расстановки) =========
# x от 0 до 1 (слева направо), y от 0 до 1 (0 — своя штрафная, 1 — чужая)
SCHEMES = {
    "4-3-3": [
        {"p":"ВР","x":0.50,"y":0.06},
        {"p":"ПЗ","x":0.85,"y":0.22},{"p":"ЦЗ","x":0.63,"y":0.26},{"p":"ЦЗ","x":0.37,"y":0.26},{"p":"ЛЗ","x":0.15,"y":0.22},
        {"p":"ЦП","x":0.72,"y":0.48},{"p":"ОП","x":0.50,"y":0.53},{"p":"ЦП","x":0.28,"y":0.48},
        {"p":"ПВ","x":0.83,"y":0.78},{"p":"ЦФ","x":0.50,"y":0.85},{"p":"ЛВ","x":0.17,"y":0.78}],
    "4-2-3-1": [
        {"p":"ВР","x":0.50,"y":0.06},
        {"p":"ПЗ","x":0.85,"y":0.22},{"p":"ЦЗ","x":0.63,"y":0.26},{"p":"ЦЗ","x":0.37,"y":0.26},{"p":"ЛЗ","x":0.15,"y":0.22},
        {"p":"ОП","x":0.64,"y":0.44},{"p":"ОП","x":0.36,"y":0.44},
        {"p":"ПВ","x":0.83,"y":0.62},{"p":"АП","x":0.50,"y":0.65},{"p":"ЛВ","x":0.17,"y":0.62},
        {"p":"ЦФ","x":0.50,"y":0.85}],
    "3-5-2": [
        {"p":"ВР","x":0.50,"y":0.06},
        {"p":"ЦЗ","x":0.75,"y":0.25},{"p":"ЦЗ","x":0.50,"y":0.27},{"p":"ЦЗ","x":0.25,"y":0.25},
        {"p":"ПЗ","x":0.88,"y":0.48},{"p":"ЦП","x":0.66,"y":0.50},{"p":"ОП","x":0.50,"y":0.55},{"p":"ЦП","x":0.34,"y":0.50},{"p":"ЛЗ","x":0.12,"y":0.48},
        {"p":"ЦФ","x":0.62,"y":0.83},{"p":"ЦФ","x":0.38,"y":0.83}],
    "4-4-2": [
        {"p":"ВР","x":0.50,"y":0.06},
        {"p":"ПЗ","x":0.85,"y":0.22},{"p":"ЦЗ","x":0.63,"y":0.26},{"p":"ЦЗ","x":0.37,"y":0.26},{"p":"ЛЗ","x":0.15,"y":0.22},
        {"p":"ПП","x":0.85,"y":0.50},{"p":"ЦП","x":0.63,"y":0.53},{"p":"ЦП","x":0.37,"y":0.53},{"p":"ЛП","x":0.15,"y":0.50},
        {"p":"ЦФ","x":0.62,"y":0.83},{"p":"ЦФ","x":0.38,"y":0.83}],
    "3-4-3": [
        {"p":"ВР","x":0.50,"y":0.06},
        {"p":"ЦЗ","x":0.75,"y":0.25},{"p":"ЦЗ","x":0.50,"y":0.27},{"p":"ЦЗ","x":0.25,"y":0.25},
        {"p":"ПЗ","x":0.88,"y":0.50},{"p":"ЦП","x":0.62,"y":0.53},{"p":"ЦП","x":0.38,"y":0.53},{"p":"ЛЗ","x":0.12,"y":0.50},
        {"p":"ПВ","x":0.80,"y":0.80},{"p":"ЦФ","x":0.50,"y":0.87},{"p":"ЛВ","x":0.20,"y":0.80}],
    "5-3-2": [
        {"p":"ВР","x":0.50,"y":0.06},
        {"p":"ПЗ","x":0.90,"y":0.25},{"p":"ЦЗ","x":0.70,"y":0.28},{"p":"ЦЗ","x":0.50,"y":0.30},{"p":"ЦЗ","x":0.30,"y":0.28},{"p":"ЛЗ","x":0.10,"y":0.25},
        {"p":"ЦП","x":0.70,"y":0.55},{"p":"ОП","x":0.50,"y":0.58},{"p":"ЦП","x":0.30,"y":0.55},
        {"p":"ЦФ","x":0.62,"y":0.85},{"p":"ЦФ","x":0.38,"y":0.85}],
    "4-1-4-1": [
        {"p":"ВР","x":0.50,"y":0.06},
        {"p":"ПЗ","x":0.85,"y":0.22},{"p":"ЦЗ","x":0.63,"y":0.26},{"p":"ЦЗ","x":0.37,"y":0.26},{"p":"ЛЗ","x":0.15,"y":0.22},
        {"p":"ОП","x":0.50,"y":0.42},
        {"p":"ПП","x":0.85,"y":0.62},{"p":"ЦП","x":0.63,"y":0.65},{"p":"ЦП","x":0.37,"y":0.65},{"p":"ЛП","x":0.15,"y":0.62},
        {"p":"ЦФ","x":0.50,"y":0.87}],
    "4-3-2-1": [
        {"p":"ВР","x":0.50,"y":0.06},
        {"p":"ПЗ","x":0.85,"y":0.22},{"p":"ЦЗ","x":0.63,"y":0.26},{"p":"ЦЗ","x":0.37,"y":0.26},{"p":"ЛЗ","x":0.15,"y":0.22},
        {"p":"ЦП","x":0.72,"y":0.48},{"p":"ОП","x":0.50,"y":0.52},{"p":"ЦП","x":0.28,"y":0.48},
        {"p":"АП","x":0.65,"y":0.68},{"p":"АП","x":0.35,"y":0.68},
        {"p":"ЦФ","x":0.50,"y":0.88}],
}

SCHEME_KEYS = list(SCHEMES.keys())
NAMES_POOL = {
    "ВР": ["Вратарь"],
    "ПЗ": ["Правый защ."],"ЦЗ": ["Центр. защ."],"ЛЗ": ["Левый защ."],
    "ОП": ["Опорник"],"ЦП": ["Центр. полузащ."],"АП": ["Атак. полузащ."],
    "ПП": ["Правый полузащ."],"ЛП": ["Левый полузащ."],
    "ПВ": ["Правый вингер"],"ЛВ": ["Левый вингер"],"ЦФ": ["Форвард"],
}

def _team_hash(name):
    n = (name or "").lower().strip()
    h = 0
    for ch in n:
        h = (h * 31 + ord(ch)) & 0xFFFFFFFF
    return h

def build_squad_for_team(team_name, forced_scheme=None):
    if forced_scheme and forced_scheme in SCHEMES:
        scheme = forced_scheme
    else:
        scheme = SCHEME_KEYS[_team_hash(team_name) % len(SCHEME_KEYS)]
    layout = SCHEMES[scheme]
    pos_count = {}
    squad = []
    for p in layout:
        pos_label = p["p"]
        idx = pos_count.get(pos_label, 0)
        pos_count[pos_label] = idx + 1
        names = NAMES_POOL.get(pos_label, ["Игрок"])
        name = names[idx % len(names)]
        if idx > 0 and len(names) == 1:
            name = f"{name} {idx+1}"
        squad.append({"n": name, "p": pos_label, "x": p["x"], "y": p["y"]})
    return scheme, squad

def get_squad_pair(home_name, away_name):
    h_scheme, h_squad = build_squad_for_team(home_name)
    a_scheme, a_squad = build_squad_for_team(away_name)
    if h_scheme == a_scheme:
        idx = (SCHEME_KEYS.index(a_scheme) + 1) % len(SCHEME_KEYS)
        a_scheme = SCHEME_KEYS[idx]
        _, a_squad = build_squad_for_team(away_name, forced_scheme=a_scheme)
    return h_scheme, h_squad, a_scheme, a_squad

def get_squad(team_name):
    _, sq = build_squad_for_team(team_name)
    return sq

DEFAULT_SQUAD = [
    {"n":"Вратарь","p":"ВР","x":0.50,"y":0.06},
    {"n":"Правый защ.","p":"ПЗ","x":0.85,"y":0.22},{"n":"Центр. защ. 1","p":"ЦЗ","x":0.63,"y":0.26},{"n":"Центр. защ. 2","p":"ЦЗ","x":0.37,"y":0.26},{"n":"Левый защ.","p":"ЛЗ","x":0.15,"y":0.22},
    {"n":"Опорник","p":"ОП","x":0.50,"y":0.53},{"n":"Центр. полузащ. 1","p":"ЦП","x":0.72,"y":0.48},{"n":"Центр. полузащ. 2","p":"ЦП","x":0.28,"y":0.48},
    {"n":"Правый вингер","p":"ПВ","x":0.83,"y":0.78},{"n":"Форвард","p":"ЦФ","x":0.50,"y":0.85},{"n":"Левый вингер","p":"ЛВ","x":0.17,"y":0.78}]

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
        taxi_stars_claimed INTEGER DEFAULT 0, taxi_collect_accum INTEGER DEFAULT 0,
        rebus_uses INTEGER DEFAULT 0, rebus_reset TEXT)''')
    for col, ct in [("top_visible","INTEGER DEFAULT 1"),("wardrobe_slots","INTEGER DEFAULT 5"),
        ("username","TEXT"),("taxi_rent_until","TEXT"),("taxi_earnings","INTEGER DEFAULT 0"),
        ("total_taxi_rides","INTEGER DEFAULT 0"),("taxi_current_order","INTEGER DEFAULT NULL"),
        ("taxi_order_end","TEXT"),("taxi_stars","INTEGER DEFAULT 0"),
        ("taxi_stars_started","TEXT"),("taxi_stars_claimed","INTEGER DEFAULT 0"),
        ("taxi_collect_accum","INTEGER DEFAULT 0"),("rebus_uses","INTEGER DEFAULT 0"),
        ("rebus_reset","TEXT")]:
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
    c.execute('CREATE TABLE IF NOT EXISTS pm_items (id INTEGER PRIMARY KEY AUTOINCREMENT, seller_id INTEGER, kind TEXT, item_name TEXT, file_id TEXT, price INTEGER, sold INTEGER DEFAULT 0, created_at TEXT, wardrobe_slot INTEGER DEFAULT NULL)')
    c.execute('CREATE TABLE IF NOT EXISTS pm_daily (kind TEXT PRIMARY KEY, sold_today INTEGER DEFAULT 0, day_start TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS bot_usage (user_id INTEGER PRIMARY KEY, total INTEGER DEFAULT 0, updated_at TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS bot_settings (key TEXT PRIMARY KEY, value TEXT)')
    c.execute('''CREATE TABLE IF NOT EXISTS football_bets (id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, fixture_id INTEGER, competition TEXT, home_team TEXT, away_team TEXT,
        pick TEXT, amount INTEGER, coefficient REAL, placed_at TEXT, status TEXT DEFAULT 'pending',
        result TEXT, payout INTEGER DEFAULT 0, reminded INTEGER DEFAULT 0)''')
    if not column_exists(c,'football_bets','reminded'):
        try: c.execute("ALTER TABLE football_bets ADD COLUMN reminded INTEGER DEFAULT 0")
        except: pass
    c.execute('''CREATE TABLE IF NOT EXISTS football_events (id INTEGER PRIMARY KEY AUTOINCREMENT,
        fixture_id INTEGER, event_type TEXT, minute INTEGER, player TEXT, team TEXT,
        score_home INTEGER, score_away INTEGER, extra TEXT, created_at TEXT)''')
    conn.commit(); conn.close()

init_db()

def format_balance(n):
    try: return f"₽{int(n):,}".replace(",",".")
    except: return f"₽{n}"

def parse_amount(s):
    s = str(s).lower().strip().replace("ё","е").replace("ë","е")
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
    await m.answer("⛔ Бот временно остановлен."); return True

async def check_banned(m):
    uid = m.from_user.id
    if uid in OWNERS: return False
    if uid in banned_users:
        await m.answer("⛔ Вы забанены."); return True
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
    waiting_nick = State()
    waiting_new_nick = State()
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
    waiting_balance = State()
    waiting_ref = State()
class ContestState(StatesGroup):
    waiting_photo = State()
class RoulettePhotoState(StatesGroup):
    waiting_photo = State()
class DonateAdminState(StatesGroup):
    waiting_photo = State()

@dp.message(Command("start"))
async def cmd_start(m: Message, state: FSMContext):
    uid = m.from_user.id
    await update_username(uid, m.from_user.username)
    _bump_usage(uid)
    args = m.text.split(); ref = None
    if len(args) > 1:
        a = args[1]
        if a.startswith("gift_"): await handle_gift_activation(m, a); return
        elif a.startswith("check_"): await handle_check_activation(m, a); return
        elif a.startswith("ref_"):
            try: ref = int(a.split("_")[1])
            except: pass
    if await user_exists(uid):
        await send_profile(m, uid); return
    if ref: await state.update_data(referrer_id=ref)
    await state.set_state(RegStates.waiting_nick)
    await m.answer("Придумай никнейм:\n(можно буквы, цифры, пробелы и знаки)")

@dp.message(RegStates.waiting_nick)
async def process_nick(m: Message, state: FSMContext):
    uid = m.from_user.id; nick = m.text.strip()
    if not nick: await m.answer("Ник не может быть пустым."); return
    un = (m.from_user.username or "").lower().lstrip('@') if m.from_user.username else None
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE nick = ?", (nick,))
    if c.fetchone():
        await m.answer("❌ Этот ник уже занят! Придумай другой."); conn.close(); return
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
            try: await bot.send_message(ref, f"🎉 По твоей ссылке зарегистрировался {nick}!\n💰 За это тебе выдано {format_balance(REFERRAL_BONUS)}\n💳 Твой баланс: {format_balance(nb)}")
            except: pass
    conn.close(); await state.clear(); await send_profile(m, uid)

@dp.message(F.text.lower().in_(["📦 меню", "меню"]))
async def menu_cmd(m: Message):
    if not is_private(m): return
    if await check_stopped(m) or await check_banned(m): return
    await update_username(m.from_user.id, m.from_user.username)
    track_command(m.chat.id, m.from_user.id, "меню"); _bump_usage(m.from_user.id)
    await m.answer("📦 Меню", reply_markup=get_menu_keyboard())

@dp.message(F.text.lower().in_(["🛒 закупки", "закупки"]))
async def shop_cmd(m: Message):
    if not is_private(m): return
    if await check_stopped(m) or await check_banned(m): return
    track_command(m.chat.id, m.from_user.id, "закупки"); _bump_usage(m.from_user.id)
    await m.answer("🛒 Закупки", reply_markup=get_shop_keyboard())

@dp.message(F.text.lower().in_(["◀️ назад", "назад"]))
async def back_cmd(m: Message):
    if not is_private(m): return
    if await check_stopped(m) or await check_banned(m): return
    await m.answer("◀️ Назад", reply_markup=get_full_keyboard())

@dp.message(F.text.lower() == "я")
async def me_cmd(m: Message):
    if await check_stopped(m) or await check_banned(m): return
    uid = m.from_user.id
    if not await user_exists(uid):
        await m.answer("Сначала зарегистрируйся через /start"); return
    await update_username(uid, m.from_user.username)
    track_command(m.chat.id, uid, "я"); _bump_usage(uid)
    await send_profile(m, uid)

@dp.message(F.text.lower() == "🔄")
async def refresh_cmd(m: Message):
    if await check_stopped(m) or await check_banned(m): return
    uid = m.from_user.id
    avatar_cache.pop(uid, None); await send_profile(m, uid)

@dp.message(F.text.lower().in_(["🎁 бонус","бонус"]))
async def bonus_cmd(m: Message):
    if await check_stopped(m) or await check_banned(m): return
    uid = m.from_user.id
    track_command(m.chat.id, uid, "бонус"); _bump_usage(uid)
    if not await user_exists(uid):
        un = (m.from_user.username or "").lower().lstrip('@') if m.from_user.username else None
        auto_nick = f"user{uid}"
        conn = get_db_connection(); c = conn.cursor()
        c.execute("SELECT user_id FROM users WHERE nick = ?", (auto_nick,))
        if c.fetchone():
            auto_nick = f"user{uid}_{random.randint(1000,9999)}"
        now = datetime.now().isoformat()
        try:
            c.execute("INSERT INTO users (user_id,nick,balance,registered_at,city,wardrobe_slots,top_visible,username) VALUES (?,?,?,?,?,?,?,?)",
                (uid, auto_nick, START_BALANCE, now, "рублёвка", DEFAULT_WARDROBE_SLOTS, 1, un))
            c.execute("INSERT OR IGNORE INTO settings (user_id,confirm_transfer) VALUES (?,1)", (uid,))
            conn.commit()
        except Exception:
            conn.close(); await m.answer("Ошибка. Напиши /start"); return
        conn.close()
    if not await check_subscribed(uid):
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="📢 Подписаться на канал", url=CHANNEL_LINK)],
            [InlineKeyboardButton(text="✅ Проверить подписку", callback_data="check_bonus_sub")]])
        await m.answer(f"❌ Чтобы забрать бонус, подпишись на наш канал!\n\n👉 {CHANNEL_LINK}", reply_markup=kb); return
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT balance,last_bonus FROM users WHERE user_id = ?", (uid,))
    u = c.fetchone(); conn.close()
    if not u: await m.answer("Ошибка. Напиши /start"); return
    bal, lbs = u; now = datetime.now()
    lb = datetime.fromisoformat(lbs) if lbs else None
    if lb and now - lb < BONUS_COOLDOWN:
        rem = BONUS_COOLDOWN - (now - lb)
        await m.answer(f"⏳ Бонус через {rem.seconds//60} мин {rem.seconds%60} сек",
            reply_markup=get_full_keyboard() if is_private(m) else None); return
    bonus = random.randint(BONUS_MIN, BONUS_MAX); nb = bal + bonus
    conn = get_db_connection(); c = conn.cursor()
    c.execute("UPDATE users SET balance = ?, last_bonus = ? WHERE user_id = ?", (nb, now.isoformat(), uid))
    conn.commit(); conn.close()
    await m.answer(f"✅ Бонус зачислен!\n💰 Сумма: {format_balance(bonus)}\n💳 Новый баланс: {format_balance(nb)}",
        reply_markup=get_full_keyboard() if is_private(m) else None)

@dp.callback_query(F.data == "check_bonus_sub")
async def check_bonus_cb(cb: CallbackQuery):
    if await check_subscribed(cb.from_user.id):
        try: await cb.message.delete()
        except: pass
        await cb.message.answer("✅ Подписка подтверждена! Напиши 'бонус' снова")
    else:
        await cb.answer("❌ Ты не подписан на канал!", show_alert=True)

@dp.message(F.text.lower().in_(["🔗 рефералка", "рефералка"]))
async def ref_cmd(m: Message):
    if await check_stopped(m) or await check_banned(m): return
    uid = m.from_user.id
    if not await user_exists(uid): await m.answer("Сначала зарегистрируйся через /start"); return
    track_command(m.chat.id, uid, "рефералка"); _bump_usage(uid)
    link = f"https://t.me/{BOT_USERNAME}?start=ref_{uid}"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔗 Поделиться", url=f"https://t.me/share/url?url={link}&text=🎰 Играй со мной в ChealOfBot!")],
        [InlineKeyboardButton(text="📋 Скопировать", callback_data="copy_link")]])
    await m.answer(f"🔗 Твоя реферальная ссылка:\n\n`{link}`\n\n💰 За каждого приглашённого ты получаешь {format_balance(REFERRAL_BONUS)}",
        reply_markup=kb, parse_mode=ParseMode.MARKDOWN)

@dp.callback_query(F.data == "copy_link")
async def copy_link_cb(cb: CallbackQuery):
    link = f"https://t.me/{BOT_USERNAME}?start=ref_{cb.from_user.id}"
    await cb.answer(f"Ссылка скопирована: {link}", show_alert=True)

# ========= ПРОФИЛЬ (картинка с фоном/сетом) =========
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
    if not u: await m.answer("Сначала зарегистрируйся через /start"); return
    nick, bal, city = u
    cn = CITIES.get(city, {}).get("name", "Рублёвка")
    txt = f"{get_nick_link(uid, nick)} | баланс: {format_balance(bal)} | 📍город: {cn}"
    try:
        img = await create_profile_image(uid)
        if img:
            await m.answer_photo(photo=img, caption=txt, parse_mode=ParseMode.HTML,
                reply_markup=get_full_keyboard() if is_private(m) else None); return
    except Exception as e: print(f"profile: {e}")
    await m.answer(txt, parse_mode=ParseMode.HTML,
        reply_markup=get_full_keyboard() if is_private(m) else None) # ========= ШКАФ =========
@dp.message(F.text.lower().in_(["📦 шкаф", "шкаф"]))
async def wardrobe_menu(m: Message):
    if await check_stopped(m) or await check_banned(m): return
    _bump_usage(m.from_user.id); uid = m.from_user.id
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT wardrobe_slots FROM users WHERE user_id = ?", (uid,))
    sr = c.fetchone()
    if not sr: await m.answer("Сначала зарегистрируйся через /start"); conn.close(); return
    total = max(sr[0], DEFAULT_WARDROBE_SLOTS)
    c.execute("SELECT slot,item_name,item_id,file_id FROM wardrobe WHERE user_id = ? ORDER BY slot", (uid,))
    items = c.fetchall()
    c.execute("SELECT file_id FROM equipped_outfit WHERE user_id = ?", (uid,))
    eq = c.fetchone()
    c.execute("SELECT file_id FROM equipped_house WHERE user_id = ?", (uid,))
    eqh = c.fetchone(); conn.close()
    txt = f"📦 ТВОЙ ШКАФ (слотов: {len(items)}/{total})\n\n"
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for s in range(1, total+1):
        row = [it for it in items if it[0] == s]
        if row:
            _, name, iid, fid = row[0]
            kb.inline_keyboard.append([InlineKeyboardButton(text=f"👕 {name} (лот #{s})", callback_data=f"wear_{s}")])
        else:
            kb.inline_keyboard.append([InlineKeyboardButton(text=f"📦 Пусто (лот #{s})", callback_data=f"empty_{s}")])
    if eq and eq[0]:
        kb.inline_keyboard.append([InlineKeyboardButton(text="🎒 Положить надетый сет в шкаф", callback_data="stash_outfit")])
    if eqh and eqh[0]:
        kb.inline_keyboard.append([InlineKeyboardButton(text="🎒 Положить надетый дом в шкаф", callback_data="stash_house")])
    kb.inline_keyboard.append([InlineKeyboardButton(text="❌ Закрыть", callback_data="close_wardrobe")])
    await m.answer(txt, parse_mode=ParseMode.HTML, reply_markup=kb)

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
        rows.append([InlineKeyboardButton(text="👕 Положить сет в этот лот", callback_data=f"stash_outfit_slot_{s}")])
    if eqh and eqh[0]:
        rows.append([InlineKeyboardButton(text="🏠 Положить дом в этот лот", callback_data=f"stash_house_slot_{s}")])
    if not rows: await cb.answer("Пусто", show_alert=False); return
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
        c.execute("SELECT item_id,item_name,price FROM wardrobe WHERE user_id = ? AND file_id = ? LIMIT 1", (uid, fid))
        i2 = c.fetchone()
        iid, iname, iprice = i2 if i2 else (0, "Сет", 0)
    c.execute("SELECT wardrobe_slots FROM users WHERE user_id = ?", (uid,))
    slots = max(c.fetchone()[0], DEFAULT_WARDROBE_SLOTS)
    c.execute("SELECT slot FROM wardrobe WHERE user_id = ?", (uid,))
    used = {r[0] for r in c.fetchall()}
    if tslot:
        if tslot in used:
            await cb.answer("❌ Лот занят", show_alert=True); conn.close(); return
        s = tslot
    else:
        s = next((x for x in range(1, slots+1) if x not in used), None)
        if s is None:
            s = slots + 1
            c.execute("UPDATE users SET wardrobe_slots = ? WHERE user_id = ?", (s, uid))
    c.execute("INSERT INTO wardrobe (user_id,slot,item_type,item_id,item_name,file_id,price) VALUES (?,?,?,?,?,?,?)",
        (uid, s, 'market', iid, iname, fid, iprice or 0))
    c.execute("DELETE FROM equipped_outfit WHERE user_id = ?", (uid,))
    conn.commit(); conn.close(); avatar_cache.pop(uid, None)
    await cb.answer(f"✅ Сет '{iname}' в шкафу", show_alert=True)
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
            await cb.answer("❌ Лот занят", show_alert=True); conn.close(); return
        s = tslot
    else:
        s = next((x for x in range(1, slots+1) if x not in used), None)
        if s is None:
            s = slots + 1
            c.execute("UPDATE users SET wardrobe_slots = ? WHERE user_id = ?", (s, uid))
    c.execute("INSERT INTO wardrobe (user_id,slot,item_type,item_id,item_name,file_id,price) VALUES (?,?,?,?,?,?,?)",
        (uid, s, 'house', hid, hname, fid, hprice or 0))
    c.execute("DELETE FROM equipped_house WHERE user_id = ?", (uid,))
    conn.commit(); conn.close(); avatar_cache.pop(uid, None)
    await cb.answer(f"✅ {hname} в шкафу", show_alert=True)
    try: await cb.message.delete()
    except: pass

@dp.callback_query(F.data.startswith("wear_"))
async def wear_cb(cb: CallbackQuery):
    uid = cb.from_user.id
    try: slot = int(cb.data.split("_")[1])
    except: await cb.answer("❌ Ошибка", show_alert=True); return
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT item_name,file_id,item_type FROM wardrobe WHERE user_id = ? AND slot = ?", (uid, slot))
    it = c.fetchone()
    if not it:
        await cb.answer("❌ Предмет не найден", show_alert=True); conn.close(); return
    name, fid, itype = it
    c.execute("SELECT 1 FROM pm_items WHERE seller_id = ? AND wardrobe_slot = ? AND sold = 0", (uid, slot))
    if c.fetchone():
        await cb.answer("❌ Этот предмет выставлен на маркете. Сначала сними лот.", show_alert=True); conn.close(); return
    if itype == 'house':
        c.execute("SELECT file_id FROM equipped_outfit WHERE user_id = ?", (uid,))
        o = c.fetchone()
        if o and o[0] and not await fid_is_white_bg(o[0]):
            await cb.answer("❌ Дом можно надеть только на сет с белым/прозрачным фоном.", show_alert=True); conn.close(); return
        c.execute("SELECT file_id FROM equipped_house WHERE user_id = ?", (uid,))
        oh = c.fetchone()
        if oh and oh[0] and oh[0] != fid:
            c.execute("SELECT id,name,price FROM houses WHERE file_id = ?", (oh[0],))
            oi = c.fetchone()
            if oi: ohid, ohname, ohprice = oi
            else:
                c.execute("SELECT item_id,item_name,price FROM wardrobe WHERE user_id = ? AND file_id = ? LIMIT 1", (uid, oh[0]))
                o2 = c.fetchone()
                ohid, ohname, ohprice = o2 if o2 else (0, "Дом", 0)
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
        await cb.answer(f"✅ Ты надел дом {name}!", show_alert=True)
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
    c.execute("INSERT OR REPLACE INTO equipped_outfit (user_id,file_id) VALUES (?,?)", (uid, fid))
    c.execute("DELETE FROM wardrobe WHERE user_id = ? AND slot = ?", (uid, slot))
    conn.commit(); conn.close(); avatar_cache.pop(uid, None)
    await cb.answer(f"✅ Ты надел {name}!", show_alert=True)
    try: await cb.message.delete()
    except: pass
    await wardrobe_menu(cb.message)

@dp.callback_query(F.data == "close_wardrobe")
async def close_wd(cb: CallbackQuery):
    try: await cb.message.delete()
    except: pass
    await cb.answer()

@dp.message(F.text.lower() == "продажа")
async def sale_cmd(m: Message):
    if await check_stopped(m) or await check_banned(m): return
    uid = m.from_user.id
    if not await user_exists(uid): await m.answer("Сначала зарегистрируйся через /start"); return
    track_command(m.chat.id, uid, "продажа"); _bump_usage(uid)
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT slot,item_name,item_type,price,file_id FROM wardrobe WHERE user_id = ?", (uid,))
    items = c.fetchall(); conn.close()
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for s, name, itype, price, _ in items:
        kb.inline_keyboard.append([InlineKeyboardButton(text=f"🎁 {name} — {format_balance(int((price or 0)*0.35))}", callback_data=f"sell_{s}")])
    if not kb.inline_keyboard:
        await m.answer("❌ У тебя нет имущества в шкафу для продажи."); return
    kb.inline_keyboard.append([InlineKeyboardButton(text="❌ Закрыть", callback_data="close_sale")])
    await m.answer("💸 Что продать? (35% от стоимости, только из шкафа)", reply_markup=kb)

@dp.callback_query(F.data.startswith("sell_"))
async def sell_cb(cb: CallbackQuery):
    uid = cb.from_user.id; s = int(cb.data.split("_")[1])
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT item_name,price FROM wardrobe WHERE user_id = ? AND slot = ?", (uid, s))
    row = c.fetchone()
    if not row:
        await cb.answer("❌ Не найдено", show_alert=True); conn.close(); return
    name, price = row; sp = int((price or 0)*0.35)
    c.execute("DELETE FROM pm_items WHERE seller_id = ? AND wardrobe_slot = ? AND sold = 0", (uid, s))
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (sp, uid))
    c.execute("DELETE FROM wardrobe WHERE user_id = ? AND slot = ?", (uid, s))
    conn.commit(); conn.close()
    await cb.answer(f"✅ '{name}' продан за {format_balance(sp)}", show_alert=True)
    try: await cb.message.delete()
    except: pass

@dp.callback_query(F.data == "close_sale")
async def close_sale_cb(cb: CallbackQuery):
    try: await cb.message.delete()
    except: pass
    await cb.answer()

# ========= МАРКЕТ СЕТОВ =========
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
        await m.answer("❌ Ответь на фото командой:\n<code>/добавить_сет [номер] [цена] [название]</code>", parse_mode=ParseMode.HTML); return
    args = m.text.split(maxsplit=3)
    if len(args) < 4: await m.answer("❌ Пример:\n<code>/добавить_сет 1 50000000000 'Красный сет'</code>", parse_mode=ParseMode.HTML); return
    try: iid = int(args[1]); price = parse_amount(args[2]); name = args[3].strip("'\"")
    except Exception as e: await m.answer(f"❌ Ошибка: {e}"); return
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT MAX(id) FROM market_items")
    mx = c.fetchone()[0] or 0
    if iid != mx + 1:
        await m.answer(f"❌ ID должен идти по порядку! Следующий ID: {mx + 1}"); conn.close(); return
    fid = m.reply_to_message.photo[-1].file_id
    c.execute("INSERT INTO market_items (id,name,price,file_id,created_by,created_at) VALUES (?,?,?,?,?,?)",
        (iid, name, price, fid, m.from_user.id, datetime.now().isoformat()))
    conn.commit(); conn.close()
    await m.answer(f"✅ <b>СЕТ ДОБАВЛЕН!</b>\n\n📦 Номер: <b>{iid}</b>\n📝 Название: <b>{name}</b>\n💰 Цена: <b>{format_balance(price)}</b>", parse_mode=ParseMode.HTML)

@dp.message(F.text.lower() == "👕 маркет сетов")
async def market_cmd(m: Message):
    if await check_stopped(m) or await check_banned(m): return
    _bump_usage(m.from_user.id)
    items = get_market_items()
    if not items: await m.answer("👕 Маркет сетов пуст", parse_mode=ParseMode.HTML); return
    await show_market(m, 0, items)

def market_kb(i, total, iid, price):
    kb = InlineKeyboardMarkup(inline_keyboard=[]); nav = []
    if i > 0: nav.append(InlineKeyboardButton(text="◀️ Назад", callback_data=f"mp_{i}"))
    if i < total-1: nav.append(InlineKeyboardButton(text="Вперёд ▶️", callback_data=f"mn_{i}"))
    if nav: kb.inline_keyboard.append(nav)
    kb.inline_keyboard.append([InlineKeyboardButton(text="💰 Купить", callback_data=f"mbuy_{iid}_{i}")])
    kb.inline_keyboard.append([InlineKeyboardButton(text="❌ Закрыть", callback_data="close_market")])
    return kb

async def show_market(m, i, items):
    if i < 0: i = 0
    if i >= len(items): i = len(items)-1
    iid, name, price, fid = items[i]
    await m.answer_photo(photo=fid, caption=f"👕 {name}\n\n💰 Цена: {format_balance(price)}",
        parse_mode=ParseMode.HTML, reply_markup=market_kb(i, len(items), iid, price))

@dp.callback_query(F.data.regexp(r"^mp_\d+$"))
async def mkt_prev(cb: CallbackQuery):
    i = int(cb.data.split("_")[1]); items = get_market_items()
    ni = max(0, i-1); iid, name, price, fid = items[ni]
    try:
        await cb.message.edit_media(media=InputMediaPhoto(media=fid, caption=f"👕 {name}\n\n💰 Цена: {format_balance(price)}", parse_mode=ParseMode.HTML),
            reply_markup=market_kb(ni, len(items), iid, price))
    except:
        try: await cb.message.edit_caption(caption=f"👕 {name}\n\n💰 Цена: {format_balance(price)}", parse_mode=ParseMode.HTML, reply_markup=market_kb(ni, len(items), iid, price))
        except: pass
    await cb.answer()

@dp.callback_query(F.data.regexp(r"^mn_\d+$"))
async def mkt_next(cb: CallbackQuery):
    i = int(cb.data.split("_")[1]); items = get_market_items()
    ni = min(len(items)-1, i+1); iid, name, price, fid = items[ni]
    try:
        await cb.message.edit_media(media=InputMediaPhoto(media=fid, caption=f"👕 {name}\n\n💰 Цена: {format_balance(price)}", parse_mode=ParseMode.HTML),
            reply_markup=market_kb(ni, len(items), iid, price))
    except:
        try: await cb.message.edit_caption(caption=f"👕 {name}\n\n💰 Цена: {format_balance(price)}", parse_mode=ParseMode.HTML, reply_markup=market_kb(ni, len(items), iid, price))
        except: pass
    await cb.answer()

@dp.callback_query(F.data.startswith("mbuy_"))
async def mkt_buy(cb: CallbackQuery):
    uid = cb.from_user.id; parts = cb.data.split("_"); iid = int(parts[1])
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id = ?", (uid,))
    u = c.fetchone()
    if not u: await cb.answer("Сначала зарегистрируйся через /start", show_alert=True); conn.close(); return
    c.execute("SELECT name,price,file_id FROM market_items WHERE id = ?", (iid,))
    it = c.fetchone()
    if not it: await cb.answer("Сет не найден", show_alert=True); conn.close(); return
    name, price, fid = it
    if u[0] < price:
        await cb.answer(f"❌ Не хватает! Нужно {format_balance(price)}", show_alert=True); conn.close(); return
    nb = u[0] - price
    c.execute("UPDATE users SET balance = ? WHERE user_id = ?", (nb, uid))
    add_to_wardrobe(c, uid, 'market', iid, name, fid, price)
    conn.commit(); conn.close(); avatar_cache.pop(uid, None)
    await cb.answer("✅ Куплено! Открой шкаф чтобы надеть", show_alert=True)
    items = get_market_items()
    idx = next((i for i, it in enumerate(items) if it[0] == iid), 0)
    try:
        await cb.message.edit_media(media=InputMediaPhoto(media=fid,
            caption=f"✅ ПОКУПКА УСПЕШНА!\n\nСет <b>{name}</b> отправлен в шкаф\n💰 Потрачено: {format_balance(price)}\n💳 Остаток: {format_balance(nb)}\n\n📦 Открой шкаф чтобы надеть",
            parse_mode=ParseMode.HTML), reply_markup=market_kb(idx, len(items), iid, price))
    except:
        try: await cb.message.edit_caption(caption=f"✅ ПОКУПКА УСПЕШНА!\n\nСет <b>{name}</b> отправлен в шкаф\n💰 Потрачено: {format_balance(price)}\n💳 Остаток: {format_balance(nb)}", parse_mode=ParseMode.HTML, reply_markup=market_kb(idx, len(items), iid, price))
        except: pass

@dp.callback_query(F.data == "close_market")
async def mkt_close(cb: CallbackQuery):
    try: await cb.message.delete()
    except: pass
    await cb.answer()

@dp.message(Command("удалить_маркет"))
async def del_market(m: Message):
    if not is_admin(m.from_user.id): return
    args = m.text.split()
    if len(args) < 2: await m.answer("❌ Пример: /удалить_маркет 1"); return
    try: iid = int(args[1])
    except: return
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT id,name FROM market_items WHERE id = ?", (iid,))
    item = c.fetchone()
    if not item: await m.answer(f"❌ Сета с ID {iid} не существует"); conn.close(); return
    c.execute("DELETE FROM market_items WHERE id = ?", (iid,))
    conn.commit(); conn.close()
    await m.answer(f"✅ Сет '{item[1]}' (ID: {iid}) удалён!")

@dp.message(Command("изменить_цену"))
async def ch_price(m: Message):
    if not is_admin(m.from_user.id): return
    args = m.text.split()
    if len(args) < 3: await m.answer("❌ Пример: /изменить_цену 1 50000000000"); return
    try: iid = int(args[1]); price = parse_amount(args[2])
    except: return
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT id,name FROM market_items WHERE id = ?", (iid,))
    item = c.fetchone()
    if not item: await m.answer(f"❌ Сета с ID {iid} не существует"); conn.close(); return
    c.execute("UPDATE market_items SET price = ? WHERE id = ?", (price, iid))
    conn.commit(); conn.close()
    await m.answer(f"✅ Цена сета '{item[1]}' изменена на {format_balance(price)}!")

# ========= ДОМА =========
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
            [InlineKeyboardButton(text="🏠 Магазин домов", callback_data="hshop")],
            [InlineKeyboardButton(text="❌ Закрыть", callback_data="close_house")]])
        await m.answer_photo(photo=hfid, caption=f"🏠 ТВОЙ ДОМ — {hname}\n\n💰 Куплен за: {format_balance(price)}\n💸 Можно продать за: {format_balance(sp)} (35%)", parse_mode=ParseMode.HTML, reply_markup=kb)
    else: await show_hshop(m, 0)

def house_kb(i, total, hid):
    kb = InlineKeyboardMarkup(inline_keyboard=[]); nav = []
    if i > 0: nav.append(InlineKeyboardButton(text="◀️ Назад", callback_data=f"hp_{i}"))
    if i < total-1: nav.append(InlineKeyboardButton(text="Вперёд ▶️", callback_data=f"hn_{i}"))
    if nav: kb.inline_keyboard.append(nav)
    kb.inline_keyboard.append([InlineKeyboardButton(text="💰 Купить дом", callback_data=f"hbuy_{hid}")])
    kb.inline_keyboard.append([InlineKeyboardButton(text="❌ Закрыть", callback_data="close_house")])
    return kb

async def show_hshop(m, i, edit=False):
    items = get_houses()
    if not items: await m.answer("🏠 Магазин домов пуст", parse_mode=ParseMode.HTML); return
    if i < 0: i = 0
    if i >= len(items): i = len(items)-1
    hid, price, fid, hname = items[i]
    cap = f"🏠 ДОМ #{hid}" + (f" — {hname}" if hname else "") + f"\n\n💰 Цена: {format_balance(price)}"
    kb = house_kb(i, len(items), hid)
    if edit:
        try: await m.edit_media(InputMediaPhoto(media=fid, caption=cap, parse_mode=ParseMode.HTML), reply_markup=kb)
        except:
            try: await m.edit_caption(caption=cap, parse_mode=ParseMode.HTML, reply_markup=kb)
            except: pass
    else: await m.answer_photo(photo=fid, caption=cap, parse_mode=ParseMode.HTML, reply_markup=kb)

@dp.callback_query(F.data == "hshop")
async def hshop_cb(cb: CallbackQuery):
    try: await cb.message.delete()
    except: pass
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
    if not u: await cb.answer("Сначала зарегистрируйся через /start", show_alert=True); conn.close(); return
    c.execute("SELECT price,file_id,name FROM houses WHERE id = ?", (hid,))
    h = c.fetchone()
    if not h: await cb.answer("Дом не найден", show_alert=True); conn.close(); return
    price, fid, hname = h
    if u[0] < price:
        await cb.answer(f"❌ Не хватает! Нужно {format_balance(price)}", show_alert=True); conn.close(); return
    nb = u[0] - price; dn = hname or f"Дом #{hid}"
    c.execute("UPDATE users SET balance = ? WHERE user_id = ?", (nb, uid))
    add_to_wardrobe(c, uid, 'house', hid, dn, fid, price)
    conn.commit(); conn.close(); avatar_cache.pop(uid, None)
    await cb.answer("✅ Куплено! Открой шкаф чтобы надеть", show_alert=True)
    try:
        await cb.message.edit_caption(caption=f"✅ ПОКУПКА УСПЕШНА!\n\nТы приобрёл {dn}\n💰 Потрачено: {format_balance(price)}\n💳 Остаток: {format_balance(nb)}\n\n📦 Открой шкаф чтобы надеть", parse_mode=ParseMode.HTML)
    except: pass

@dp.callback_query(F.data.startswith("shsell_"))
async def shsell_cb(cb: CallbackQuery):
    uid = cb.from_user.id
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT file_id FROM equipped_house WHERE user_id = ?", (uid,))
    ch = c.fetchone()
    if not ch or not ch[0]: await cb.answer("❌ У тебя нет дома", show_alert=True); conn.close(); return
    c.execute("SELECT price FROM houses WHERE file_id = ?", (ch[0],))
    hd = c.fetchone()
    if not hd: await cb.answer("❌ Дом не найден", show_alert=True); conn.close(); return
    sp = int(hd[0]*0.35)
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (sp, uid))
    c.execute("DELETE FROM equipped_house WHERE user_id = ?", (uid,))
    conn.commit(); conn.close(); avatar_cache.pop(uid, None)
    try: await cb.message.edit_caption(caption=f"✅ Дом продан за {format_balance(sp)}!", parse_mode=ParseMode.HTML)
    except: pass
    await cb.answer(f"✅ Продан!", show_alert=True)

@dp.callback_query(F.data == "close_house")
async def close_h_cb(cb: CallbackQuery):
    try: await cb.message.delete()
    except: pass
    await cb.answer()

@dp.message(Command("дом"))
async def add_house_cmd(m: Message, state: FSMContext):
    if not is_admin(m.from_user.id): return
    args = m.text.split(maxsplit=3)
    if len(args) < 3: await m.answer("❌ Пример: /дом 1 100ккк 'Люкс'"); return
    try:
        hid = int(args[1]); price = parse_amount(args[2])
        name = args[3].strip("'\"") if len(args) >= 4 else ""
    except Exception as e: await m.answer(f"❌ Ошибка: {e}"); return
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT MAX(id) FROM houses")
    mx = c.fetchone()[0] or 0; conn.close()
    if hid != mx+1: await m.answer(f"❌ ID должен идти по порядку! Следующий ID: {mx+1}"); return
    await state.update_data(hid=hid, price=price, hname=name)
    await state.set_state(HouseImageState.waiting_image)
    await m.answer(f"📸 Отправь фото для дома #{hid}\n💰 Цена: {format_balance(price)}" + (f"\n📝 Название: {name}" if name else ""))

@dp.message(HouseImageState.waiting_image)
async def save_house_img(m: Message, state: FSMContext):
    if not m.photo: await m.answer("❌ Отправь фото!"); return
    d = await state.get_data(); fid = m.photo[-1].file_id
    conn = get_db_connection(); c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO houses (id,price,file_id,name,created_by,created_at) VALUES (?,?,?,?,?,?)",
        (d["hid"], d["price"], fid, d.get("hname",""), m.from_user.id, datetime.now().isoformat()))
    conn.commit(); conn.close(); await state.clear()
    await m.answer(f"✅ Дом #{d['hid']} добавлен!" + (f" — {d.get('hname')}" if d.get("hname") else "") + f"\n💰 {format_balance(d['price'])}")

@dp.message(Command("удалить_дом"))
async def del_house_admin_cmd(m: Message):
    if not is_admin(m.from_user.id): return
    args = m.text.split()
    if len(args) < 2: await m.answer("❌ Пример: /удалить_дом 1"); return
    try: hid = int(args[1])
    except: return
    conn = get_db_connection(); c = conn.cursor()
    c.execute("DELETE FROM houses WHERE id = ?", (hid,))
    conn.commit(); conn.close()
    await m.answer(f"✅ Дом #{hid} удалён!")

@dp.message(Command("изменить_цену_дома"))
async def ch_hprice(m: Message, cmd: CommandObject):
    if not is_admin(m.from_user.id): return
    args = (cmd.args or "").split()
    if len(args) < 2: await m.answer("❌ /изменить_цену_дома [номер] [сумма]"); return
    try: hid = int(args[0]); price = parse_amount(args[1])
    except: return
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT id FROM houses WHERE id = ?", (hid,))
    if not c.fetchone(): await m.answer(f"❌ Дома с ID {hid} нет"); conn.close(); return
    c.execute("UPDATE houses SET price = ? WHERE id = ?", (price, hid))
    conn.commit(); conn.close()
    await m.answer(f"✅ Цена дома #{hid} → {format_balance(price)}")

# ========= МАРКЕТ ИГРОКОВ (PM) =========
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
    return (max(0, PM_DAILY_LIMIT_SET - int(r.get("set",0))), max(0, PM_DAILY_LIMIT_HOUSE - int(r.get("house",0))))

def pm_inc(kind):
    conn = get_db_connection(); c = conn.cursor()
    c.execute("UPDATE pm_daily SET sold_today = sold_today + 1 WHERE kind = ?", (kind,))
    conn.commit(); conn.close()

def pm_kb():
    sl, hl = pm_limits()
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"👕 Сеты ({sl}/{PM_DAILY_LIMIT_SET})", callback_data="pm_sets_0")],
        [InlineKeyboardButton(text=f"🏠 Дома ({hl}/{PM_DAILY_LIMIT_HOUSE})", callback_data="pm_houses_0")],
        [InlineKeyboardButton(text="➕ Продать сет", callback_data="pm_add_set")],
        [InlineKeyboardButton(text="➕ Продать дом", callback_data="pm_add_house")],
        [InlineKeyboardButton(text="📦 Мои лоты", callback_data="pm_mylots")],
        [InlineKeyboardButton(text="❌ Закрыть", callback_data="close_pm")]])

@dp.message(F.text.lower() == "🛒 маркет игроков")
async def pm_cmd(m: Message):
    if await check_stopped(m) or await check_banned(m): return
    uid = m.from_user.id
    if not await user_exists(uid): await m.answer("Сначала зарегистрируйся через /start"); return
    _bump_usage(uid)
    try: await m.answer_photo(photo=PM_IMAGE_URL, caption="🛒 МАРКЕТ ИГРОКОВ\n\nВыбери отдел:", reply_markup=pm_kb())
    except: await m.answer("🛒 МАРКЕТ ИГРОКОВ\n\nВыбери отдел:", reply_markup=pm_kb())

@dp.callback_query(F.data == "close_pm")
async def close_pm_cb(cb: CallbackQuery):
    try: await cb.message.delete()
    except: pass
    await cb.answer()

async def pm_show_list(m, kind, page, edit=False):
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT id,seller_id,item_name,file_id,price FROM pm_items WHERE kind = ? AND sold = 0 AND wardrobe_slot IS NOT NULL ORDER BY id DESC", (kind,))
    rows_all = c.fetchall(); rows = []
    for r in rows_all:
        c.execute("SELECT 1 FROM wardrobe w JOIN pm_items p ON p.seller_id = w.user_id AND p.wardrobe_slot = w.slot WHERE p.id = ?", (r[0],))
        if c.fetchone(): rows.append(r)
    conn.close()
    if not rows:
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="pm_back")]])
        if edit:
            try: await m.edit_caption(caption="🛒 Пока нет лотов", reply_markup=kb)
            except: pass
        else: await m.answer("🛒 Пока нет лотов", reply_markup=kb)
        return
    total = len(rows)
    if page < 0: page = 0
    if page >= total: page = total-1
    lot_id, seller_id, name, fid, price = rows[page]
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT nick FROM users WHERE user_id = ?", (seller_id,))
    sr = c.fetchone(); conn.close()
    sn = sr[0] if sr else str(seller_id)
    cap = f"{'👕' if kind == 'set' else '🏠'} {name}\n💰 Цена: {format_balance(price)}\n👤 Продавец: {get_nick_link(seller_id, sn)}\n📄 Лот {page+1}/{total}"
    kb_rows = []; nav = []
    if page > 0: nav.append(InlineKeyboardButton(text="◀️", callback_data=f"pm_{kind}s_{page-1}"))
    if page < total-1: nav.append(InlineKeyboardButton(text="▶️", callback_data=f"pm_{kind}s_{page+1}"))
    if nav: kb_rows.append(nav)
    kb_rows.append([InlineKeyboardButton(text="💰 Купить", callback_data=f"pm_buy_{lot_id}")])
    kb_rows.append([InlineKeyboardButton(text="◀️ Назад", callback_data="pm_back")])
    kb_rows.append([InlineKeyboardButton(text="❌ Закрыть", callback_data="close_pm")])
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
    try: await cb.message.answer_photo(photo=PM_IMAGE_URL, caption="🛒 МАРКЕТ ИГРОКОВ\n\nВыбери отдел:", reply_markup=pm_kb())
    except: await cb.message.answer("🛒 МАРКЕТ ИГРОКОВ\n\nВыбери отдел:", reply_markup=pm_kb())
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

async def pm_picker(cb, kind):
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
        kb_rows.append([InlineKeyboardButton(text=f"{emoji} {name} (лот #{s})", callback_data=f"pm_pick_{kind}_{s}")])
    kb_rows.append([InlineKeyboardButton(text="❌ Отмена", callback_data="pm_back")])
    if len(kb_rows) == 1:
        await cb.answer("У тебя нет подходящих предметов в шкафу", show_alert=True); return
    title = "👕 Выбери СЕТ из шкафа:" if kind == "set" else "🏠 Выбери ДОМ из шкафа:"
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
    if not row: await cb.answer("❌ Предмет не найден", show_alert=True); conn.close(); return
    name, fid, _ = row; conn.close()
    pm_states[uid] = {"kind": kind, "slot": s, "name": name, "file_id": fid}
    await cb.message.answer(f"{'👕' if kind == 'set' else '🏠'} {name}\n\n💰 Напиши цену продажи (например 5ккк или 5000000000):")
    await state.set_state(PMAddState.waiting_price)
    await cb.answer()

@dp.message(PMAddState.waiting_price)
async def pm_price_msg(m: Message, state: FSMContext):
    uid = m.from_user.id; st = pm_states.get(uid)
    if not st: await state.clear(); return
    try:
        price = parse_amount(m.text.strip())
        if price <= 0: raise ValueError
    except: await m.answer("❌ Неверная цена"); return
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT 1 FROM wardrobe WHERE user_id = ? AND slot = ?", (uid, st["slot"]))
    if not c.fetchone():
        await m.answer("❌ Предмета уже нет в шкафу"); conn.close(); pm_states.pop(uid, None); await state.clear(); return
    c.execute("INSERT INTO pm_items (seller_id,kind,item_name,file_id,price,created_at,wardrobe_slot) VALUES (?,?,?,?,?,?,?)",
        (uid, st["kind"], st["name"], st["file_id"], price, datetime.now().isoformat(), st["slot"]))
    conn.commit(); conn.close()
    pm_states.pop(uid, None); await state.clear()
    await m.answer(f"✅ Лот выставлен!\n\n{'👕' if st['kind'] == 'set' else '🏠'} {st['name']}\n💰 Цена: {format_balance(price)}\n📉 Комиссия: 15%")

@dp.callback_query(F.data.startswith("pm_buy_"))
async def pm_buy_cb(cb: CallbackQuery):
    lot_id = int(cb.data.split("_")[2]); buyer_id = cb.from_user.id
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT seller_id,kind,item_name,file_id,price,sold,wardrobe_slot FROM pm_items WHERE id = ?", (lot_id,))
    row = c.fetchone()
    if not row: await cb.answer("❌ Лот не найден", show_alert=True); conn.close(); return
    seller_id, kind, name, fid, price, sold, wslot = row
    if sold: await cb.answer("❌ Уже продан", show_alert=True); conn.close(); return
    if seller_id == buyer_id: await cb.answer("❌ Это твой лот", show_alert=True); conn.close(); return
    sl, hl = pm_limits()
    if kind == "set" and sl <= 0: await cb.answer(f"❌ Лимит сетов исчерпан", show_alert=True); conn.close(); return
    if kind == "house" and hl <= 0: await cb.answer(f"❌ Лимит домов исчерпан", show_alert=True); conn.close(); return
    c.execute("SELECT balance FROM users WHERE user_id = ?", (buyer_id,))
    b = c.fetchone()
    if not b: await cb.answer("Сначала /start", show_alert=True); conn.close(); return
    if b[0] < price: await cb.answer(f"❌ Не хватает {format_balance(price)}", show_alert=True); conn.close(); return
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
    await cb.message.answer(f"✅ ЛОТ КУПЛЕН!\n\n{'👕' if kind == 'set' else '🏠'} {name}\n💰 Оплачено: {format_balance(price)}\n📦 Отправлено в шкаф")
    try: await bot.send_message(seller_id, f"💸 Твой лот продан!\n\n{'👕' if kind == 'set' else '🏠'} {name}\n💰 Получено (минус 15% комиссия): {format_balance(sg)}")
    except: pass

@dp.callback_query(F.data == "pm_mylots")
async def pm_mylots_cb(cb: CallbackQuery):
    uid = cb.from_user.id
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT id,kind,item_name,price,sold FROM pm_items WHERE seller_id = ? ORDER BY id DESC", (uid,))
    rows = c.fetchall(); conn.close()
    if not rows: await cb.answer("У тебя нет лотов", show_alert=True); return
    txt = "📦 ТВОИ ЛОТЫ\n\n"
    for lid, k, n, p, s in rows:
        e = "👕" if k == "set" else "🏠"; st = "🟢 продаётся" if not s else "🔴 продан"
        txt += f"#{lid} {e} {n} — {format_balance(p)} — {st}\n"
    await cb.message.answer(txt, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Закрыть", callback_data="close_pm")]]))
    await cb.answer()

# ========= БАНК =========
@dp.message(F.text.lower().in_(["банк", "🏦 банк"]))
async def bank_cmd(m: Message):
    if await check_stopped(m) or await check_banned(m): return
    uid = m.from_user.id; _bump_usage(uid)
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id = ?", (uid,))
    u = c.fetchone()
    if not u: await m.answer("Сначала зарегистрируйся через /start"); conn.close(); return
    bal = u[0]
    c.execute("SELECT deposit,deposit_time FROM bank WHERE user_id = ?", (uid,))
    b = c.fetchone(); conn.close()
    txt = f"🏦 БАНК\n\n💳 Твой баланс: {format_balance(bal)}\n"
    if b and b[0] > 0:
        d, dts = b; dt = datetime.fromisoformat(dts)
        if datetime.now() >= dt + timedelta(hours=24):
            i = int(d*0.1)
            txt += f"💰 Вклад: {format_balance(d)}\n📈 Проценты: +{format_balance(i)}\n💵 Итого: {format_balance(d+i)}"
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💵 Положить", callback_data="bank_dep")],
                [InlineKeyboardButton(text="💰 Забрать + проценты", callback_data="bank_wd")]])
        else:
            tl = (dt + timedelta(hours=24)) - datetime.now()
            txt += f"💰 Вклад: {format_balance(d)}\n⏳ До снятия: {tl.seconds//3600}ч {(tl.seconds%3600)//60}мин\n📈 Проценты: 10% через 24ч"
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💵 Положить", callback_data="bank_dep")],
                [InlineKeyboardButton(text="⏳ Забрать (ожидание)", callback_data="bank_pend")]])
    else:
        txt += "\n💰 Вклад: нет активного вклада\n\n💡 Вклад под 10% на 24 часа"
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="💵 Положить деньги", callback_data="bank_dep")]])
    await m.answer(txt, parse_mode=ParseMode.HTML, reply_markup=kb)

@dp.callback_query(F.data == "bank_dep")
async def bank_dep_cb(cb: CallbackQuery, state: FSMContext):
    uid = cb.from_user.id
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id = ?", (uid,))
    bal = c.fetchone()[0]; conn.close()
    md = bal // 2
    if md < 1_000_000: await cb.answer("❌ Минимальный вклад: 1.000.000", show_alert=True); return
    await cb.message.answer(f"💵 ПОЛОЖИТЬ ВКЛАД\n\nБаланс: {format_balance(bal)}\nМаксимум: {format_balance(md)}\nМинимум: {format_balance(1_000_000)}\n\nВведи сумму:")
    await state.set_state(BankDepositState.waiting_amount)
    await cb.answer()

@dp.message(BankDepositState.waiting_amount)
async def bank_dep_msg(m: Message, state: FSMContext):
    if await check_banned(m): return
    uid = m.from_user.id
    try: amount = parse_amount(m.text.strip())
    except: await m.answer("❌ Неверная сумма"); return
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
    await m.answer(f"✅ Вклад: {format_balance(amount)}\n💰 Через 24ч получишь {format_balance(int(amount*1.1))}\n💳 Баланс: {format_balance(nb)}",
        reply_markup=get_full_keyboard() if is_private(m) else None)
    await state.clear()

@dp.callback_query(F.data == "bank_wd")
async def bank_wd_cb(cb: CallbackQuery):
    uid = cb.from_user.id
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT deposit,deposit_time FROM bank WHERE user_id = ?", (uid,))
    b = c.fetchone()
    if not b or b[0] == 0: await cb.answer("❌ Нет активного вклада", show_alert=True); conn.close(); return
    d, dts = b; dt = datetime.fromisoformat(dts)
    if datetime.now() < dt + timedelta(hours=24):
        await cb.answer("❌ Вклад ещё не готов", show_alert=True); conn.close(); return
    i = int(d*0.1); total = d + i
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (total, uid))
    c.execute("DELETE FROM bank WHERE user_id = ?", (uid,))
    conn.commit()
    c.execute("SELECT balance FROM users WHERE user_id = ?", (uid,))
    nb = c.fetchone()[0]; conn.close()
    try: await cb.message.edit_text(f"✅ Вклад снят!\n💰 {format_balance(d)}\n📈 +{format_balance(i)}\n💵 Итого: {format_balance(total)}\n💳 Баланс: {format_balance(nb)}", parse_mode=ParseMode.HTML)
    except: pass
    await cb.answer()

@dp.callback_query(F.data == "bank_pend")
async def bank_pend_cb(cb: CallbackQuery): await cb.answer("❌ Вклад ещё не готов! Нужно 24 часа", show_alert=True)

# ========= РУЛЕТКА =========
RUL_ALIASES = {
    "красное":"кра","красный":"кра","красная":"кра","красн":"кра","крас":"кра","кра":"кра",
    "чёрное":"чер","черное":"чер","чёрный":"чер","черный":"чер","чёрная":"чер","черная":"чер",
    "чёрн":"чер","черн":"чер","чёр":"чер","чер":"чер",
    "чётное":"чет","четное":"чет","чётный":"чет","четный":"чет","чёт":"чет","чет":"чет",
    "нечётное":"неч","нечетное":"неч","нечётный":"неч","нечетный":"неч","нечёт":"неч","нечет":"неч","неч":"неч",
    "больше":"бол","большое":"бол","бол":"бол","меньше":"мал","малое":"мал","мал":"мал",
    "ноль":"0","нуль":"0","зеро":"0","zero":"0","0":"0",
    "1-12":"d1","1д":"d1","д1":"d1","дюжина1":"d1","13-24":"d2","2д":"d2","д2":"d2","дюжина2":"d2",
    "25-36":"d3","3д":"d3","д3":"d3","дюжина3":"d3",
    "ряд1":"r1","ряд2":"r2","ряд3":"r3","r1":"r1","r2":"r2","r3":"r3"}

def _normalize_rul(word):
    w = word.lower().strip()
    if w.isdigit() and 1 <= int(w) <= 36: return w
    if w in RUL_ALIASES: return RUL_ALIASES[w]
    for p in ("столб","столбец","столбик","col","column","с"):
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
        await m.answer("Ставки запрещены здесь", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🎰 Играть в казино", url=CASINO_LINK)]]))
        return
    uid = m.from_user.id; track_command(m.chat.id, uid, "рул"); _bump_usage(uid)
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT nick,balance FROM users WHERE user_id = ?", (uid,))
    u = c.fetchone(); conn.close()
    if not u: await m.answer("Сначала зарегистрируйся через /start"); return
    parts = m.text.lower().split()
    if len(parts) < 3: await m.answer("❌ Пример: рулетка чёрное 1000000"); return
    bt, ba = parse_rul_bet(parts)
    if bt is None: await m.answer("❌ Неверный тип или сумма"); return
    if ba == "ALL": ba = u[1]
    if ba <= 0: await m.answer("❌ Ставка должна быть больше 0"); return
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
    if win:
        cap = f"{get_nick_link(uid, u[0])}, Молодец, ты выиграл {format_balance(wa)}!\nБаланс — {format_balance(nb)}"
    else:
        cap = f"{get_nick_link(uid, u[0])}, К сожалению ты проиграл {format_balance(ba)}!\nБаланс — {format_balance(nb)}"
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
    ams = parts[1]
    if ams == "все":
        conn = get_db_connection(); c = conn.cursor()
        c.execute("SELECT balance FROM users WHERE user_id = ?", (uid,))
        amount = c.fetchone()[0]; conn.close()
    else:
        try: amount = parse_amount(ams)
        except: await m.answer("❌ Сумма"); return
    if amount <= 0: return
    track_command(m.chat.id, uid, f"ряд{row}"); _bump_usage(uid)
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT nick,balance FROM users WHERE user_id = ?", (uid,))
    u = c.fetchone(); conn.close()
    if not u: await m.answer("Сначала зарегистрируйся через /start"); return
    if u[1] < amount: await m.answer(f"❌ Баланс: {format_balance(u[1])}"); return
    rn = random.randint(0, 36); win = rn in _row_numbers(row)
    wa = amount*3 if win else 0; nb = u[1] - amount + wa
    conn = get_db_connection(); c = conn.cursor()
    c.execute("UPDATE users SET balance = ? WHERE user_id = ?", (nb, uid))
    conn.commit()
    c.execute("SELECT file_id FROM roulette_images WHERE number = ?", (rn,))
    ir = c.fetchone(); conn.close()
    cap = f"{get_nick_link(uid, u[0])}, РЯД {row} {'🎯 +' + format_balance(wa) if win else '❌ -' + format_balance(amount)}\nБаланс — {format_balance(nb)}"
    if ir and ir[0]: await m.answer_photo(photo=ir[0], caption=cap, parse_mode=ParseMode.HTML)
    else: await m.answer(cap, parse_mode=ParseMode.HTML)

@dp.message(F.text.lower().startswith("слот"))
async def slot_cmd(m: Message):
    if await check_stopped(m) or await check_banned(m): return
    if is_private(m):
        await m.answer("Ставки запрещены здесь", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🎰 Играть в казино", url=CASINO_LINK)]]))
        return
    uid = m.from_user.id; track_command(m.chat.id, uid, "слот"); _bump_usage(uid)
    if uid in last_slot_time and (datetime.now() - last_slot_time[uid]).total_seconds() < SLOT_COOLDOWN:
        await m.answer(f"⏳ Подожди {int(SLOT_COOLDOWN - (datetime.now() - last_slot_time[uid]).total_seconds())} секунд!"); return
    parts = m.text.split()
    if len(parts) < 2: await m.answer("❌ Пример: слот 1000000"); return
    ams = parts[1].lower()
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT balance,nick FROM users WHERE user_id = ?", (uid,))
    u = c.fetchone(); conn.close()
    if not u: await m.answer("Сначала зарегистрируйся через /start"); return
    if ams == "все": amount = u[0]
    else:
        try: amount = parse_amount(parts[1])
        except: await m.answer("❌ Неверная сумма"); return
    if u[0] < amount: await m.answer(f"❌ Не хватает! Баланс: {format_balance(u[0])}"); return
    last_slot_time[uid] = datetime.now()
    sm = await m.answer_dice(emoji="🎰"); await asyncio.sleep(3.1)
    if sm.dice.value in {1,22,43,64}:
        wa = int(amount*14.5); nb = u[0] + wa
        conn = get_db_connection(); c = conn.cursor()
        c.execute("UPDATE users SET balance = ? WHERE user_id = ?", (nb, uid)); conn.commit(); conn.close()
        await m.answer(f"{get_nick_link(uid,u[1])}, 🎉 ДЖЕКПОТ! 🎉 Ты выиграл {format_balance(wa)} (x14.5)!\nБаланс — {format_balance(nb)}", parse_mode=ParseMode.HTML)
    else:
        nb = u[0] - amount
        conn = get_db_connection(); c = conn.cursor()
        c.execute("UPDATE users SET balance = ? WHERE user_id = ?", (nb, uid)); conn.commit(); conn.close()
        await m.answer(f"{get_nick_link(uid,u[1])}, К сожалению ты проиграл {format_balance(amount)} (x0).\nБаланс — {format_balance(nb)}", parse_mode=ParseMode.HTML)

# ========= КОСТИ =========
@dp.message(F.text.lower().startswith("кости"))
async def dice_cmd(m: Message):
    if await check_stopped(m) or await check_banned(m): return
    if is_private(m):
        await m.answer("Ставки запрещены здесь", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🎰 Играть в казино", url=CASINO_LINK)]]))
        return
    uid = m.from_user.id; track_command(m.chat.id, uid, "кости"); _bump_usage(uid)
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT nick,balance FROM users WHERE user_id = ?", (uid,))
    s = c.fetchone(); conn.close()
    if not s: await m.answer("Сначала /start"); return
    if not m.reply_to_message: await m.answer("❌ В ответ на сообщение игрока"); return
    parts = m.text.split()
    if len(parts) < 2: await m.answer("❌ Пример: кости 1000000"); return
    ams = parts[1].lower()
    if ams == "все": amount = s[1]
    else:
        try: amount = parse_amount(parts[1])
        except: await m.answer("❌ Неверная сумма"); return
    if amount <= 0: await m.answer("❌ Сумма > 0"); return
    opp = m.reply_to_message.from_user
    if opp.id == uid: await m.answer("❌ Нельзя с собой"); return
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE user_id = ?", (opp.id,))
    if not c.fetchone(): await m.answer("❌ Игрок не зарегистрирован"); conn.close(); return
    conn.close()
    if s[1] < amount: await m.answer(f"❌ Не хватает. Баланс: {format_balance(s[1])}"); return
    gid = f"{uid}_{opp.id}_{int(datetime.now().timestamp())}"
    dice_games[gid] = {"challenger":uid,"opponent":opp.id,"amount":amount,"challenger_nick":s[0],"status":"waiting","chat_id":m.chat.id}
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Принять", callback_data=f"dacc_{gid}"),
         InlineKeyboardButton(text="❌ Отказаться", callback_data=f"ddec_{gid}")]])
    try: await m.reply_photo(photo=DICE_IMAGE_URL, caption=f"🎲 {get_nick_link(uid, s[0])} вызывает тебя на кости!\n💰 Ставка: {format_balance(amount)}", parse_mode=ParseMode.HTML, reply_markup=kb)
    except: await m.reply(f"🎲 {get_nick_link(uid, s[0])} вызывает тебя на кости!\n💰 Ставка: {format_balance(amount)}", parse_mode=ParseMode.HTML, reply_markup=kb)

@dp.callback_query(F.data.startswith("dacc_"))
async def dice_acc_cb(cb: CallbackQuery):
    gid = cb.data.replace("dacc_",""); g = dice_games.get(gid)
    if not g or cb.from_user.id != g["opponent"]: await cb.answer("❌ Не твой вызов!", show_alert=True); return
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id IN (?,?)", (g["challenger"], g["opponent"]))
    bals = [r[0] for r in c.fetchall()]
    if min(bals) < g["amount"]: await cb.answer("❌ Не хватает средств", show_alert=True); del dice_games[gid]; conn.close(); return
    c.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (g["amount"], g["challenger"]))
    c.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (g["amount"], g["opponent"]))
    conn.commit()
    c.execute("SELECT nick FROM users WHERE user_id = ?", (g["challenger"],))
    cn = c.fetchone()[0]
    c.execute("SELECT nick FROM users WHERE user_id = ?", (g["opponent"],))
    on = c.fetchone()[0]
    conn.close()
    try: await cb.message.delete()
    except: pass
    await bot.send_message(g["chat_id"], f"🎲 Кубик кидает: {cn}")
    c1 = await bot.send_dice(g["chat_id"]); await asyncio.sleep(4)
    await bot.send_message(g["chat_id"], f"🎲 Кубик кидает: {on}")
    c2 = await bot.send_dice(g["chat_id"]); await asyncio.sleep(4)
    v1, v2 = c1.dice.value, c2.dice.value
    conn = get_db_connection(); c = conn.cursor()
    if v1 > v2:
        wa = g["amount"]*2
        c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (wa, g["challenger"]))
        res = f"🏆 Победил: {get_nick_link(g['challenger'], cn)}\n💰 Выигрыш: {format_balance(wa)}"
    elif v2 > v1:
        wa = g["amount"]*2
        c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (wa, g["opponent"]))
        res = f"🏆 Победил: {get_nick_link(g['opponent'], on)}\n💰 Выигрыш: {format_balance(wa)}"
    else:
        c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (g["amount"], g["challenger"]))
        c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (g["amount"], g["opponent"]))
        res = "🤝 Ничья! Ставки возвращены"
    conn.commit(); conn.close()
    await bot.send_message(g["chat_id"], f"🎲 РЕЗУЛЬТАТ\n\n{cn}: {v1}\n{on}: {v2}\n\n{res}", parse_mode=ParseMode.HTML)
    del dice_games[gid]; await cb.answer()

@dp.callback_query(F.data.startswith("ddec_"))
async def dice_dec_cb(cb: CallbackQuery):
    gid = cb.data.replace("ddec_",""); g = dice_games.get(gid)
    if not g or cb.from_user.id != g["opponent"]: await cb.answer("❌ Не твой вызов!", show_alert=True); return
    try: await cb.message.edit_caption(caption="❌ Вызов отклонён")
    except:
        try: await cb.message.edit_text("❌ Вызов отклонён")
        except: pass
    if gid in dice_games: del dice_games[gid]
    await cb.answer() # ========= РАБОТА =========
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

REBUS_WORDS = [{"word":"КОТ","letters":["К","О","Т"]},{"word":"ДОМ","letters":["Д","О","М"]},
    {"word":"ЛЕС","letters":["Л","Е","С"]},{"word":"ИГРА","letters":["И","Г","Р","А"]},
    {"word":"СТОЛ","letters":["С","Т","О","Л"]},{"word":"ВОДА","letters":["В","О","Д","А"]},
    {"word":"МОРЕ","letters":["М","О","Р","Е"]},{"word":"ГОРА","letters":["Г","О","Р","А"]},
    {"word":"КИНО","letters":["К","И","Н","О"]},{"word":"БАНК","letters":["Б","А","Н","К"]},
    {"word":"ОКНО","letters":["О","К","Н","О"]},{"word":"ЛИСТ","letters":["Л","И","С","Т"]},
    {"word":"ПАРК","letters":["П","А","Р","К"]},{"word":"СНЕГ","letters":["С","Н","Е","Г"]},
    {"word":"ЗИМА","letters":["З","И","М","А"]},{"word":"ЛЕТО","letters":["Л","Е","Т","О"]},
    {"word":"ХЛЕБ","letters":["Х","Л","Е","Б"]},{"word":"МОСТ","letters":["М","О","С","Т"]},
    {"word":"КЛЮЧ","letters":["К","Л","Ю","Ч"]},{"word":"СТУЛ","letters":["С","Т","У","Л"]},
    {"word":"РЫБА","letters":["Р","Ы","Б","А"]},{"word":"ТЕНЬ","letters":["Т","Е","Н","Ь"]},
    {"word":"НОЧЬ","letters":["Н","О","Ч","Ь"]},{"word":"ДЕНЬ","letters":["Д","Е","Н","Ь"]}]
REBUS_BLOCKLIST = {"БИЗ","Я","БОНУС","РАБОТА","ПОМОЩЬ","МЕНЮ","ЗАКУПКИ","КАРТА","НАСТРОЙКИ",
    "НАЗАД","ШКАФ","ПРОМОКОД","ДОНАТ","СТАТА","ТОП","БАНК","СЛОТ","РУЛ","КОСТИ","КЛИКЕР","ТАКСИ"}

def gen_rebus():
    d = random.choice(REBUS_WORDS); L = d["letters"].copy(); random.shuffle(L)
    return {"word":d["word"],"s":" ".join(L)}

@dp.message(F.text.lower().in_(["💼 работа", "работа"]))
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
    await m.answer("💼 РАБОТА\n\nВыбери тип работы:", parse_mode=ParseMode.HTML, reply_markup=kb)

@dp.callback_query(F.data == "close_work")
async def close_work_cb(cb: CallbackQuery, state: FSMContext):
    try: await cb.message.delete()
    except: pass
    await state.clear(); await cb.answer()

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
        [InlineKeyboardButton(text=f"🖱️ Кликнуть (+100кк) ({clicks}/{CLICKER_MAX_CLICKS})", callback_data="cli_click")],
        [InlineKeyboardButton(text="❌ Закрыть", callback_data="close_work")]])
    try: await cb.message.edit_text(f"🖱️ КЛИКЕР\n\nКликов: {clicks}/{CLICKER_MAX_CLICKS}\n+{format_balance(CLICKER_REWARD)} за клик", parse_mode=ParseMode.HTML, reply_markup=kb)
    except: pass
    await cb.answer()

@dp.callback_query(F.data == "cli_click")
async def cli_click_cb(cb: CallbackQuery):
    uid = cb.from_user.id
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT clicks FROM clicker WHERE user_id = ?", (uid,))
    r = c.fetchone(); clicks = r[0] if r else 0
    if clicks >= CLICKER_MAX_CLICKS:
        await cb.answer("❌ Лимит!", show_alert=True); conn.close(); return
    nc = clicks + 1
    if r: c.execute("UPDATE clicker SET clicks = ? WHERE user_id = ?", (nc, uid))
    else: c.execute("INSERT INTO clicker (user_id,clicks) VALUES (?,?)", (uid, nc))
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (CLICKER_REWARD, uid))
    conn.commit()
    c.execute("SELECT balance FROM users WHERE user_id = ?", (uid,))
    nb = c.fetchone()[0]; conn.close()
    await cb.answer(f"✅ +{format_balance(CLICKER_REWARD)}!", show_alert=True)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🖱️ Кликнуть ({nc}/{CLICKER_MAX_CLICKS})", callback_data="cli_click")],
        [InlineKeyboardButton(text="❌ Закрыть", callback_data="close_work")]])
    try: await cb.message.edit_text(f"🖱️ КЛИКЕР\n\nКликов: {nc}/{CLICKER_MAX_CLICKS}\n💳 {format_balance(nb)}", parse_mode=ParseMode.HTML, reply_markup=kb)
    except: pass

@dp.callback_query(F.data == "tch_start")
async def tch_start_cb(cb: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, выйти на смену", callback_data="tch_yes")],
        [InlineKeyboardButton(text="❌ Нет", callback_data="close_work")]])
    try: await cb.message.edit_text(f"👨‍🏫 УЧИТЕЛЬ\n\nХочешь ли ты выйти на смену?\n\n⚠️ Правильный ответ: +2.5ккк\n⚠️ Неправильный ответ: -5ккк\n⚠️ После 4 ошибок работа завершится", parse_mode=ParseMode.HTML, reply_markup=kb)
    except: pass
    await cb.answer()

@dp.callback_query(F.data == "tch_yes")
async def tch_yes_cb(cb: CallbackQuery, state: FSMContext):
    uid = cb.from_user.id
    q = gen_math(); ic = random.choice([True, False]); da = q["c"] if ic else q["w"]
    teacher_sessions[uid] = {"q":q, "ic":ic, "cc":0, "wc":0}
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Правильно", callback_data="tch_ok"),
         InlineKeyboardButton(text="❌ Неверно", callback_data="tch_no")],
        [InlineKeyboardButton(text="❌ Закончить", callback_data="close_work")]])
    try: await cb.message.edit_text(f"👨‍🏫 УЧИТЕЛЬ\n\nУченик решил пример: {q['p']}\nЕго ответ: {da}\n\nОн ответил правильно?", parse_mode=ParseMode.HTML, reply_markup=kb)
    except: pass
    await state.set_state(TeacherState.waiting_answer)
    await cb.answer()

@dp.callback_query(F.data.startswith("tch_"))
async def tch_ans_cb(cb: CallbackQuery, state: FSMContext):
    if cb.data in ("tch_start","tch_yes"): return
    uid = cb.from_user.id; at = cb.data.split("_")[1]
    s = teacher_sessions.get(uid)
    if not s: await cb.answer("❌ Сессия потеряна!", show_alert=True); await state.clear(); return
    uc = at == "ok"; ic = s["ic"]
    conn = get_db_connection(); c = conn.cursor()
    if uc == ic:
        r = 2_500_000_000
        c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (r, uid))
        s["cc"] = s.get("cc",0) + 1
    else:
        p = TEACHER_PENALTY
        c.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (p, uid))
        s["wc"] = s.get("wc",0) + 1
    conn.commit(); conn.close()
    await cb.answer("✅" if uc == ic else "❌", show_alert=False)
    if s.get("wc",0) >= 4:
        try: await cb.message.edit_text(f"❌ Ты ошибся 4 раза! Работа завершена.\n💰 Заработано: {format_balance(s.get('cc',0)*2_500_000_000)}")
        except: pass
        teacher_sessions.pop(uid, None); await state.clear(); return
    q = gen_math(); ic2 = random.choice([True, False]); da = q["c"] if ic2 else q["w"]
    teacher_sessions[uid] = {"q":q,"ic":ic2,"cc":s.get("cc",0),"wc":s.get("wc",0)}
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Правильно", callback_data="tch_ok"),
         InlineKeyboardButton(text="❌ Неверно", callback_data="tch_no")],
        [InlineKeyboardButton(text="❌ Закончить", callback_data="close_work")]])
    try: await cb.message.edit_text(f"👨‍🏫 УЧИТЕЛЬ\n\nУченик решил пример: {q['p']}\nЕго ответ: {da}\n\nОн ответил правильно?", parse_mode=ParseMode.HTML, reply_markup=kb)
    except: pass
    await state.set_state(TeacherState.waiting_answer)

@dp.callback_query(F.data == "reb_start")
async def reb_start_cb(cb: CallbackQuery, state: FSMContext):
    uid = cb.from_user.id
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT rebus_uses,rebus_reset FROM users WHERE user_id = ?", (uid,))
    row = c.fetchone(); conn.close()
    if not row:
        await cb.answer("Сначала /start", show_alert=True); return
    uses, reset_str = row
    now = datetime.now()
    reset = datetime.fromisoformat(reset_str) if reset_str else None
    if reset and now - reset >= REBUS_COOLDOWN:
        conn = get_db_connection(); c = conn.cursor()
        c.execute("UPDATE users SET rebus_uses = 0, rebus_reset = NULL WHERE user_id = ?", (uid,))
        conn.commit(); conn.close()
        uses = 0
    if uses >= REBUS_LIMIT:
        if reset:
            rem = REBUS_COOLDOWN - (now - reset)
            h = rem.seconds // 3600; m = (rem.seconds % 3600) // 60
            await cb.answer(f"❌ Лимит исчерпан! Жди {h}ч {m}мин", show_alert=True)
        else:
            await cb.answer("❌ Лимит исчерпан!", show_alert=True)
        return
    conn = get_db_connection(); c = conn.cursor()
    if uses == 0:
        c.execute("UPDATE users SET rebus_uses = 1, rebus_reset = ? WHERE user_id = ?", (now.isoformat(), uid))
    else:
        c.execute("UPDATE users SET rebus_uses = rebus_uses + 1 WHERE user_id = ?", (uid,))
    conn.commit(); conn.close()
    r = gen_rebus()
    rebus_sessions[uid] = {"word":r["word"],"cc":0,"wc":0}
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Закончить работу", callback_data="close_work")]])
    try: await cb.message.edit_text(f"🧩 РЕБУСЫ 🧩\n\nИз букв нужно составить слово:\n\n<code>{r['s']}</code>\n\nНапиши слово в чат!\n\n💰 +{format_balance(1_000_000_000)} за правильный ответ\n📊 Использовано: {uses+1}/{REBUS_LIMIT}\n\n✅ 6 правильных — работа завершится\n❌ 6 неправильных — работа завершится", parse_mode=ParseMode.HTML, reply_markup=kb)
    except: pass
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
            await m.answer(f"🎉 Ты отгадал 6 слов! Работа завершена.\n💰 Заработано: {format_balance(6_000_000_000)}")
            rebus_sessions.pop(uid, None); await state.clear(); return
        r = gen_rebus()
        rebus_sessions[uid] = {"word":r["word"],"cc":cc,"wc":s.get("wc",0)}
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Закончить работу", callback_data="close_work")]])
        await m.answer(f"✅ ПРАВИЛЬНО!\n\nСлово: <b>{s['word']}</b>\n💰 +{format_balance(1_000_000_000)}\n\n✅ Правильных: {cc}/6\n\n🧩 Следующий:\n<code>{r['s']}</code>", parse_mode=ParseMode.HTML, reply_markup=kb)
    else:
        wc = s.get("wc",0) + 1
        if wc >= 6:
            await m.answer("❌ Ты ошибся 6 раз! Работа завершена."); rebus_sessions.pop(uid, None); await state.clear(); return
        r = gen_rebus()
        rebus_sessions[uid] = {"word":r["word"],"cc":s.get("cc",0),"wc":wc}
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Закончить работу", callback_data="close_work")]])
        await m.answer(f"❌ НЕПРАВИЛЬНО!\n\nТвой ответ: <b>{ans}</b>\nПравильно: <b>{s['word']}</b>\n\n❌ Ошибок: {wc}/6\n\n🧩 Новый:\n<code>{r['s']}</code>", parse_mode=ParseMode.HTML, reply_markup=kb)

# ========= ТАКСИ (НОВОЕ: 2 этапа + таймер + события в пути) =========
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

def _fmt_timer(sec):
    sec = max(0, int(sec))
    m, s = divmod(sec, 60)
    return f"{m}м {s}с" if m else f"{s}с"

@dp.callback_query(F.data == "taxi_open")
async def taxi_open_cb(cb: CallbackQuery):
    uid = cb.from_user.id
    if not await user_exists(uid): await cb.answer("Сначала зарегистрируйся через /start", show_alert=True); return
    try: await cb.message.delete()
    except: pass
    await show_taxi(cb.message, uid)

async def show_taxi(m, uid):
    left = taxi_left(uid)
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT balance,taxi_earnings,taxi_current_order,taxi_stars FROM users WHERE user_id = ?", (uid,))
    u = c.fetchone(); conn.close()
    if not u: await m.answer("Сначала зарегистрируйся через /start"); return
    bal, earn, cur, stars = u
    ride = taxi_active_rides.get(uid)
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    cap = ""
    if ride:
        # активная поездка — таймер
        end = _pdt(ride["end_time"])
        rem = int((end - datetime.now()).total_seconds()) if end else 0
        phase = ride["phase"]
        phase_txt = "🚗 Едем к клиенту" if phase == "to_client" else "🚕 Везём клиента"
        cap = (f"🚕 ТАКСИ — В ПУТИ\n\n"
               f"{phase_txt}\n"
               f"⏱ Осталось: {_fmt_timer(rem)}\n"
               f"💰 Оплата: {format_balance(ride['payout'])}\n"
               f"🌟 Звёзды: {stars}\n")
        if ride.get("events"):
            cap += "\n📋 События в пути:\n" + "\n".join(f"• {e}" for e in ride["events"][-5:])
        kb.inline_keyboard.append([InlineKeyboardButton(text="🔄 Обновить таймер", callback_data="taxi_refresh")])
    elif left <= 0:
        kb.inline_keyboard.append([InlineKeyboardButton(text=f"🚗 Арендовать авто ({format_balance(TAXI_RENT_PRICE)}/{TAXI_RENT_MINUTES} мин)", callback_data="taxi_rent")])
        cap = (f"🚕 ТАКСИ\n\n"
               f"❌ Нет активной аренды.\n"
               f"💰 Стоимость: {format_balance(TAXI_RENT_PRICE)} / {TAXI_RENT_MINUTES} мин\n"
               f"🌟 Рейтинг: {stars}/{TAXI_STARS_GOAL}")
    else:
        cap = (f"🚕 ТАКСИ\n\n"
               f"⏳ Аренда: {_fmt_timer(left)}\n"
               f"💰 Заработано: {format_balance(earn or 0)}\n"
               f"🌟 Рейтинг: {stars}/{TAXI_STARS_GOAL}\n")
        if cur: cap += f"\n🚗 Заказ #{cur} в пути..."
        else:
            cap += "\n✅ Можно брать заказ"
            kb.inline_keyboard.append([InlineKeyboardButton(text="🚕 Взять заказ", callback_data="taxi_take")])
        kb.inline_keyboard.append([InlineKeyboardButton(text="💰 Забрать заработок", callback_data="taxi_collect")])
        kb.inline_keyboard.append([InlineKeyboardButton(text="🔄 Обновить", callback_data="taxi_refresh")])
    try:
        await m.answer_photo(photo=TAXI_PHOTOS["car"], caption=cap, parse_mode=ParseMode.HTML, reply_markup=kb)
    except:
        await m.answer(cap, parse_mode=ParseMode.HTML, reply_markup=kb)

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
    if taxi_left(uid) <= 0: await cb.answer("❌ Сначала арендуйте!", show_alert=True); return
    if uid in taxi_active_rides: await cb.answer("❌ Уже в поездке!", show_alert=True); return
    b = []
    for oid, o in TAXI_ORDERS.items():
        b.append([InlineKeyboardButton(text=f"{o['emoji']} {o['name']} ({o['seconds']}с+{o['seconds']//2}с) — {format_balance(o['min_payout'])}..{format_balance(o['max_payout'])}", callback_data=f"taxi_ord_{oid}")])
    b.append([InlineKeyboardButton(text="◀️ Назад", callback_data="taxi_back")])
    try:
        await cb.message.answer_photo(photo=TAXI_PHOTOS["destination"], caption="🚕 Выбери тип заказа:", reply_markup=InlineKeyboardMarkup(inline_keyboard=b))
    except:
        await cb.message.answer("🚕 Выбери тип заказа:", reply_markup=InlineKeyboardMarkup(inline_keyboard=b))
    await cb.answer()

@dp.callback_query(F.data.startswith("taxi_ord_"))
async def taxi_process_cb(cb: CallbackQuery):
    uid = cb.from_user.id
    try: oid = int(cb.data.split("_")[2])
    except: await cb.answer("❌"); return
    if oid not in TAXI_ORDERS: await cb.answer("❌"); return
    if uid in taxi_order_locks: await cb.answer("⏳ Уже выполняется", show_alert=True); return
    if uid in taxi_active_rides: await cb.answer("❌ Уже в поездке!", show_alert=True); return
    if taxi_left(uid) <= 0: await cb.answer("❌ Аренда не активна!", show_alert=True); return
    order = TAXI_ORDERS[oid]
    payout = random.randint(order["min_payout"], order["max_payout"])
    to_client_sec = order["seconds"]
    to_dest_sec = max(20, order["seconds"] // 2)
    end_time = datetime.now() + timedelta(seconds=to_client_sec)
    taxi_active_rides[uid] = {
        "phase": "to_client",
        "end_time": end_time.isoformat(),
        "payout": payout,
        "order_type": oid,
        "events": [],
        "chat_id": cb.message.chat.id,
        "to_client_sec": to_client_sec,
        "to_dest_sec": to_dest_sec,
        "rent_started": datetime.now().isoformat(),
    }
    conn = get_db_connection(); c = conn.cursor()
    c.execute("UPDATE users SET taxi_current_order = ? WHERE user_id = ?", (oid, uid))
    conn.commit(); conn.close()
    await cb.answer(f"🚗 Заказ принят!")
    try: await cb.message.delete()
    except: pass
    try:
        await cb.message.answer_photo(
            photo=TAXI_PHOTOS["passenger"],
            caption=f"🚕 {order['emoji']} {order['name']}\n\n🚗 **Этап 1/2 — едем к клиенту**\n⏱ {_fmt_timer(to_client_sec)}\n💰 Оплата: {format_balance(payout)}\n\nНажми «🔄 Обновить таймер» чтобы увидеть остаток",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔄 Обновить таймер", callback_data="taxi_refresh")]])
        )
    except: pass
    asyncio.create_task(_taxi_drive_loop(uid))

async def _taxi_drive_loop(uid):
    """Едет к клиенту → событие → везёт к месту → событие → финал."""
    ride = taxi_active_rides.get(uid)
    if not ride: return
    try:
        # Фаза 1: к клиенту
        await asyncio.sleep(ride["to_client_sec"])
        ride = taxi_active_rides.get(uid)
        if not ride: return
        ev1 = random.choice(TAXI_EVENTS)
        ride["events"].append(f"{ev1['text']} ({ev1['stars']:+d}🌟)")
        conn = get_db_connection(); c = conn.cursor()
        c.execute("UPDATE users SET taxi_stars = MAX(0, COALESCE(taxi_stars,0) + ?) WHERE user_id = ?", (ev1["stars"], uid))
        conn.commit(); conn.close()
        try:
            await bot.send_message(uid, f"🚗 Приехали к клиенту!\n{ev1['text']} ({ev1['stars']:+d}🌟)")
        except: pass
        # Фаза 2: везём клиента
        ride["phase"] = "to_dest"
        ride["end_time"] = (datetime.now() + timedelta(seconds=ride["to_dest_sec"])).isoformat()
        await asyncio.sleep(ride["to_dest_sec"])
        ride = taxi_active_rides.get(uid)
        if not ride: return
        ev2 = random.choice(TAXI_EVENTS)
        ride["events"].append(f"{ev2['text']} ({ev2['stars']:+d}🌟)")
        conn = get_db_connection(); c = conn.cursor()
        c.execute("UPDATE users SET taxi_stars = MAX(0, COALESCE(taxi_stars,0) + ?) WHERE user_id = ?", (ev2["stars"], uid))
        c.execute("UPDATE users SET taxi_earnings = COALESCE(taxi_earnings,0) + ?, taxi_current_order = NULL WHERE user_id = ?", (ride["payout"], uid))
        c.execute("INSERT INTO taxi_orders (user_id,order_type,earnings,completed,created_at) VALUES (?,?,?,1,?)", (uid, ride["order_type"], ride["payout"], datetime.now().isoformat()))
        conn.commit(); conn.close()
        try:
            await bot.send_message(uid, f"✅ Заказ выполнен!\n\n📋 События в пути:\n" + "\n".join(f"• {e}" for e in ride["events"]) + f"\n\n💰 +{format_balance(ride['payout'])}\n💵 Можно забрать через «💰 Забрать заработок»")
        except: pass
    finally:
        taxi_active_rides.pop(uid, None)
        taxi_order_locks.discard(uid)

@dp.callback_query(F.data == "taxi_refresh")
async def taxi_refresh_cb(cb: CallbackQuery):
    uid = cb.from_user.id
    ride = taxi_active_rides.get(uid)
    if ride:
        end = _pdt(ride["end_time"])
        rem = int((end - datetime.now()).total_seconds()) if end else 0
        phase = ride["phase"]
        phase_txt = "🚗 Едем к клиенту" if phase == "to_client" else "🚕 Везём клиента"
        cap = (f"🚕 ТАКСИ — В ПУТИ\n\n"
               f"{phase_txt}\n"
               f"⏱ Осталось: {_fmt_timer(rem)}\n"
               f"💰 Оплата: {format_balance(ride['payout'])}\n")
        if ride.get("events"):
            cap += "\n📋 События:\n" + "\n".join(f"• {e}" for e in ride["events"][-5:])
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔄 Обновить таймер", callback_data="taxi_refresh")]])
        try:
            await cb.message.edit_caption(caption=cap, parse_mode=ParseMode.HTML, reply_markup=kb)
        except:
            try: await cb.message.answer(cap, parse_mode=ParseMode.HTML, reply_markup=kb)
            except: pass
        await cb.answer("🔄 Обновлено")
        return
    # нет активной — просто перерисовываем
    try: await cb.message.delete()
    except: pass
    await show_taxi(cb.message, uid); await cb.answer()

@dp.callback_query(F.data == "taxi_collect")
async def taxi_collect_cb(cb: CallbackQuery):
    uid = cb.from_user.id; last = taxi_collect_last.get(uid)
    if last and datetime.now() - last < TAXI_COLLECT_COOLDOWN:
        rem = TAXI_COLLECT_COOLDOWN - (datetime.now() - last)
        await cb.answer(f"⏳ Забрать через {rem.seconds//3600}ч {(rem.seconds%3600)//60}мин", show_alert=True); return
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT taxi_earnings FROM users WHERE user_id = ?", (uid,))
    r = c.fetchone(); earn = int(r[0] or 0) if r else 0
    if earn < TAXI_COLLECT_MIN:
        await cb.answer(f"❌ Минимум: {format_balance(TAXI_COLLECT_MIN)}", show_alert=True); conn.close(); return
    take = min(earn, TAXI_COLLECT_CAP)
    c.execute("UPDATE users SET balance = balance + ?, taxi_earnings = taxi_earnings - ? WHERE user_id = ?", (take, take, uid))
    conn.commit(); conn.close()
    taxi_collect_last[uid] = datetime.now()
    await cb.answer(f"💰 Получено {format_balance(take)}!", show_alert=True)
    try: await cb.message.delete()
    except: pass

@dp.callback_query(F.data == "taxi_back")
async def taxi_back_cb(cb: CallbackQuery):
    try: await cb.message.delete()
    except: pass
    await cb.answer()

# ========= КАРТА =========
@dp.message(F.text.lower().in_(["карта", "🗺️ карта"]))
async def map_cmd(m: Message):
    if await check_stopped(m) or await check_banned(m): return
    uid = m.from_user.id
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT city,travel_end_time FROM users WHERE user_id = ?", (uid,))
    u = c.fetchone(); conn.close()
    if not u: await m.answer("Сначала зарегистрируйся через /start"); return
    cc, tet = u
    if tet:
        te = datetime.fromisoformat(tet)
        if datetime.now() < te:
            rem = (te - datetime.now()).seconds
            await m.answer(f"🚗 Вы уже в пути! Осталось: {rem//60}мин {rem%60}сек"); return
    track_command(m.chat.id, uid, "карта"); _bump_usage(uid)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚗 Рублёвка (40с)", callback_data="trv_рублёвка"),
         InlineKeyboardButton(text="🚗 Лыткарино (50с)", callback_data="trv_лыткарино")],
        [InlineKeyboardButton(text="🚗 Арзамас (35с)", callback_data="trv_арзамас"),
         InlineKeyboardButton(text="🚗 Батырево (30с)", callback_data="trv_батырево")],
        [InlineKeyboardButton(text="🚗 Южный (45с)", callback_data="trv_южный"),
         InlineKeyboardButton(text="🚗 Нижнегородск (60с)", callback_data="trv_нижнегородск")],
        [InlineKeyboardButton(text="❌ Закрыть", callback_data="close_map")]])
    cn = CITIES.get(cc, {}).get("name", "Рублёвка")
    await m.answer_photo(photo=MAP_IMAGE_URL, caption=f"🗺️ КАРТА ГОРОДОВ\n\n📍 Текущее: {cn}\n\nВыбери город:", parse_mode=ParseMode.HTML, reply_markup=kb)

@dp.callback_query(F.data.startswith("trv_"))
async def travel_cb(cb: CallbackQuery):
    uid = cb.from_user.id
    ck = cb.data.split("_", 1)[1]
    cd = CITIES.get(ck)
    if not cd: await cb.answer("Город не найден", show_alert=True); return
    te = datetime.now() + timedelta(seconds=cd["travel_time"])
    conn = get_db_connection(); c = conn.cursor()
    c.execute("UPDATE users SET city = ?, travel_end_time = ? WHERE user_id = ?", (ck, te.isoformat(), uid))
    conn.commit(); conn.close()
    try: await cb.message.delete()
    except: pass
    await cb.message.answer_photo(photo=TRAVEL_IMAGE_URL, caption=f"🚗 Вас подобрал таксист!\n📍 {cd['name']}\n⏱ {cd['travel_time']}с", parse_mode=ParseMode.HTML)
    await asyncio.sleep(cd["travel_time"])
    conn = get_db_connection(); c = conn.cursor()
    c.execute("UPDATE users SET travel_end_time = NULL WHERE user_id = ?", (uid,))
    conn.commit(); conn.close()
    img = CITY_ARRIVAL_IMAGES.get(ck, MAP_IMAGE_URL)
    try: await cb.message.answer_photo(photo=img, caption=f"📍 Вы прибыли в {cd['name']}!")
    except: await cb.message.answer(f"📍 Вы прибыли в {cd['name']}!")

@dp.callback_query(F.data == "close_map")
async def close_map_cb(cb: CallbackQuery):
    try: await cb.message.delete()
    except: pass
    await cb.answer()

# ========= ПРОМОКОДЫ =========
@dp.message(F.text.lower().in_(["🎫 промокод", "промокод"]))
async def promo_cmd(m: Message, state: FSMContext):
    if await check_stopped(m) or await check_banned(m): return
    uid = m.from_user.id; _bump_usage(uid)
    if not await check_subscribed(uid):
        await m.answer(f"Для активации промокода подпишись на канал:\n{CHANNEL_LINK}"); return
    await m.answer("📝 Введи название промокода:")
    await state.set_state(PromoCodeState.waiting_input)

@dp.message(PromoCodeState.waiting_input)
async def promo_act(m: Message, state: FSMContext):
    if await check_banned(m): return
    uid = m.from_user.id; text = m.text.strip()
    if not await check_subscribed(uid):
        await m.answer(f"Подпишись на канал: {CHANNEL_LINK}"); await state.clear(); return
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT amount,activations_left FROM promocodes WHERE name = ?", (text,))
    pc = c.fetchone()
    if not pc: await m.answer("❌ Промокод не найден"); conn.close(); await state.clear(); return
    if pc[1] <= 0: await m.answer("❌ Промокод использован"); conn.close(); await state.clear(); return
    c.execute("UPDATE promocodes SET activations_left = activations_left - 1 WHERE name = ?", (text,))
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (pc[0], uid))
    conn.commit(); conn.close()
    await m.answer(f"🍻 Активирован промокод: {text}\nНачислено: {format_balance(pc[0])}", reply_markup=get_full_keyboard() if is_private(m) else None)
    await state.clear()

@dp.message(Command("промо"))
async def create_promo(m: Message):
    if not is_admin(m.from_user.id): return
    args = m.text.split()
    if len(args) < 4: await m.answer("❌ Пример: /промо summer2024 1000000 10"); return
    name = args[1]
    try: amount = parse_amount(args[2]); ac = int(args[3])
    except: await m.answer("❌ Неверные параметры"); return
    conn = get_db_connection(); c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO promocodes (name,amount,activations_left,total_activations,creator_id,created_at) VALUES (?,?,?,?,?,?)", (name, amount, ac, ac, m.from_user.id, datetime.now().isoformat()))
    conn.commit(); conn.close()
    await m.answer(f"🎫 ПРОМОКОД СОЗДАН\n\n🔑 {name}\n💰 {format_balance(amount)}\n🎟️ {ac}", parse_mode=ParseMode.HTML)

async def handle_gift_activation(m, gid):
    uid = m.from_user.id
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE user_id = ?", (uid,))
    if not c.fetchone(): await m.answer("Сначала /start"); conn.close(); return
    c.execute("SELECT amount,activations_left FROM gifts WHERE gift_id = ?", (gid,))
    g = c.fetchone()
    if not g or g[1] <= 0: await m.answer("❌ Подарок недействителен"); conn.close(); return
    amount = g[0]
    c.execute("UPDATE gifts SET activations_left = 0 WHERE gift_id = ?", (gid,))
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, uid))
    c.execute("SELECT nick FROM users WHERE user_id = ?", (uid,))
    nr = c.fetchone(); nick = nr[0] if nr else str(uid)
    conn.commit(); conn.close()
    await m.answer(f"🎉 Ты получил {format_balance(amount)}!", reply_markup=get_full_keyboard() if is_private(m) else None)
    await notify_owners(f"🎁 <b>ПОДАРОК</b>\n\n👤 {get_nick_link(uid, nick)}\n💰 {format_balance(amount)}")

async def notify_owners(text):
    for oid in OWNERS:
        try: await bot.send_message(oid, text, parse_mode=ParseMode.HTML)
        except: pass

async def handle_check_activation(m, cid):
    uid = m.from_user.id
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE user_id = ?", (uid,))
    if not c.fetchone(): await m.answer("Сначала /start"); conn.close(); return
    c.execute("SELECT 1 FROM check_activations WHERE check_id = ? AND user_id = ?", (cid, uid))
    if c.fetchone(): await m.answer("❌ Ты уже активировал этот чек"); conn.close(); return
    c.execute("SELECT amount,activations_left,creator_id FROM checks WHERE check_id = ?", (cid,))
    ch = c.fetchone()
    if not ch or ch[1] <= 0: await m.answer("❌ Чек недействителен"); conn.close(); return
    amount, _, creator = ch
    c.execute("UPDATE checks SET activations_left = activations_left - 1 WHERE check_id = ?", (cid,))
    c.execute("INSERT OR IGNORE INTO check_activations (check_id,user_id) VALUES (?,?)", (cid, uid))
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, uid))
    c.execute("SELECT nick FROM users WHERE user_id = ?", (uid,))
    nr = c.fetchone(); nick = nr[0] if nr else str(uid)
    c.execute("SELECT activations_left FROM checks WHERE check_id = ?", (cid,))
    left = c.fetchone()[0]
    conn.commit(); conn.close()
    await m.answer(f"🎉 Ты получил {format_balance(amount)}!", reply_markup=get_full_keyboard() if is_private(m) else None)
    if creator:
        try: await bot.send_message(creator, f"🧾 <b>ЧЕК АКТИВИРОВАН</b>\n\n👤 {get_nick_link(uid, nick)}\n💰 {format_balance(amount)}\n🔒 Осталось: {left}", parse_mode=ParseMode.HTML)
        except: pass

@dp.message(Command("подарок"))
async def create_gift_cmd(m: Message):
    if not is_admin(m.from_user.id): return
    args = m.text.split()
    if len(args) < 2: await m.answer("❌ /подарок 1000000"); return
    try: amount = parse_amount(args[1])
    except: return
    gid = f"gift_{int(datetime.now().timestamp())}"
    conn = get_db_connection(); c = conn.cursor()
    c.execute("INSERT INTO gifts (gift_id,amount,activations_left,creator_id,created_at) VALUES (?,?,1,?,?)", (gid, amount, m.from_user.id, datetime.now().isoformat()))
    conn.commit(); conn.close()
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="💰 Активировать", url=f"https://t.me/{BOT_USERNAME}?start={gid}")]])
    await m.answer(f"🎁 ПОДАРОК СОЗДАН!\n💰 {format_balance(amount)}", parse_mode=ParseMode.HTML, reply_markup=kb)

@dp.message(Command("чек"))
async def create_check_cmd(m: Message):
    if not is_admin(m.from_user.id): return
    args = m.text.split()
    if len(args) < 3: await m.answer("❌ /чек 1000000 5"); return
    try: amount = parse_amount(args[1]); ac = int(args[2])
    except: await m.answer("❌ Неверные параметры"); return
    cid = f"check_{int(datetime.now().timestamp())}"
    conn = get_db_connection(); c = conn.cursor()
    c.execute("INSERT INTO checks (check_id,amount,activations_left,total_activations,creator_id,created_at) VALUES (?,?,?,?,?,?)", (cid, amount, ac, ac, m.from_user.id, datetime.now().isoformat()))
    conn.commit(); conn.close()
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="💰 Активировать", url=f"https://t.me/{BOT_USERNAME}?start={cid}")]])
    text = f"🧾 НОВЫЙ ЧЕК!\n\n💰 {format_balance(amount)}\n🎟️ Активаций: {ac}"
    try:
        await bot.send_message(f"@{CHANNEL_USERNAME}", text, parse_mode=ParseMode.HTML, reply_markup=kb)
        await m.answer("✅ Чек опубликован!")
    except Exception as e: await m.answer(f"⚠️ {e}\n\n{text}", parse_mode=ParseMode.HTML, reply_markup=kb)

# ========= ПЕРЕВОДЫ =========
transfer_words = ["кинуть","дать","передать","скинуть","перевести"]
async def find_user(ident):
    ident = ident.strip().lstrip('@').lower()
    if not ident: return None
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT user_id,nick FROM users WHERE LOWER(nick) = ?", (ident,))
    r = c.fetchone()
    if r: conn.close(); return r
    c.execute("SELECT user_id,nick FROM users WHERE LOWER(username) = ?", (ident,))
    r = c.fetchone()
    if r: conn.close(); return r
    if ident.isdigit():
        c.execute("SELECT user_id,nick FROM users WHERE user_id = ?", (int(ident),))
        r = c.fetchone()
        if r: conn.close(); return r
    conn.close()
    try:
        chat = await bot.get_chat(f"@{ident}")
        if chat and chat.id:
            conn2 = get_db_connection(); c2 = conn2.cursor()
            c2.execute("SELECT user_id,nick FROM users WHERE user_id = ?", (chat.id,))
            r2 = c2.fetchone()
            if r2: conn2.close(); return r2
            conn2.close()
            return (chat.id, chat.username or chat.full_name or str(chat.id))
    except: pass
    return None

@dp.message(F.text.lower().split()[0].in_(transfer_words))
async def transfer_cmd(m: Message):
    if await check_stopped(m) or await check_banned(m): return
    await update_username(m.from_user.id, m.from_user.username)
    uid = m.from_user.id; parts = m.text.split()
    target = None; ams = None
    if m.reply_to_message:
        target = m.reply_to_message.from_user
        if len(parts) >= 2: ams = parts[1]
    else:
        if len(parts) >= 3:
            found = await find_user(parts[1].replace("@","").strip())
            if found:
                target = type('obj',(object,),{'id':found[0],'nick':found[1]}); ams = parts[2]
    if not target:
        await m.answer("❌ Пользователь не найден.\n💡 Пример: <code>перевести @username 1000000</code>", parse_mode=ParseMode.HTML); return
    if not ams: await m.answer("❌ Укажи сумму"); return
    if ams.lower() == "все":
        conn = get_db_connection(); c = conn.cursor()
        c.execute("SELECT balance FROM users WHERE user_id = ?", (uid,))
        amount = c.fetchone()[0]
        conn.close()
    else:
        try: amount = parse_amount(str(ams))
        except: await m.answer("❌ Неверная сумма"); return
    if amount <= 0: await m.answer("❌ Сумма > 0"); return
    if target.id == uid: await m.answer("❌ Нельзя себе"); return
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT nick,balance FROM users WHERE user_id = ?", (uid,))
    s = c.fetchone()
    c.execute("SELECT nick,balance FROM users WHERE user_id = ?", (target.id,))
    r = c.fetchone()
    c.execute("SELECT confirm_transfer FROM settings WHERE user_id = ?", (uid,))
    ct = c.fetchone(); conn.close()
    if not s: await m.answer("Сначала /start"); return
    if not r: await m.answer("❌ Не зарегистрирован"); return
    if s[1] < amount: await m.answer(f"❌ Не хватает. Баланс: {format_balance(s[1])}"); return
    if ct and ct[0]:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"ctfrm_{target.id}_{amount}"),
             InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_transfer")]])
        await m.answer(f"❓ Перевести {format_balance(amount)} игроку {get_nick_link(target.id, r[0])}?", parse_mode=ParseMode.HTML, reply_markup=kb)
        return
    ns = s[1] - amount; nr = r[1] + amount
    conn = get_db_connection(); c = conn.cursor()
    c.execute("UPDATE users SET balance = ? WHERE user_id = ?", (ns, uid))
    c.execute("UPDATE users SET balance = ? WHERE user_id = ?", (nr, target.id))
    conn.commit(); conn.close()
    await m.answer(f"✅ Перевёл {format_balance(amount)} игроку {get_nick_link(target.id, r[0])}\n💳 Баланс: {format_balance(ns)}", parse_mode=ParseMode.HTML)
    try: await bot.send_message(target.id, f"💸 Ты получил {format_balance(amount)} от {get_nick_link(uid, s[0])}\n💳 Баланс: {format_balance(nr)}", parse_mode=ParseMode.HTML)
    except: pass

@dp.callback_query(F.data.startswith("ctfrm_"))
async def confirm_transfer_cb(cb: CallbackQuery):
    parts = cb.data.split("_")
    target_id = int(parts[1]); amount = int(parts[2]); uid = cb.from_user.id
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT nick,balance FROM users WHERE user_id = ?", (uid,))
    s = c.fetchone()
    c.execute("SELECT nick,balance FROM users WHERE user_id = ?", (target_id,))
    r = c.fetchone(); conn.close()
    if not s or not r: await cb.answer("❌ Ошибка", show_alert=True); return
    if s[1] < amount: await cb.answer("❌ Недостаточно средств", show_alert=True); return
    ns = s[1] - amount; nr = r[1] + amount
    conn = get_db_connection(); c = conn.cursor()
    c.execute("UPDATE users SET balance = ? WHERE user_id = ?", (ns, uid))
    c.execute("UPDATE users SET balance = ? WHERE user_id = ?", (nr, target_id))
    conn.commit(); conn.close()
    try: await cb.message.edit_text(f"✅ Переведено {format_balance(amount)} игроку {r[0]}\n💳 Твой баланс: {format_balance(ns)}")
    except: pass
    try: await bot.send_message(target_id, f"💸 Ты получил {format_balance(amount)} от {get_nick_link(uid, s[0])}\n💳 Баланс: {format_balance(nr)}", parse_mode=ParseMode.HTML)
    except: pass
    await cb.answer()

@dp.callback_query(F.data == "cancel_transfer")
async def cancel_transfer_cb(cb: CallbackQuery):
    try: await cb.message.delete()
    except: pass
    await cb.answer()

# ========= ИГРА «ЧИСЛО» =========
@dp.message(F.text.regexp(r"(?i)^число\s+\S+"))
async def number_cmd(m: Message):
    if await check_stopped(m) or await check_banned(m): return
    uid = m.from_user.id
    if not await user_exists(uid): await m.answer("Сначала /start"); return
    parts = m.text.split()
    if len(parts) < 2: await m.answer("❌ Пример: число 10ккк"); return
    ams = parts[1].lower()
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id = ?", (uid,))
    u = c.fetchone()
    if not u: await m.answer("Сначала /start"); conn.close(); return
    if ams == "все": amount = u[0]
    else:
        try: amount = parse_amount(parts[1])
        except: await m.answer("❌ Неверная сумма"); conn.close(); return
    if amount <= 0: await m.answer("❌ Сумма > 0"); conn.close(); return
    if u[0] < amount: await m.answer("❌ Недостаточно средств!"); conn.close(); return
    if m.chat.id in number_games and number_games[m.chat.id].get("active"):
        await m.answer("❌ В чате уже идёт игра"); conn.close(); return
    c.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, uid))
    conn.commit(); conn.close()
    track_command(m.chat.id, uid, "число"); _bump_usage(uid)
    secret = random.randint(1, 100)
    number_games[m.chat.id] = {"secret":secret,"prize":amount,"creator":uid,"active":True}
    await m.answer(f"🎲 <b>ИГРА «ЧИСЛО»!</b>\n\n💰 Приз: <b>{format_balance(amount)}</b>\n\n• Загадано число от 1 до 100\n• Пиши число в чат\n• Бот ответит: холодно ❄ / тепло ♨\n• Угадавший забирает приз", parse_mode=ParseMode.HTML)

@dp.message(F.text.regexp(r"^\d+$"))
async def guess_num(m: Message):
    if m.chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP): return
    g = number_games.get(m.chat.id)
    if not g or not g.get("active") or not m.from_user: return
    try: guess = int(m.text.strip())
    except: return
    if not 1 <= guess <= 100: return
    if m.from_user.id == g["creator"]: return
    if guess == g["secret"]:
        amount = g["prize"]; g["active"] = False
        number_games.pop(m.chat.id, None)
        conn = get_db_connection(); c = conn.cursor()
        c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, m.from_user.id))
        conn.commit(); conn.close()
        try: await m.reply(f"🎉 Ты угадал <b>{g['secret']}</b>!\n💰 Приз: {format_balance(amount)}", parse_mode=ParseMode.HTML)
        except: pass
    else:
        diff = abs(guess - g["secret"])
        await m.reply("♨ тепло" if diff <= 20 else "❄ холодно")

# ========= ТОП =========
@dp.message(F.text.lower() == "топ")
async def top_cmd(m: Message):
    if await check_stopped(m) or await check_banned(m): return
    _bump_usage(m.from_user.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏆 Топ по балансу", callback_data="top_bal_1")],
        [InlineKeyboardButton(text="👥 Топ рефералов", callback_data="top_ref_1")]])
    await m.answer("🏆 ВЫБЕРИ ТИП ТОПА:", reply_markup=kb)

@dp.callback_query(F.data.startswith("top_bal_"))
async def top_bal_cb(cb: CallbackQuery):
    page = int(cb.data.split("_")[2]); pp = 5
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT user_id,nick,balance FROM users WHERE top_visible = 1 ORDER BY balance DESC")
    us = c.fetchall(); conn.close()
    tp = max(1, (len(us) + pp - 1) // pp)
    if page > tp: page = tp
    ul = us[(page-1)*pp:page*pp]
    if not ul: await cb.answer("Нет игроков", show_alert=True); return
    txt = f"🏆 ТОП ПО БАЛАНСУ ({page}/{tp})\n\n"
    for i, (uid, nick, b) in enumerate(ul, start=(page-1)*pp+1):
        txt += f"{i}. {get_nick_link(uid, nick)} - {format_balance(b)}\n"
    kb = InlineKeyboardMarkup(inline_keyboard=[]); nav = []
    if page > 1: nav.append(InlineKeyboardButton(text="◀️ Назад", callback_data=f"top_bal_{page-1}"))
    if page < tp: nav.append(InlineKeyboardButton(text="Вперёд ▶️", callback_data=f"top_bal_{page+1}"))
    if nav: kb.inline_keyboard.append(nav)
    try: await cb.message.edit_text(txt, parse_mode=ParseMode.HTML, reply_markup=kb)
    except: pass
    await cb.answer()

@dp.callback_query(F.data.startswith("top_ref_"))
async def top_ref_cb(cb: CallbackQuery):
    page = int(cb.data.split("_")[2]); pp = 5
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT user_id,nick,referals_count FROM users WHERE top_visible = 1 ORDER BY referals_count DESC")
    us = c.fetchall(); conn.close()
    tp = max(1, (len(us) + pp - 1) // pp)
    if page > tp: page = tp
    txt = f"👥 ТОП РЕФЕРАЛОВ ({page}/{tp})\n\n"
    for i, (uid, nick, cnt) in enumerate(us[(page-1)*pp:page*pp], start=(page-1)*pp+1):
        txt += f"{i}. {get_nick_link(uid, nick)} - {cnt} приглашённых\n"
    kb = InlineKeyboardMarkup(inline_keyboard=[]); nav = []
    if page > 1: nav.append(InlineKeyboardButton(text="◀️ Назад", callback_data=f"top_ref_{page-1}"))
    if page < tp: nav.append(InlineKeyboardButton(text="Вперёд ▶️", callback_data=f"top_ref_{page+1}"))
    if nav: kb.inline_keyboard.append(nav)
    try: await cb.message.edit_text(txt, parse_mode=ParseMode.HTML, reply_markup=kb)
    except: pass
    await cb.answer()

@dp.message(F.text.lower() == "стата")
async def stats_cmd(m: Message):
    if await check_stopped(m) or await check_banned(m): return
    uid = m.from_user.id; _bump_usage(uid)
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT roul_won,roul_lost,dice_won,dice_lost,slot_won,slot_lost FROM chat_stats WHERE chat_id = ? AND user_id = ?", (m.chat.id, uid))
    r = c.fetchone(); conn.close()
    if not r: r = (0,0,0,0,0,0)
    txt = (f"ПРОИГРЫШИ ❌\n• Рулетка: {format_balance(r[1])}\n• Кости: {format_balance(r[3])}\n• Слоты: {format_balance(r[5])}\n\n"
           f"ПОБЕДЫ 🏆\n• Рулетка: {format_balance(r[0])}\n• Кости: {format_balance(r[2])}\n• Слоты: {format_balance(r[4])}")
    try: await m.answer_photo(photo=STATS_IMAGE_URL, caption=txt, parse_mode=ParseMode.HTML)
    except: await m.answer(txt, parse_mode=ParseMode.HTML)

# ========= НАСТРОЙКИ =========
@dp.message(F.text.lower().in_(["⚙️ настройки", "настройки"]))
async def settings_cmd(m: Message):
    if await check_stopped(m) or await check_banned(m): return
    uid = m.from_user.id; _bump_usage(uid)
    if not await user_exists(uid): await m.answer("Сначала /start"); return
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT top_visible FROM users WHERE user_id = ?", (uid,))
    tv = c.fetchone()[0]
    c.execute("SELECT confirm_transfer FROM settings WHERE user_id = ?", (uid,))
    ct = c.fetchone()
    ct_val = ct[0] if ct else 1
    conn.close()
    await m.answer("⚙️ НАСТРОЙКИ", reply_markup=settings_kb(tv, ct_val))

def settings_kb(tv, ct_val):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📊 В топе: {'✅ Да' if tv else '❌ Нет'}", callback_data="toggle_top")],
        [InlineKeyboardButton(text=f"💸 Подтверждение перевода: {'✅ Вкл' if ct_val else '❌ Выкл'}", callback_data="toggle_confirm_transfer")],
        [InlineKeyboardButton(text="✏️ Сменить имя", callback_data="change_name")]])

@dp.callback_query(F.data == "toggle_top")
async def toggle_top_cb(cb: CallbackQuery):
    uid = cb.from_user.id
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT top_visible FROM users WHERE user_id = ?", (uid,))
    tv = c.fetchone()[0]
    nv = 0 if tv else 1
    c.execute("UPDATE users SET top_visible = ? WHERE user_id = ?", (nv, uid))
    c.execute("SELECT confirm_transfer FROM settings WHERE user_id = ?", (uid,))
    ct = c.fetchone(); ct_val = ct[0] if ct else 1
    conn.commit(); conn.close()
    try: await cb.message.edit_reply_markup(reply_markup=settings_kb(nv, ct_val))
    except: pass
    await cb.answer("✅ Изменено!")

@dp.callback_query(F.data == "toggle_confirm_transfer")
async def toggle_confirm_transfer_cb(cb: CallbackQuery):
    uid = cb.from_user.id
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT confirm_transfer FROM settings WHERE user_id = ?", (uid,))
    r = c.fetchone()
    if not r:
        c.execute("INSERT INTO settings (user_id, confirm_transfer) VALUES (?,1)", (uid,))
        ct_val = 1
    else:
        ct_val = r[0]
    nv = 0 if ct_val else 1
    c.execute("INSERT OR REPLACE INTO settings (user_id, confirm_transfer) VALUES (?,?)", (uid, nv))
    c.execute("SELECT top_visible FROM users WHERE user_id = ?", (uid,))
    tv = c.fetchone()[0]
    conn.commit(); conn.close()
    try: await cb.message.edit_reply_markup(reply_markup=settings_kb(tv, nv))
    except: pass
    if nv:
        await cb.answer("⚠️ Подтверждение перевода ВКЛЮЧЕНО", show_alert=True)
    else:
        await cb.answer("⚠️ Подтверждение перевода ВЫКЛЮЧЕНО", show_alert=True)

@dp.callback_query(F.data == "change_name")
async def change_name_cb(cb: CallbackQuery, state: FSMContext):
    await cb.message.answer("✏️ Введи новый ник:")
    await state.set_state(RegStates.waiting_new_nick)
    await cb.answer()

@dp.message(RegStates.waiting_new_nick)
async def process_new_nick(m: Message, state: FSMContext):
    uid = m.from_user.id; nick = m.text.strip()
    if not nick: await m.answer("Ник не может быть пустым."); return
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE nick = ? AND user_id != ?", (nick, uid))
    if c.fetchone():
        await m.answer("❌ Этот ник уже занят! Придумай другой."); conn.close(); return
    c.execute("UPDATE users SET nick = ? WHERE user_id = ?", (nick, uid))
    conn.commit(); conn.close()
    avatar_cache.pop(uid, None)
    await m.answer(f"✅ Ник изменён на {nick}")
    await state.clear()

# ========= ПОМОЩЬ =========
@dp.message(F.text.lower() == "помощь")
async def help_cmd(m: Message):
    await m.answer("""🎰 КОМАНДЫ ИГРОКОВ 🎰

💰 БОНУСЫ:
• бонус — каждые 25 мин
• 🔗 рефералка — 15ккк за друга

👤 ПРОФИЛЬ:
• я — профиль
• стата — статистика
• шкаф — вещи
• продажа — продать за 35%

💸 ПЕРЕВОДЫ:
• перевести @ник сумма (или "все")

🎰 СТАВКИ (в чатах):
• рул чёрное 1ккк
• ряд1 1ккк (x3)
• слот 1ккк
• кости 1ккк (ответом)

🗺️ КАРТА:
• карта — путешествие

💼 РАБОТА:
• кликер / учитель / ребусы / такси

🏦 БАНК:
• вклад под 10% на 24ч

🏢 БИЗНЕС:
• временно недоступен

⚽ ФУТБОЛ:
• Football Чел — ставки в Mini App""", reply_markup=get_full_keyboard() if is_private(m) else None)

@dp.message(F.text.lower() == "🏢 бизнес")
async def biz_cmd(m: Message):
    if await check_stopped(m) or await check_banned(m): return
    _bump_usage(m.from_user.id)
    await m.answer("🏢 <b>БИЗНЕС ВРЕМЕННО НЕДОСТУПЕН</b>\n\nРаздел находится в разработке. Следи за новостями!", parse_mode=ParseMode.HTML) # ========= ДРОП =========
@dp.message(Command("дроп"))
async def drop_cmd(m: Message):
    global drop_data
    if not is_admin(m.from_user.id): return
    args = m.text.split()
    if len(args) < 2: await m.answer("❌ /дроп 50000000000"); return
    try: amount = parse_amount(args[1])
    except: await m.answer("❌ Неверная сумма"); return
    rc = random.choice(list(CITIES.keys()))
    drop_data = {"active":True,"city":rc,"amount":amount,"expires_at":datetime.now()+timedelta(hours=2),"claimed":False,"creator_id":m.from_user.id}
    text = f"🎁 ДРОП СОЗДАН\n\n💰 {format_balance(amount)}\n⏰ Активен 2 часа"
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    us = c.fetchall(); conn.close()
    for (uid,) in us:
        try: await bot.send_message(uid, text)
        except: pass
    await m.answer(text + f"\n📍 Город: {rc}")

@dp.message(F.text.lower() == "дропчик")
async def claim_drop(m: Message):
    global drop_data
    if await check_stopped(m) or await check_banned(m): return
    uid = m.from_user.id
    if not drop_data["active"] or drop_data["claimed"]:
        await m.answer("❌ Нет активного дропа"); return
    if datetime.now() > drop_data["expires_at"]:
        drop_data["active"] = False; await m.answer("❌ Время дропа истекло"); return
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT city FROM users WHERE user_id = ?", (uid,))
    u = c.fetchone(); conn.close()
    if not u: await m.answer("Сначала /start"); return
    if u[0] == drop_data["city"]: await m.answer("❌ Дроп упал не в твоём городе!"); return
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🎁 Активировать дропчик", callback_data="open_drop")]])
    await m.answer("🎁 ТЫ НАШЁЛ ДРОП! 🎁", reply_markup=kb)

@dp.callback_query(F.data == "open_drop")
async def open_drop_cb(cb: CallbackQuery):
    global drop_data
    uid = cb.from_user.id
    if not drop_data["active"] or drop_data["claimed"]: await cb.answer("❌ Дроп неактивен", show_alert=True); return
    if datetime.now() > drop_data["expires_at"]:
        drop_data["active"] = False; await cb.answer("❌ Время истекло", show_alert=True); return
    amount = drop_data["amount"]; cid = drop_data["creator_id"]
    drop_data["active"] = False; drop_data["claimed"] = True
    conn = get_db_connection(); c = conn.cursor()
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, uid))
    c.execute("SELECT balance,nick FROM users WHERE user_id = ?", (uid,))
    nb, nick = c.fetchone(); conn.commit(); conn.close()
    try: await cb.message.delete()
    except: pass
    await cb.message.answer(f"🎉 ПОЗДРАВЛЯЮ! 🎉\n\nТы получил {format_balance(amount)}!\n💳 Баланс: {format_balance(nb)}", parse_mode=ParseMode.HTML)
    if cid:
        try: await bot.send_message(cid, f"🎁 Дроп забрал {get_nick_link(uid, nick)}!\n💰 {format_balance(amount)}", parse_mode=ParseMode.HTML)
        except: pass

# ========= АДМИН: СТОП/СТАРТ/ВЫДАЧА/ЗАБРАТЬ/ОБНУЛ =========
@dp.message(Command("стоп"))
async def stop_bot_cmd(m: Message, cmd: CommandObject):
    if not is_admin(m.from_user.id): return
    if (cmd.args or "").strip().lower() != "бот": await m.answer("❌ /стоп бот"); return
    BOT_STOPPED["value"] = True
    await m.answer("🛑 Бот остановлен.")

@dp.message(Command("старт"))
async def start_bot_cmd(m: Message, cmd: CommandObject):
    if not is_admin(m.from_user.id): return
    if (cmd.args or "").strip().lower() != "бот": await m.answer("❌ /старт бот"); return
    BOT_STOPPED["value"] = False
    await m.answer("✅ Бот запущен.")

@dp.message(Command("выдать_себе"))
async def give_self_cmd(m: Message):
    if not is_admin(m.from_user.id): return
    args = m.text.split()
    if len(args) < 2: await m.answer("❌ /выдать_себе 10ккк"); return
    try: amount = parse_amount(args[1])
    except: await m.answer("❌ Неверная сумма"); return
    uid = m.from_user.id
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id = ?", (uid,))
    u = c.fetchone()
    if not u:
        c.execute("INSERT INTO users (user_id,nick,balance) VALUES (?,?,?)", (uid, "владелец", amount)); nb = amount
    else:
        nb = u[0] + amount
        c.execute("UPDATE users SET balance = ? WHERE user_id = ?", (nb, uid))
    conn.commit(); conn.close()
    await m.answer(f"✅ +{format_balance(amount)}\n💳 {format_balance(nb)}")

@dp.message(Command("выдать"))
async def give_cmd(m: Message):
    if not is_admin(m.from_user.id): return
    if not m.reply_to_message: await m.answer("❌ В ответ"); return
    tu = m.reply_to_message.from_user
    args = m.text.split()
    if len(args) < 2: await m.answer("❌ /выдать 10ккк"); return
    try: amount = parse_amount(args[1])
    except: await m.answer("❌ Неверная сумма"); return
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT nick FROM users WHERE user_id = ?", (tu.id,))
    u = c.fetchone()
    if not u: await m.answer("❌ Не зарегистрирован"); conn.close(); return
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, tu.id))
    conn.commit(); conn.close()
    await m.answer(f"✅ {format_balance(amount)} игроку {u[0]}")

@dp.message(Command("забрать"))
async def take_cmd(m: Message):
    if not is_admin(m.from_user.id): return
    args = m.text.split()
    target_id = None; amount = None
    if m.reply_to_message:
        target_id = m.reply_to_message.from_user.id
        if len(args) >= 2:
            try: amount = parse_amount(args[1])
            except: await m.answer("❌ Неверная сумма"); return
    else:
        if len(args) < 3: await m.answer("❌ Пример: /забрать @ник 10ккк\nИли: /забрать 10ккк — в ответ"); return
        found = await find_user(args[1].replace("@","").strip())
        if not found: await m.answer("❌ Игрок не найден"); return
        target_id = found[0]
        try: amount = parse_amount(args[2])
        except: await m.answer("❌ Неверная сумма"); return
    if not target_id or not amount:
        await m.answer("❌ Не хватает данных"); return
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT nick,balance FROM users WHERE user_id = ?", (target_id,))
    u = c.fetchone()
    if not u: await m.answer("❌ Игрок не найден"); conn.close(); return
    nb = max(0, u[1] - amount)
    c.execute("UPDATE users SET balance = ? WHERE user_id = ?", (nb, target_id))
    conn.commit(); conn.close()
    await m.answer(f"✅ Забрано {format_balance(amount)} у {u[0]}\n💳 У него: {format_balance(nb)}", parse_mode=ParseMode.HTML)
    try: await bot.send_message(target_id, f"⚠️ У тебя забрали {format_balance(amount)}\n💳 Баланс: {format_balance(nb)}")
    except: pass

@dp.message(Command("всем"))
async def all_cmd(m: Message):
    if not is_admin(m.from_user.id): return
    args = m.text.split()
    if len(args) < 2: await m.answer("❌ /всем 1ккк"); return
    try: amount = parse_amount(args[1])
    except: await m.answer("❌ Неверная сумма"); return
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    us = c.fetchall()
    for (uid,) in us: c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, uid))
    conn.commit(); conn.close()
    text = f"🎁 МАССОВАЯ РАЗДАЧА!\n\nВсем по {format_balance(amount)}! 🎉"
    for (uid,) in us:
        try: await bot.send_message(uid, text)
        except: pass
    await m.answer(f"✅ {len(us)} игрокам по {format_balance(amount)}")

@dp.message(Command("обнул"))
async def zero_user_cmd(m: Message):
    if not is_admin(m.from_user.id): return
    args = m.text.split()
    if len(args) < 2: await m.answer("❌ /обнул @ник"); return
    found = await find_user(args[1].replace("@","").strip())
    if not found: await m.answer("❌ Игрок не найден"); return
    tid, tnick = found
    conn = get_db_connection(); c = conn.cursor()
    c.execute("UPDATE users SET balance = 0 WHERE user_id = ?", (tid,))
    conn.commit(); conn.close()
    await m.answer(f"✅ Баланс {tnick} обнулён до 0", parse_mode=ParseMode.HTML)

@dp.message(Command("фулл_обнул"))
async def zero_all_cmd(m: Message):
    if not is_admin(m.from_user.id): return
    conn = get_db_connection(); c = conn.cursor()
    c.execute("UPDATE users SET balance = 0 WHERE user_id NOT IN ({})".format(",".join("?"*len(OWNERS))), tuple(OWNERS))
    conn.commit(); conn.close()
    await m.answer("✅ Балансы всех игроков (кроме владельцев) обнулены!")

@dp.message(Command("фулл_обнул_юзера"))
async def zero_user_full_cmd(m: Message):
    if not is_admin(m.from_user.id): return
    args = m.text.split()
    if len(args) < 2: await m.answer("❌ /фулл_обнул_юзера @ник"); return
    found = await find_user(args[1].replace("@","").strip())
    if not found: await m.answer("❌ Игрок не найден"); return
    tid, tnick = found
    conn = get_db_connection(); c = conn.cursor()
    c.execute("UPDATE users SET balance = 0 WHERE user_id = ?", (tid,))
    c.execute("DELETE FROM bank WHERE user_id = ?", (tid,))
    c.execute("DELETE FROM wardrobe WHERE user_id = ?", (tid,))
    c.execute("DELETE FROM equipped_outfit WHERE user_id = ?", (tid,))
    c.execute("DELETE FROM equipped_house WHERE user_id = ?", (tid,))
    c.execute("UPDATE users SET wardrobe_slots = 5 WHERE user_id = ?", (tid,))
    conn.commit(); conn.close()
    avatar_cache.pop(tid, None)
    await m.answer(f"✅ {tnick} полностью обнулён (баланс, шкаф, дом, банк)", parse_mode=ParseMode.HTML)

# ========= АДМИН: БАН =========
@dp.message(Command("бан"))
async def ban_cmd(m: Message):
    if not is_admin(m.from_user.id): return
    args = m.text.split()
    if len(args) < 2: await m.answer("❌ /бан @username"); return
    t = args[1].replace("@","").strip()
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT user_id,nick FROM users WHERE LOWER(nick) = LOWER(?) OR LOWER(username) = LOWER(?)", (t, t))
    tgt = c.fetchone()
    if not tgt: await m.answer("❌ Не найден"); conn.close(); return
    tid, nick = tgt
    if tid in OWNERS: await m.answer("❌ Владельца нельзя"); conn.close(); return
    c.execute("UPDATE users SET is_banned = 1 WHERE user_id = ?", (tid,))
    conn.commit(); conn.close()
    banned_users.add(tid)
    await m.answer(f"✅ {nick} забанен")

@dp.message(Command("разбан"))
async def unban_cmd(m: Message):
    if not is_admin(m.from_user.id): return
    args = m.text.split()
    if len(args) < 2: await m.answer("❌ /разбан @username"); return
    t = args[1].replace("@","").strip()
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT user_id,nick FROM users WHERE LOWER(nick) = LOWER(?) OR LOWER(username) = LOWER(?)", (t, t))
    tgt = c.fetchone()
    if not tgt: await m.answer("❌ Не найден"); conn.close(); return
    tid, nick = tgt
    c.execute("UPDATE users SET is_banned = 0 WHERE user_id = ?", (tid,))
    conn.commit(); conn.close()
    banned_users.discard(tid)
    await m.answer(f"✅ {nick} разбанен")

# ========= АДМИН: КОНКУРСЫ =========
# /конкурс [сумма] [номер сета] [текст] — ответом на фото
@dp.message(Command("конкурс"))
async def contest_set_cmd(m: Message):
    if not is_admin(m.from_user.id): return
    if not m.reply_to_message or not m.reply_to_message.photo:
        await m.answer("❌ Ответь на фото командой:\n<code>/конкурс [сумма] [номер сета] [текст]</code>", parse_mode=ParseMode.HTML); return
    args = m.text.split(maxsplit=3)
    if len(args) < 4: await m.answer("❌ Пример: /конкурс 5000000000 3 'Угадай счет'"); return
    try:
        prize = parse_amount(args[1]); set_id = int(args[2]); text = args[3]
    except: await m.answer("❌ Неверные параметры"); return
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT name,file_id,price FROM market_items WHERE id = ?", (set_id,))
    row = c.fetchone(); conn.close()
    if not row: await m.answer(f"❌ Сета #{set_id} нет в маркете"); return
    set_name, set_fid, set_price = row
    global next_contest_id
    cid = next_contest_id; next_contest_id += 1
    contest_data[cid] = {
        "prize": prize, "text": text, "type": "set",
        "set_id": set_id, "set_name": set_name, "set_fid": set_fid,
        "creator": m.from_user.id, "answers": [],
        "announce_msg_id": None, "chat_id": m.chat.id
    }
    await m.answer(
        f"🎉 <b>КОНКУРС #{cid} СОЗДАН!</b>\n\n"
        f"💰 Приз: {format_balance(prize)}\n"
        f"👕 Сет: {set_name} (ID {set_id})\n"
        f"📝 Задание: {text}\n\n"
        f"Конкурс опубликован в чате!",
        parse_mode=ParseMode.HTML
    )
    try:
        sent = await bot.send_photo(
            m.chat.id, set_fid,
            caption=(
                f"🎉 <b>КОНКУРС #{cid}</b>\n\n"
                f"📝 {text}\n\n"
                f"💰 Приз: {format_balance(prize)}\n"
                f"👕 Сет: <b>{set_name}</b>\n\n"
                f"✍️ Отвечай командой: <code>/ответ {cid} твой_ответ</code>"
            ),
            parse_mode=ParseMode.HTML
        )
        contest_data[cid]["announce_msg_id"] = sent.message_id
    except Exception as e:
        await m.answer(f"⚠️ Ошибка публикации: {e}")

@dp.message(Command("конкурс_дом"))
async def contest_house_cmd(m: Message):
    if not is_admin(m.from_user.id): return
    if not m.reply_to_message or not m.reply_to_message.photo:
        await m.answer("❌ Ответь на фото командой:\n<code>/конкурс_дом [сумма] [номер дома] [текст]</code>", parse_mode=ParseMode.HTML); return
    args = m.text.split(maxsplit=3)
    if len(args) < 4: await m.answer("❌ Пример: /конкурс_дом 5000000000 2 'Угадай счет'"); return
    try:
        prize = parse_amount(args[1]); hid = int(args[2]); text = args[3]
    except: await m.answer("❌ Неверные параметры"); return
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT name,file_id,price FROM houses WHERE id = ?", (hid,))
    row = c.fetchone(); conn.close()
    if not row: await m.answer(f"❌ Дома #{hid} нет в магазине"); return
    hname, hfid, hprice = row
    global next_contest_id
    cid = next_contest_id; next_contest_id += 1
    contest_data[cid] = {
        "prize": prize, "text": text, "type": "house",
        "set_id": hid, "set_name": hname or f"Дом #{hid}", "set_fid": hfid,
        "creator": m.from_user.id, "answers": [], "announce_msg_id": None, "chat_id": m.chat.id
    }
    await m.answer(
        f"🎉 <b>КОНКУРС #{cid} (ДОМ) СОЗДАН!</b>\n\n"
        f"💰 Приз: {format_balance(prize)}\n🏠 Дом: {hname}\n📝 {text}",
        parse_mode=ParseMode.HTML
    )
    try:
        sent = await bot.send_photo(
            m.chat.id, hfid,
            caption=(
                f"🎉 <b>КОНКУРС #{cid}</b>\n\n"
                f"📝 {text}\n\n💰 Приз: {format_balance(prize)}\n"
                f"🏠 Дом: <b>{hname}</b>\n\n"
                f"✍️ Отвечай: <code>/ответ {cid} твой_ответ</code>"
            ),
            parse_mode=ParseMode.HTML
        )
        contest_data[cid]["announce_msg_id"] = sent.message_id
    except Exception as e:
        await m.answer(f"⚠️ Ошибка публикации: {e}")

@dp.message(Command("конкурс_сет"))
async def contest_custom_set_cmd(m: Message, state: FSMContext):
    if not is_admin(m.from_user.id): return
    if not m.reply_to_message or not m.reply_to_message.photo:
        await m.answer("❌ Ответь на фото (сет вне маркета) командой:\n<code>/конкурс_сет [сумма] [кол-во] [текст]</code>", parse_mode=ParseMode.HTML); return
    args = m.text.split(maxsplit=3)
    if len(args) < 4: await m.answer("❌ Пример: /конкурс_сет 5000000000 3 'Угадай счет'"); return
    try:
        prize = parse_amount(args[1]); cnt = int(args[2]); text = args[3]
    except: await m.answer("❌ Неверные параметры"); return
    fid = m.reply_to_message.photo[-1].file_id
    global next_contest_id
    cid = next_contest_id; next_contest_id += 1
    contest_data[cid] = {
        "prize": prize, "text": text, "type": "custom_set", "count": cnt,
        "set_id": 0, "set_name": "Кастомный сет", "set_fid": fid,
        "creator": m.from_user.id, "answers": [], "announce_msg_id": None, "chat_id": m.chat.id
    }
    await m.answer(
        f"🎉 <b>КОНКУРС #{cid} (КАСТОМ) СОЗДАН!</b>\n\n"
        f"💰 Приз: {format_balance(prize)}\n👥 Кол-во победителей: {cnt}\n📝 {text}",
        parse_mode=ParseMode.HTML
    )
    try:
        sent = await bot.send_photo(
            m.chat.id, fid,
            caption=(
                f"🎉 <b>КОНКУРС #{cid}</b>\n\n📝 {text}\n\n"
                f"💰 Приз: {format_balance(prize)}\n"
                f"👥 Победителей: {cnt}\n\n"
                f"✍️ Отвечай: <code>/ответ {cid} твой_ответ</code>"
            ),
            parse_mode=ParseMode.HTML
        )
        contest_data[cid]["announce_msg_id"] = sent.message_id
    except Exception as e:
        await m.answer(f"⚠️ Ошибка публикации: {e}")

@dp.message(Command("конкурс_дом_кастом"))
async def contest_custom_house_cmd(m: Message):
    if not is_admin(m.from_user.id): return
    if not m.reply_to_message or not m.reply_to_message.photo:
        await m.answer("❌ Ответь на фото (дом вне магазина) командой:\n<code>/конкурс_дом_кастом [сумма] [кол-во] [текст]</code>", parse_mode=ParseMode.HTML); return
    args = m.text.split(maxsplit=3)
    if len(args) < 4: await m.answer("❌ Пример: /конкурс_дом_кастом 5000000000 2 'Угадай счет'"); return
    try:
        prize = parse_amount(args[1]); cnt = int(args[2]); text = args[3]
    except: await m.answer("❌ Неверные параметры"); return
    fid = m.reply_to_message.photo[-1].file_id
    global next_contest_id
    cid = next_contest_id; next_contest_id += 1
    contest_data[cid] = {
        "prize": prize, "text": text, "type": "custom_house", "count": cnt,
        "set_id": 0, "set_name": "Кастомный дом", "set_fid": fid,
        "creator": m.from_user.id, "answers": [], "announce_msg_id": None, "chat_id": m.chat.id
    }
    await m.answer(
        f"🎉 <b>КОНКУРС #{cid} (ДОМ-КАСТОМ) СОЗДАН!</b>\n\n"
        f"💰 Приз: {format_balance(prize)}\n👥 Победителей: {cnt}\n📝 {text}",
        parse_mode=ParseMode.HTML
    )
    try:
        sent = await bot.send_photo(
            m.chat.id, fid,
            caption=(
                f"🎉 <b>КОНКУРС #{cid}</b>\n\n📝 {text}\n\n"
                f"💰 Приз: {format_balance(prize)}\n👥 Победителей: {cnt}\n\n"
                f"✍️ Отвечай: <code>/ответ {cid} твой_ответ</code>"
            ),
            parse_mode=ParseMode.HTML
        )
        contest_data[cid]["announce_msg_id"] = sent.message_id
    except Exception as e:
        await m.answer(f"⚠️ Ошибка публикации: {e}")

@dp.message(Command("ответ"))
async def answer_contest(m: Message, cmd: CommandObject):
    if not cmd.args: await m.answer("❌ /ответ [номер конкурса] [ответ]"); return
    parts = cmd.args.split(maxsplit=1)
    if len(parts) < 2: await m.answer("❌ /ответ [номер] [твой ответ]"); return
    try: cid = int(parts[0])
    except: await m.answer("❌ Номер конкурса — число"); return
    ans = parts[1].strip()
    if cid not in contest_data: await m.answer("❌ Конкурс не найден"); return
    cd = contest_data[cid]
    cd["answers"].append({"user_id": m.from_user.id, "nick": m.from_user.full_name, "text": ans})
    await m.answer(f"✅ Ответ принят на конкурс #{cid}!")
    try:
        await bot.send_message(cd["creator"], f"📩 Ответ на конкурс #{cid}\n👤 {get_nick_link(m.from_user.id, m.from_user.full_name)}\n💬 {ans}", parse_mode=ParseMode.HTML)
    except: pass

# ========= АДМИН: РУЛЕТКА-ФОТО =========
@dp.message(Command("рул_фото"))
async def rul_photo_cmd(m: Message):
    if not is_admin(m.from_user.id): return
    args = m.text.split()
    if len(args) < 2: await m.answer("❌ /рул_фото [0-36] — ответом на фото"); return
    if not m.reply_to_message or not m.reply_to_message.photo:
        await m.answer("❌ Ответь на фото командой /рул_фото [цифра]"); return
    try: num = int(args[1])
    except: await m.answer("❌ Цифра 0-36"); return
    if num < 0 or num > 36: await m.answer("❌ Цифра 0-36"); return
    fid = m.reply_to_message.photo[-1].file_id
    conn = get_db_connection(); c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO roulette_images (number, file_id) VALUES (?, ?)", (num, fid))
    conn.commit(); conn.close()
    await m.answer(f"✅ Фото для числа {num} сохранено")

@dp.message(Command("удалить_рул_фото"))
async def del_rul_photo_cmd(m: Message):
    if not is_admin(m.from_user.id): return
    args = m.text.split()
    if len(args) < 2: await m.answer("❌ /удалить_рул_фото [0-36]"); return
    try: num = int(args[1])
    except: return
    conn = get_db_connection(); c = conn.cursor()
    c.execute("DELETE FROM roulette_images WHERE number = ?", (num,))
    conn.commit(); conn.close()
    await m.answer(f"✅ Фото числа {num} удалено")

@dp.message(Command("рулетка"))
async def list_rul_photos(m: Message):
    if not is_admin(m.from_user.id): return
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT number FROM roulette_images ORDER BY number")
    nums = [r[0] for r in c.fetchall()]; conn.close()
    if not nums: await m.answer("📸 Нет сохранённых фото"); return
    await m.answer(f"📸 Сохранённые фото: {', '.join(map(str, nums))}")

# ========= АДМИН: ДОНАТ =========
@dp.message(Command("донат"))
async def donate_add_cmd(m: Message, state: FSMContext):
    if not is_admin(m.from_user.id): return
    if not m.reply_to_message or not m.reply_to_message.photo:
        await m.answer("❌ Ответь на фото командой:\n<code>/донат [номер] [название]</code>", parse_mode=ParseMode.HTML); return
    args = m.text.split(maxsplit=2)
    if len(args) < 3: await m.answer("❌ Пример: /донат 1 'Золотой сет'"); return
    try: did = int(args[1]); name = args[2].strip("'\"")
    except: await m.answer("❌ Неверные параметры"); return
    fid = m.reply_to_message.photo[-1].file_id
    conn = get_db_connection(); c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO donate_items (id,name,file_id,created_by,created_at) VALUES (?,?,?,?,?)",
        (did, name, fid, m.from_user.id, datetime.now().isoformat()))
    conn.commit(); conn.close()
    await m.answer(f"✅ ДОНАТ #{did} '{name}' добавлен!")

@dp.message(Command("удалить_донат"))
async def donate_del_cmd(m: Message):
    if not is_admin(m.from_user.id): return
    args = m.text.split()
    if len(args) < 2: await m.answer("❌ /удалить_донат [номер]"); return
    try: did = int(args[1])
    except: return
    conn = get_db_connection(); c = conn.cursor()
    c.execute("DELETE FROM donate_items WHERE id = ?", (did,))
    conn.commit(); conn.close()
    await m.answer(f"✅ Донат #{did} удалён")

# ========= АДМИН: ОЧИСТКА =========
@dp.message(Command("очистить_все"))
async def clear_all_cmd(m: Message):
    if not is_admin(m.from_user.id): return
    if not m.reply_to_message: await m.answer("❌ В ответ на сообщение"); return
    tu = m.reply_to_message.from_user
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT nick FROM users WHERE user_id = ?", (tu.id,))
    u = c.fetchone()
    if not u: await m.answer("❌ Игрок не зарегистрирован"); conn.close(); return
    c.execute("DELETE FROM wardrobe WHERE user_id = ?", (tu.id,))
    c.execute("DELETE FROM equipped_outfit WHERE user_id = ?", (tu.id,))
    c.execute("DELETE FROM equipped_house WHERE user_id = ?", (tu.id,))
    c.execute("DELETE FROM bank WHERE user_id = ?", (tu.id,))
    c.execute("UPDATE users SET wardrobe_slots = 5 WHERE user_id = ?", (tu.id,))
    conn.commit(); conn.close()
    avatar_cache.pop(tu.id, None)
    await m.answer(f"✅ У {u[0]} очищен шкаф, дом, банк", parse_mode=ParseMode.HTML)

# ========= АДМИН: /состав =========
@dp.message(Command("состав"))
async def squad_cmd(m: Message, cmd: CommandObject):
    args = (cmd.args or "").strip()
    if not args:
        await m.answer("❌ Использование: <code>/состав Название команды</code>\nПример: <code>/состав Зенит</code>", parse_mode=ParseMode.HTML); return
    home_squad = get_squad(args)
    away_squad = DEFAULT_SQUAD
    try:
        img = draw_football_field(args, "Соперник", home_squad, away_squad)
        await m.answer_photo(photo=img, caption=f"⚽ Состав: <b>{args}</b>", parse_mode=ParseMode.HTML)
    except Exception as e:
        await m.answer(f"❌ Ошибка генерации: {e}")

# ========= АДМИН: БЭКАП =========
@dp.message(Command("бэкап"))
async def backup_cmd(m: Message):
    if not is_admin(m.from_user.id): return
    try:
        conn = get_db_connection()
        conn.execute("PRAGMA wal_checkpoint(FULL)"); conn.commit(); conn.close()
        if not os.path.exists(DB_PATH): await m.answer("❌ Файл БД не найден"); return
        with open(DB_PATH, "rb") as f: data = f.read()
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        fname = f"backup_{stamp}.db"
        await m.answer_document(document=BufferedInputFile(data, filename=fname),
            caption=f"📦 <b>БЭКАП</b>\n\n📅 {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n📊 {len(data)/1024:.1f} КБ", parse_mode=ParseMode.HTML)
    except Exception as e: await m.answer(f"❌ {e}")

@dp.message(Command("удалить"))
async def del_cmd(m: Message, cmd: CommandObject):
    uid = m.from_user.id
    if not is_admin(uid): return
    if (cmd.args or "").strip().lower() not in ("я","me","self"):
        await m.answer("❌ Использование: <code>/удалить я</code>", parse_mode=ParseMode.HTML); return
    conn = get_db_connection(); c = conn.cursor()
    c.execute("DELETE FROM equipped_outfit WHERE user_id = ?", (uid,))
    conn.commit(); conn.close()
    avatar_cache.pop(uid, None)
    await m.answer("✅ С тебя снят сет."); await send_profile(m, uid)

@dp.message(Command("удалить_дом_я"))
async def del_house_cmd(m: Message):
    uid = m.from_user.id
    if not is_admin(uid): return
    conn = get_db_connection(); c = conn.cursor()
    c.execute("DELETE FROM equipped_house WHERE user_id = ?", (uid,))
    conn.commit(); conn.close()
    avatar_cache.pop(uid, None)
    await m.answer("✅ С тебя снят дом (фон)."); await send_profile(m, uid)

# ========= АДМИН-ПОМОЩЬ =========
@dp.message(Command("адм"))
async def adm_cmd(m: Message):
    if not is_admin(m.from_user.id): return
    await m.answer("""👑 <b>АДМИН-КОМАНДЫ БОТА</b> 👑

🛑 /стоп бот
✅ /старт бот

💰 <b>ВЫДАЧА И ОБНУЛЕНИЕ</b>
• /выдать_себе [сумма]
• /выдать [сумма] — в ответ
• /забрать [сумма] — в ответ
• /забрать @ник [сумма]
• /всем [сумма]
• /обнул @ник
• /фулл_обнул
• /фулл_обнул_юзера @ник

🔨 <b>БАН</b>
• /бан @ник
• /разбан @ник

🎁 <b>ПОДАРКИ, ЧЕКИ, ПРОМОКОДЫ</b>
• /подарок [сумма]
• /чек [сумма] [кол-во]
• /промо [название] [сумма] [кол-во]

🎲 <b>ДРОПЫ И КОНКУРСЫ</b>
• /дроп [сумма]
• /конкурс [сумма] [номер сета] [текст] — ответом на фото
• /конкурс_дом [сумма] [номер дома] [текст] — ответом на фото
• /конкурс_сет [сумма] [кол-во] [текст] — ответом на фото (сет вне маркета)
• /конкурс_дом_кастом [сумма] [кол-во] [текст] — ответом на фото (дом вне магазина)

🎰 <b>РУЛЕТКА</b>
• /рул_фото [цифра] — фото 0-36 (ответом)
• /удалить_рул_фото [цифра]
• /рулетка — какие фото есть

👕 <b>МАРКЕТ СЕТОВ</b>
• /добавить_сет [номер] [цена] [название] — ответом на фото
• /удалить_маркет [номер]
• /изменить_цену [номер] [цена]

🎁 <b>ДОНАТ</b>
• /донат [номер] [название] — ответом на фото
• /удалить_донат [номер]

🏠 <b>ДОМА</b>
• /дом [номер] [цена] [название] — ответом на фото
• /изменить_цену_дома [номер] [цена]
• /удалить_дом [номер]

📊 <b>СТАТИСТИКА</b>
• /стата

🧹 <b>ОЧИСТКА</b>
• /очистить_все (в ответ)
• /удалить я — снять сет
• /удалить_дом_я — снять дом

⚽ <b>ФУТБОЛ</b>
• /состав [команда]

💾 <b>БЭКАП</b>
• /бэкап""", parse_mode=ParseMode.HTML) # ========= ФУТБОЛ =========
COMPETITIONS_FOOTBALL = {
    "PL":"🏴 Premier League","PD":"🇪🇸 La Liga","BL1":"🇩🇪 Bundesliga",
    "SA":"🇮🇹 Serie A","FL1":"🇫🇷 Ligue 1","CL":"🏆 Champions League"}

_fb_cache = {}; FB_TTL = 300

async def fb_get(path, params=None):
    key = f"{path}?{params}"; now = datetime.now()
    if key in _fb_cache:
        data, ts = _fb_cache[key]
        if (now-ts).total_seconds() < FB_TTL: return data
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(f"{FOOTBALL_BASE}{path}",
            headers={"X-Auth-Token": FOOTBALL_API_KEY},
            params=params or {})
        if r.status_code == 429: raise Exception("Лимит API (10/мин)")
        if r.status_code == 403: raise Exception("Доступ запрещён")
        if r.status_code == 404: raise Exception("Не найдено")
        r.raise_for_status(); data = r.json()
    _fb_cache[key] = (data, now); return data

async def fb_matches(comp):
    data = await fb_get(f"/competitions/{comp}/matches", {"status":"SCHEDULED,LIVE,IN_PLAY,PAUSED,FINISHED"})
    ms = data.get("matches",[]); now = datetime.utcnow()
    today = now.date(); tomorrow = today + timedelta(days=1)
    live = []; today_ms = []; tomorrow_ms = []; future_ms = []
    for m in ms:
        try: utc = datetime.fromisoformat(m["utcDate"].replace("Z","+00:00")).replace(tzinfo=None)
        except: continue
        st = m.get("status","")
        if st in ("LIVE","IN_PLAY","PAUSED"): live.append((utc, m))
        elif utc.date() == today: today_ms.append((utc, m))
        elif utc.date() == tomorrow: tomorrow_ms.append((utc, m))
        elif utc.date() > tomorrow: future_ms.append((utc, m))
    live.sort(key=lambda x: x[0]); today_ms.sort(key=lambda x: x[0])
    tomorrow_ms.sort(key=lambda x: x[0]); future_ms.sort(key=lambda x: x[0])
    if live or today_ms:
        return [m for _,m in live] + [m for _,m in today_ms]
    elif tomorrow_ms:
        return [m for _,m in tomorrow_ms]
    else:
        return [m for _,m in future_ms][:40]

async def fb_fixture(fid):
    return await fb_get(f"/matches/{fid}")

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
    d = max(0.15, 1-h-a); tot = h+a+d; h/=tot; a/=tot; d/=tot; mg = 1.10
    return {"home":round(1/h*mg,2),"draw":round(1/d*mg,2),"away":round(1/a*mg,2),
        "favorite":"home" if h > a else "away","home_chance":round(h*100,1),
        "draw_chance":round(d*100,1),"away_chance":round(a*100,1)}

def verify_init(init):
    if not init: raise HTTPException(401, "no initData")
    try:
        return safe_parse_webapp_init_data(token=BOT_TOKEN, init_data=init).user.id
    except Exception as e:
        raise HTTPException(401, f"invalid: {e}")

@app.get("/api/competitions")
async def api_comps(): return COMPETITIONS_FOOTBALL

@app.get("/api/matches")
async def api_matches(competition: str = "PL"):
    try:
        ms = await fb_matches(competition); st = await fb_standings(competition)
    except Exception as e:
        return JSONResponse({"error":str(e)}, status_code=500)
    res = []
    for m in ms:
        try:
            h = m["homeTeam"]; a = m["awayTeam"]
            odds = calc_odds(h["id"], a["id"], st)
            res.append({"id":m["id"],"competition":m.get("competition",{}).get("name",""),
                "utcDate":m["utcDate"],"status":m["status"],"minute":m.get("minute"),
                "home":{"id":h["id"],"name":h.get("shortName") or h.get("name"),"crest":h.get("crest","")},
                "away":{"id":a["id"],"name":a.get("shortName") or a.get("name"),"crest":a.get("crest","")},
                "score":{"home":m.get("score",{}).get("fullTime",{}).get("home"),
                         "away":m.get("score",{}).get("fullTime",{}).get("away")},
                "odds":odds})
        except Exception as e:
            print(f"parse match: {e}"); continue
    return {"matches":res}

@app.get("/api/match/{mid}")
async def api_match(mid: int):
    try: return await fb_fixture(mid)
    except Exception as e: return JSONResponse({"error":str(e)}, status_code=500)

@app.get("/api/squad_pair/{home_name}/{away_name}")
async def api_squad_pair(home_name: str, away_name: str):
    """Возвращает составы + схемы двух команд (гарантированно разные схемы)."""
    h_scheme, h_squad, a_scheme, a_squad = get_squad_pair(home_name, away_name)
    return {"home":{"scheme":h_scheme,"players":h_squad},"away":{"scheme":a_scheme,"players":a_squad}}

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
    if pick not in ("home","draw","away"): return JSONResponse({"ok":False,"error":"Неверный выбор"}, status_code=400)
    if amount < 100_000: return JSONResponse({"ok":False,"error":"Минимум 100.000"}, status_code=400)
    try:
        m = await fb_fixture(mid)
        st = m.get("status","SCHEDULED")
        if st not in ("SCHEDULED","TIMED"): return JSONResponse({"ok":False,"error":"Ставки закрыты"}, status_code=400)
        h = m["homeTeam"].get("shortName") or m["homeTeam"].get("name")
        a = m["awayTeam"].get("shortName") or m["awayTeam"].get("name")
    except: h, a = "?","?"
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT 1 FROM football_bets WHERE user_id = ? AND fixture_id = ?", (uid, mid))
    if c.fetchone():
        conn.close(); return JSONResponse({"ok":False,"error":"Вы уже ставили на этот матч"}, status_code=400)
    c.execute("SELECT balance FROM users WHERE user_id = ?", (uid,))
    r = c.fetchone()
    if not r: conn.close(); return JSONResponse({"ok":False,"error":"Сначала /start"}, status_code=400)
    if r[0] < amount: conn.close(); return JSONResponse({"ok":False,"error":"Недостаточно средств"}, status_code=400)
    c.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, uid))
    c.execute("INSERT INTO football_bets (user_id,fixture_id,competition,home_team,away_team,pick,amount,coefficient,placed_at) VALUES (?,?,?,?,?,?,?,?,?)",
        (uid, mid, comp, h, a, pick, amount, coef, datetime.now().isoformat()))
    conn.commit()
    c.execute("SELECT balance FROM users WHERE user_id = ?", (uid,))
    nb = c.fetchone()[0]; conn.close()
    lbl = "П1" if pick == "home" else "Х" if pick == "draw" else "П2"
    return {"ok":True,"message":f"✅ Ставка {amount:,}₽ на {lbl}".replace(",","."),"balance":nb}

@app.get("/api/my_bets")
async def api_bets(initData: str):
    uid = verify_init(initData)
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT fixture_id,home_team,away_team,pick,amount,coefficient,status,payout FROM football_bets WHERE user_id = ? ORDER BY id DESC LIMIT 50", (uid,))
    rs = c.fetchall(); conn.close()
    return {"bets":[{"fixture_id":r[0],"home":r[1],"away":r[2],"pick":r[3],"amount":r[4],"coefficient":r[5],"status":r[6],"payout":r[7]} for r in rs]}

@app.get("/api/match_events/{mid}")
async def api_match_events(mid: int):
    """Возвращает события матча (голы, карточки, замены) из локальной БД."""
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT event_type,minute,player,team,score_home,score_away,extra FROM football_events WHERE fixture_id = ? ORDER BY minute", (mid,))
    rows = c.fetchall(); conn.close()
    return {"events":[{"type":r[0],"minute":r[1],"player":r[2],"team":r[3],
                       "score_home":r[4],"score_away":r[5],"extra":r[6]} for r in rows]}

FOOTBALL_HTML = r"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<title>⚽ Football Чел</title>
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<style>
*{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}
:root{--bg:#ffffff;--card:#f7f8fa;--card2:#eef1f5;--border:#e1e5eb;--text:#0a0e14;--text2:#6b7280;--accent:#00b87a;--accent2:#0095d4;--gold:#f59e0b;--red:#ef4444}
body{background:var(--bg);color:var(--text);min-height:100vh;padding-bottom:90px}
.header{position:sticky;top:0;z-index:50;background:rgba(255,255,255,.95);backdrop-filter:blur(20px);padding:14px 16px 10px;border-bottom:1px solid var(--border)}
.header-top{display:flex;align-items:center;gap:10px;margin-bottom:10px}
.logo{font-size:20px;font-weight:800;background:linear-gradient(135deg,var(--accent),var(--accent2));-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.bot-avatar{width:32px;height:32px;border-radius:50%;object-fit:cover;border:2px solid var(--accent)}
.balance-pill{margin-left:auto;background:linear-gradient(135deg,rgba(0,184,122,.12),rgba(0,149,212,.08));border:1px solid rgba(0,184,122,.3);padding:6px 12px;border-radius:100px;font-size:13px;font-weight:700;color:var(--accent)}
.tournaments{display:flex;gap:8px;overflow-x:auto;padding:0 16px 4px;scrollbar-width:none}
.tournaments::-webkit-scrollbar{display:none}
.tournaments button{flex-shrink:0;background:var(--card2);border:1px solid var(--border);color:var(--text2);padding:8px 14px;border-radius:100px;font-size:12px;font-weight:600;white-space:nowrap;cursor:pointer}
.tournaments button.active{background:linear-gradient(135deg,var(--accent),var(--accent2));color:#fff;border-color:transparent}
.tabs{display:flex;gap:6px;padding:12px 16px 4px}
.tabs button{flex:1;background:transparent;border:none;color:var(--text2);padding:10px;font-size:13px;font-weight:600;cursor:pointer;border-bottom:2px solid transparent}
.tabs button.active{color:var(--text);border-bottom-color:var(--accent)}
#content{padding:12px 16px 20px}
.match{background:var(--card);border:1px solid var(--border);border-radius:20px;padding:14px;margin-bottom:14px;cursor:pointer;transition:.15s}
.match:active{transform:scale(.98)}
.match-top{display:flex;justify-content:space-between;margin-bottom:14px;font-size:11px;color:var(--text2)}
.status-live{color:var(--red);font-weight:700}
.status-sched{color:var(--accent2);font-weight:700}
.teams{display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:10px;margin-bottom:16px}
.team{display:flex;flex-direction:column;align-items:center;gap:8px;text-align:center;min-width:0}
.team-logo-wrap{width:56px;height:56px;display:flex;align-items:center;justify-content:center;background:#fff;border-radius:50%;border:2px solid var(--border);overflow:hidden}
.team-logo-wrap img{width:40px;height:40px;object-fit:contain}
.team-name{font-size:12px;font-weight:700;line-height:1.15;color:var(--text)}
.score{font-size:26px;font-weight:800;min-width:60px;text-align:center}
.score.vs{font-size:18px;color:var(--text2)}
.odds{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:12px}
.odds button{background:#fff;border:1.5px solid var(--border);color:var(--text);padding:10px 6px;border-radius:14px;cursor:pointer;display:flex;flex-direction:column;align-items:center;gap:3px}
.odds button:disabled{opacity:.4}
.odds button.fav{border-color:rgba(245,158,11,.5);background:rgba(245,158,11,.08)}
.odds-label-pick{font-size:10px;color:var(--text2);font-weight:600}
.odds-coef{font-size:16px;font-weight:800;color:var(--accent)}
.odds button.fav .odds-coef{color:var(--gold)}
.odds-chance{font-size:9px;color:var(--text2)}
.loading{text-align:center;padding:60px 20px;color:var(--text2)}
.error{color:var(--red);text-align:center;padding:20px;background:rgba(239,68,68,.06);border-radius:14px}
.empty{text-align:center;padding:60px 20px;color:var(--text2)}
.empty-icon{font-size:48px;margin-bottom:10px;opacity:.5}
.modal-bg{display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:100;align-items:flex-end;justify-content:center}
.modal-bg.show{display:flex}
.modal{background:#fff;border-radius:24px 24px 0 0;padding:20px;width:100%;max-width:500px;max-height:85vh;overflow-y:auto}
.modal-title{font-size:16px;font-weight:700;margin-bottom:8px}
.modal-sub{font-size:12px;color:var(--text2);margin-bottom:16px;line-height:1.5}
.field-box{position:relative;width:100%;aspect-ratio:9/13;background:linear-gradient(#2e7d32,#1b5e20);border-radius:12px;overflow:hidden;margin-bottom:14px}
.field-box::before{content:"";position:absolute;inset:4%;border:2px solid rgba(255,255,255,.5);border-radius:6px}
.field-box::after{content:"";position:absolute;left:4%;right:4%;top:50%;height:2px;background:rgba(255,255,255,.5);transform:translateY(-1px)}
.field-mid-circle{position:absolute;left:50%;top:50%;width:22%;aspect-ratio:1;border:2px solid rgba(255,255,255,.5);border-radius:50%;transform:translate(-50%,-50%)}
.player{position:absolute;transform:translate(-50%,-50%);text-align:center;width:60px}
.player-circle{width:34px;height:34px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:9px;font-weight:800;color:#fff;border:2px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,.3);margin:0 auto}
.player-circle.home{background:#e53935}
.player-circle.away{background:#1e88e5}
.player-name{font-size:9px;font-weight:700;color:#fff;background:rgba(0,0,0,.6);padding:1px 4px;border-radius:4px;margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:60px;line-height:1.1}
.field-legend{display:flex;justify-content:center;gap:20px;margin-bottom:14px;font-size:12px}
.field-legend span{display:flex;align-items:center;gap:6px}
.field-legend .dot{width:12px;height:12px;border-radius:50%}
.field-legend .dot.home{background:#e53935}
.field-legend .dot.away{background:#1e88e5}
.scheme-label{font-size:11px;color:var(--text2);font-weight:600;margin-bottom:6px;text-align:center}
.events-list{background:var(--card2);border-radius:12px;padding:12px;font-size:12px;margin-bottom:14px}
.events-list .ev{display:flex;align-items:center;gap:8px;padding:4px 0;border-bottom:1px solid var(--border)}
.events-list .ev:last-child{border-bottom:none}
.events-list .ev-minute{font-weight:700;color:var(--accent);min-width:34px}
.amount-input{width:100%;background:var(--card2);border:1.5px solid var(--border);color:var(--text);padding:14px;border-radius:14px;font-size:18px;font-weight:700;outline:none;margin-bottom:12px}
.quick-amounts{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-bottom:16px}
.quick-amounts button{background:var(--card2);border:1px solid var(--border);color:var(--text2);padding:8px;border-radius:10px;font-size:11px;font-weight:600;cursor:pointer}
.payout-preview{display:flex;justify-content:space-between;background:rgba(0,184,122,.08);border:1px solid rgba(0,184,122,.2);border-radius:12px;padding:12px;margin-bottom:16px}
.payout-preview .label{font-size:11px;color:var(--text2);text-transform:uppercase}
.payout-preview .value{font-size:16px;font-weight:800;color:var(--accent)}
.modal-actions{display:grid;grid-template-columns:1fr 2fr;gap:8px}
.modal-actions button{padding:14px;border-radius:14px;border:none;font-size:14px;font-weight:700;cursor:pointer}
.btn-cancel{background:var(--card2);color:var(--text2)}
.btn-confirm{background:linear-gradient(135deg,var(--accent),var(--accent2));color:#fff}
.toast{position:fixed;bottom:100px;left:50%;transform:translateX(-50%) translateY(20px);background:linear-gradient(135deg,var(--accent),var(--accent2));color:#fff;padding:12px 22px;border-radius:100px;font-size:13px;font-weight:700;opacity:0;transition:.3s;z-index:200;pointer-events:none;max-width:90%;text-align:center}
.toast.show{opacity:1;transform:translateX(-50%) translateY(0)}
.toast.error{background:var(--red)}
.bottom-nav{position:fixed;bottom:0;left:0;right:0;background:rgba(255,255,255,.95);backdrop-filter:blur(20px);border-top:1px solid var(--border);display:flex;padding:8px 0 max(8px,env(safe-area-inset-bottom));z-index:60}
.bottom-nav button{flex:1;background:transparent;border:none;color:var(--text2);padding:8px;font-size:10px;font-weight:600;cursor:pointer;display:flex;flex-direction:column;align-items:center;gap:3px}
.bottom-nav button .icon{font-size:20px}
.bottom-nav button.active{color:var(--accent)}
</style>
</head>
<body>
<div class="header">
<div class="header-top">
<img class="bot-avatar" src="https://images.meme-arsenal.com/1b33706ef743ada8f45708d260f40436.jpg">
<div class="logo">⚽ Football Чел</div>
<div class="balance-pill" id="balance">₽...</div>
</div>
<div class="tournaments" id="tournaments"></div>
</div>
<div class="tabs" id="main-tabs">
<button id="tab-matches" class="active" onclick="showTab('matches')">🔥 Матчи</button>
<button id="tab-bets" onclick="showTab('bets')">🎯 Мои ставки</button>
</div>
<div id="content"><div class="loading">Загрузка...</div></div>

<div class="modal-bg" id="detailModal"><div class="modal">
<div class="modal-title" id="detailTitle">Матч</div>
<div id="detailContent"></div>
<div style="margin-top:16px"><button class="btn-cancel" style="width:100%;padding:14px;border-radius:14px;border:none;font-weight:700" onclick="closeDetail()">Закрыть</button></div>
</div></div>

<div class="modal-bg" id="betModal"><div class="modal">
<div class="modal-title" id="modalTitle">Ставка</div>
<div class="modal-sub" id="modalInfo"></div>
<input class="amount-input" type="number" id="betAmount" value="1000000">
<div class="quick-amounts">
<button onclick="setAmount(1000000)">1М</button>
<button onclick="setAmount(10000000)">10М</button>
<button onclick="setAmount(100000000)">100М</button>
<button onclick="setAmount('all')">MAX</button>
</div>
<div class="payout-preview"><span class="label">Выигрыш</span><span class="value" id="payoutPreview">₽0</span></div>
<div class="modal-actions">
<button class="btn-cancel" onclick="closeModal()">Отмена</button>
<button class="btn-confirm" onclick="confirmBet()">Поставить</button>
</div>
</div></div>

<div class="toast" id="toast"></div>
<div class="bottom-nav" id="bottom-nav">
<button class="active" data-tab="matches" onclick="showTab('matches')"><span class="icon">⚽</span>Матчи</button>
<button data-tab="bets" onclick="showTab('bets')"><span class="icon">🎯</span>Ставки</button>
</div>
<script>
const tg = window.Telegram.WebApp; tg.expand(); tg.ready();
const initData = tg.initData || "";
let currentComp = "PL", currentTab = "matches", currentMatch = null, currentPick = null, currentCoef = 0, balance = 0;
let liveInterval = null;
function fmtBalance(n){return "₽"+Number(n).toLocaleString("ru-RU").replace(/,/g,".");}
function toast(msg,err){const t=document.getElementById("toast");t.textContent=msg;t.className="toast show"+(err?" error":"");setTimeout(()=>t.className="toast",2500);}
function fmtTime(iso){try{return new Date(iso).toLocaleTimeString("ru-RU",{hour:"2-digit",minute:"2-digit"});}catch(e){return "--:--";}}
function fmtDate(iso){try{const d=new Date(iso),t=new Date(),tm=new Date(t);tm.setDate(t.getDate()+1);if(d.toDateString()===t.toDateString())return"Сегодня";if(d.toDateString()===tm.toDateString())return"Завтра";return d.toLocaleDateString("ru-RU",{day:"2-digit",month:"2-digit"});}catch(e){return"";}}
function isLive(m){return ["LIVE","IN_PLAY","PAUSED"].includes(m.status);}
function isFinished(m){return m.status==="FINISHED";}
function isScheduled(m){return ["SCHEDULED","TIMED"].includes(m.status);}
function canBet(m){return isScheduled(m);}
function statusLabel(m){
  if(isLive(m))return'<span class="status-live">🔴 LIVE'+(m.minute?" "+m.minute+"'":"")+'</span>';
  if(isFinished(m))return'<span style="color:var(--text2)">✓ Завершён</span>';
  return'<span class="status-sched">'+fmtDate(m.utcDate)+' · '+fmtTime(m.utcDate)+'</span>';
}
async function loadBalance(){
  if(!initData){document.getElementById("balance").textContent="no initData";return;}
  try{
    const r=await fetch("/api/my_balance?initData="+encodeURIComponent(initData));
    const d=await r.json();
    if(r.status!==200){document.getElementById("balance").textContent="ERR";return;}
    balance=d.balance||0;
    document.getElementById("balance").textContent=fmtBalance(balance);
  }catch(e){document.getElementById("balance").textContent="NET";}
}
async function loadComps(){
  try{
    const r=await fetch("/api/competitions");const comps=await r.json();
    const el=document.getElementById("tournaments");el.innerHTML="";let first=true;
    for(const [code,name] of Object.entries(comps)){
      const b=document.createElement("button");b.textContent=name;
      if(first){b.classList.add("active");currentComp=code;first=false;}
      b.onclick=()=>{document.querySelectorAll("#tournaments button").forEach(x=>x.classList.remove("active"));b.classList.add("active");currentComp=code;showTab(currentTab);};
      el.appendChild(b);
    }
  }catch(e){}
}
async function loadMatches(){
  const el=document.getElementById("content");el.innerHTML='<div class="loading">Загрузка...</div>';
  try{
    const r=await fetch("/api/matches?competition="+currentComp);const d=await r.json();
    if(d.error){el.innerHTML='<div class="error">'+d.error+'</div>';return;}
    if(!d.matches||!d.matches.length){el.innerHTML='<div class="empty"><div class="empty-icon">⚽</div>Нет матчей</div>';return;}
    el.innerHTML="";d.matches.forEach(m=>el.appendChild(renderMatch(m)));
  }catch(e){el.innerHTML='<div class="error">'+e.message+'</div>';}
}
function renderMatch(m){
  const c=document.createElement("div");c.className="match";const o=m.odds;
  const fh=o.favorite==="home",fa=o.favorite==="away";
  const hs=m.score?.home,as_=m.score?.away;
  const ss=(isLive(m)||isFinished(m))&&hs!==null&&as_!==null;const lk=!canBet(m);
  c.innerHTML='<div class="match-top"><span>'+(m.competition||"")+'</span>'+statusLabel(m)+'</div>'+
'<div class="teams">'+
'<div class="team"><div class="team-logo-wrap"><img src="'+m.home.crest+'" onerror="this.style.display=\'none\'"></div><div class="team-name">'+m.home.name+'</div></div>'+
'<div><div class="score '+(ss?"":"vs")+'">'+(ss?hs+":"+as_:"VS")+'</div>'+(m.minute&&isLive(m)?'<div style="text-align:center;color:var(--red);font-size:10px;font-weight:700">'+m.minute+"'</div>":"")+'</div>'+
'<div class="team"><div class="team-logo-wrap"><img src="'+m.away.crest+'" onerror="this.style.display=\'none\'"></div><div class="team-name">'+m.away.name+'</div></div>'+
'</div>'+
'<div class="odds">'+
'<button class="'+(fh?"fav":"")+'" data-p="home" '+(lk?"disabled":"")+'><span class="odds-label-pick">Победа 1</span><span class="odds-coef">'+o.home.toFixed(2)+'</span>'+(lk?"":'<span class="odds-chance">'+o.home_chance+'%</span>')+'</button>'+
'<button data-p="draw" '+(lk?"disabled":"")+'><span class="odds-label-pick">Ничья</span><span class="odds-coef">'+o.draw.toFixed(2)+'</span>'+(lk?"":'<span class="odds-chance">'+o.draw_chance+'%</span>')+'</button>'+
'<button class="'+(fa?"fav":"")+'" data-p="away" '+(lk?"disabled":"")+'><span class="odds-label-pick">Победа 2</span><span class="odds-coef">'+o.away.toFixed(2)+'</span>'+(lk?"":'<span class="odds-chance">'+o.away_chance+'%</span>')+'</button>'+
'</div>';
  c.onclick=(e)=>{if(e.target.closest(".odds button"))return;openDetail(m.id);};
  c.querySelectorAll(".odds button").forEach(b=>{if(b.disabled)return;b.onclick=(e)=>{e.stopPropagation();openBet(m,b.dataset.p,o[b.dataset.p]);};});
  return c;
}
function drawField(homeSquad, awaySquad, homeName, awayName, hScheme, aScheme){
  let html='<div class="field-legend"><span><span class="dot home"></span>'+homeName+' ('+hScheme+')</span><span><span class="dot away"></span>'+awayName+' ('+aScheme+')</span></div>';
  html+='<div class="field-box"><div class="field-mid-circle"></div>';
  homeSquad.forEach(p=>{
    const left=(p.x*100).toFixed(1)+"%";
    const top=((1-p.y)*100*0.5+5).toFixed(1)+"%";
    html+='<div class="player" style="left:'+left+';top:'+top+';"><div class="player-circle home">'+p.p+'</div><div class="player-name">'+p.n+'</div></div>';
  });
  awaySquad.forEach(p=>{
    const left=(p.x*100).toFixed(1)+"%";
    const top=((p.y)*100*0.5+45).toFixed(1)+"%";
    html+='<div class="player" style="left:'+left+';top:'+top+';"><div class="player-circle away">'+p.p+'</div><div class="player-name">'+p.n+'</div></div>';
  });
  html+='</div>';
  return html;
}
async function openDetail(mid){
  document.getElementById("detailTitle").textContent="Загрузка...";
  document.getElementById("detailContent").innerHTML="";
  document.getElementById("detailModal").classList.add("show");
  try{
    const r=await fetch("/api/match/"+mid);const m=await r.json();
    if(m.error){document.getElementById("detailContent").innerHTML='<div class="error">'+m.error+'</div>';return;}
    const h=m.homeTeam||{},a=m.awayTeam||{};
    const hs=m.score?.fullTime?.home,as_=m.score?.fullTime?.away;
    const lv=isLive(m),fn=isFinished(m);const ss=(lv||fn)&&hs!==null&&as_!==null;
    let homeSquad=[], awaySquad=[], hScheme="", aScheme="";
    try{
      const hr=await fetch("/api/squad_pair/"+encodeURIComponent(h.shortName||h.name||"")+"/"+encodeURIComponent(a.shortName||a.name||""));
      const hd=await hr.json();
      homeSquad=hd.home.players||[]; hScheme=hd.home.scheme||"";
      awaySquad=hd.away.players||[]; aScheme=hd.away.scheme||"";
    }catch(e){}
    let eventsHtml="";
    try{
      const er=await fetch("/api/match_events/"+mid);const ed=await er.json();
      if(ed.events && ed.events.length){
        eventsHtml='<div class="events-list"><div style="font-weight:700;margin-bottom:6px">📋 События матча</div>';
        ed.events.forEach(ev=>{
          const icon = ev.type==="goal"?"⚽":ev.type==="yellow"?"🟨":ev.type==="red"?"🟥":ev.type==="sub"?"🔄":"•";
          eventsHtml+='<div class="ev"><span class="ev-minute">'+ev.minute+"'</span><span>"+icon+"</span><span>"+(ev.player||"")+(ev.extra?" — "+ev.extra:"")+'</span></div>';
        });
        eventsHtml+='</div>';
      }
    }catch(e){}
    let html='<div style="text-align:center;margin-bottom:14px">'+
      '<div style="font-size:12px;color:var(--text2);margin-bottom:8px">'+(m.competition?.name||"")+'</div>'+
      '<div style="display:flex;align-items:center;justify-content:center;gap:12px;margin-bottom:8px">'+
        '<div style="text-align:center;flex:1"><img src="'+(h.crest||"")+'" style="width:44px;height:44px;object-fit:contain"><div style="font-size:12px;font-weight:700;margin-top:4px">'+(h.shortName||h.name||"")+'</div></div>'+
        '<div style="font-size:22px;font-weight:800">'+(ss?hs+":"+as_:"VS")+'</div>'+
        '<div style="text-align:center;flex:1"><img src="'+(a.crest||"")+'" style="width:44px;height:44px;object-fit:contain"><div style="font-size:12px;font-weight:700;margin-top:4px">'+(a.shortName||a.name||"")+'</div></div>'+
      '</div>'+
      '<div style="font-size:11px;color:var(--text2);margin-bottom:6px">'+(lv?'🔴 LIVE '+(m.minute||"")+"'":fn?'✓ Завершён':fmtDate(m.utcDate)+" "+fmtTime(m.utcDate))+'</div>'+
    '</div>';
    if(homeSquad.length && awaySquad.length){
      html += drawField(homeSquad, awaySquad, h.shortName||h.name||"Дом", a.shortName||a.name||"Гости", hScheme, aScheme);
    }
    html += eventsHtml;
    html += '<div style="background:var(--card2);border-radius:12px;padding:12px;font-size:12px;margin-bottom:14px">'+
      '<div>Стадион: <b>'+(m.venue||"—")+'</b></div>'+
      '<div>Тур: <b>'+(m.matchday?("День "+m.matchday):"—")+'</b></div>'+
    '</div>';
    document.getElementById("detailTitle").textContent=(h.shortName||h.name||"")+" — "+(a.shortName||a.name||"");
    document.getElementById("detailContent").innerHTML=html;
  }catch(e){document.getElementById("detailContent").innerHTML='<div class="error">'+e.message+'</div>';}
}
function closeDetail(){
  document.getElementById("detailModal").classList.remove("show");
}
function openBet(match,pick,coef){
  if(!canBet(match)){toast("Ставки закрыты",true);return;}
  currentMatch=match;currentPick=pick;currentCoef=coef;
  const lbl=pick==="home"?"Победа 1":pick==="draw"?"Ничья":"Победа 2";
  const tn=pick==="home"?match.home.name:pick==="draw"?"Ничья":match.away.name;
  document.getElementById("modalTitle").textContent=lbl+" · "+tn;
  document.getElementById("modalInfo").innerHTML=match.home.name+" — "+match.away.name+"<br>Коэф: <b>x"+coef.toFixed(2)+"</b><br>Баланс: <b>"+fmtBalance(balance)+"</b>";
  document.getElementById("betAmount").value="1000000";
  updatePay();document.getElementById("betModal").classList.add("show");
}
function updatePay(){const a=parseInt(document.getElementById("betAmount").value)||0;document.getElementById("payoutPreview").textContent=fmtBalance(Math.floor(a*currentCoef));}
document.getElementById("betAmount").addEventListener("input",updatePay);
function setAmount(v){document.getElementById("betAmount").value=v==="all"?balance:v;updatePay();}
function closeModal(){document.getElementById("betModal").classList.remove("show");currentMatch=null;}
async function confirmBet(){
  const a=parseInt(document.getElementById("betAmount").value);
  if(!a||a<100000){toast("Мин. 100.000",true);return;}
  if(a>balance){toast("Недостаточно",true);return;}
  try{
    const r=await fetch("/api/bet",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({initData:initData,matchId:currentMatch.id,pick:currentPick,amount:a,coefficient:currentCoef,competition:currentComp})});
    const d=await r.json();
    if(d.ok){balance=d.balance;document.getElementById("balance").textContent=fmtBalance(balance);closeModal();toast("✅ Ставка "+fmtBalance(a));}
    else toast("❌ "+d.error,true);
  }catch(e){toast("Ошибка",true);}
}
async function renderMyBets(){
  const el=document.getElementById("content");el.innerHTML='<div class="loading">Загрузка...</div>';
  if(!initData){el.innerHTML='<div class="empty">Нет initData</div>';return;}
  try{
    const r=await fetch("/api/my_bets?initData="+encodeURIComponent(initData));const d=await r.json();
    if(!d.bets||!d.bets.length){el.innerHTML='<div class="empty"><div class="empty-icon">🎯</div>У тебя нет ставок</div>';return;}
    el.innerHTML="";
    d.bets.forEach(b=>{
      const lbl=b.pick==="home"?("Победа 1 ("+b.home+")"):b.pick==="draw"?"Ничья":("Победа 2 ("+b.away+")");
      let st="⏳ В игре",cls="";
      if(b.status==="won"){st="✅ ВЫИГРЫШ +"+fmtBalance(b.payout);cls="color:var(--accent);font-weight:700";}
      if(b.status==="lost"){st="❌ Проигрыш";cls="color:var(--red);font-weight:700";}
      const d2=document.createElement("div");d2.className="match";
      d2.innerHTML='<div style="font-weight:700;margin-bottom:8px">'+b.home+" — "+b.away+'</div><div style="font-size:12px;color:var(--text2);margin-bottom:6px">'+lbl+" · "+fmtBalance(b.amount)+" · x"+(b.coefficient||1).toFixed(2)+'</div><div style="font-size:12px;'+cls+'">'+st+'</div>';
      el.appendChild(d2);
    });
  }catch(e){el.innerHTML='<div class="error">'+e.message+'</div>';}
}
function showTab(t){
  currentTab=t;
  document.querySelectorAll(".tabs button").forEach(b=>b.classList.remove("active"));
  document.querySelectorAll(".bottom-nav button").forEach(b=>b.classList.toggle("active",b.dataset.tab===t));
  const tb=document.getElementById("tab-"+t);if(tb)tb.classList.add("active");
  if(t=="matches")loadMatches();else renderMyBets();
}
loadBalance();loadComps().then(loadMatches);
</script>
</body>
</html>"""

@app.get("/", response_class=HTMLResponse)
async def index(): return FOOTBALL_HTML

@app.get("/health")
async def health(): return {"status":"ok"} # ========= ЦИКЛЫ =========
async def top3_loop():
    while True:
        try:
            now_utc = datetime.utcnow(); now_msk = now_utc + timedelta(hours=3)
            days = (5 - now_msk.weekday()) % 7
            tgt = now_msk.replace(hour=12,minute=55,second=0,microsecond=0) + timedelta(days=days)
            if tgt <= now_msk: tgt += timedelta(days=7)
            wait = (tgt - now_msk).total_seconds()
            if wait > 0:
                await asyncio.sleep(min(wait,60)); continue
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
        except Exception as e:
            print(f"top3: {e}")
            await asyncio.sleep(3600)

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
            drop_data = {"active":True,"city":rc,"amount":amount,"expires_at":datetime.now()+timedelta(hours=2),"claimed":False,"creator_id":None}
            print(f"[AUTO-DROP] {rc}: {amount}")
        except Exception as e: print(f"drop: {e}")

def _parse_score(s):
    """'2:1' -> (2,1), None -> (None, None)"""
    if not s or ":" not in s: return None, None
    try:
        a, b = s.split(":")
        return int(a), int(b)
    except: return None, None

async def football_events_loop():
    """
    Каждые 60 секунд проверяет live-матчи, на которые есть ставки.
    Парсит события (голы) из данных API и рассылает в личку.
    """
    # Хранит последний счёт по матчу, чтобы не повторять голы
    seen_scores = {}  # {fixture_id: (home, away)}
    while True:
        try:
            conn = get_db_connection(); c = conn.cursor()
            c.execute("SELECT DISTINCT fixture_id FROM football_bets WHERE status = 'pending'")
            ids = [r[0] for r in c.fetchall()]; conn.close()
            for fid in ids:
                try:
                    m = await fb_fixture(fid)
                except: continue
                st = m.get("status","")
                # только live или завершённые
                if st not in ("IN_PLAY","LIVE","PAUSED","FINISHED","1H","2H","HT"): continue
                score_obj = m.get("score",{})
                cur = score_obj.get("fullTime",{}) or score_obj.get("halfTime",{})
                hs = cur.get("home"); as_ = cur.get("away")
                if hs is None or as_ is None: continue
                last = seen_scores.get(fid)
                # если счёт изменился → был гол
                if last is not None and (hs, as_) != last:
                    # определяем, кто забил
                    dh = hs - last[0]
                    da = as_ - last[1]
                    hn = m["homeTeam"].get("shortName") or m["homeTeam"].get("name","?")
                    an = m["awayTeam"].get("shortName") or m["awayTeam"].get("name","?")
                    minute = m.get("minute", "?")
                    # сохраняем событие в БД
                    scorer_team = hn if dh > 0 else an
                    conn = get_db_connection(); c = conn.cursor()
                    c.execute("INSERT INTO football_events (fixture_id,event_type,minute,player,team,score_home,score_away,extra,created_at) VALUES (?,?,?,?,?,?,?,?,?)",
                        (fid, "goal", minute, "", scorer_team, hs, as_, "", datetime.now().isoformat()))
                    conn.commit(); conn.close()
                    # рассылаем тем, кто ставил
                    conn = get_db_connection(); c = conn.cursor()
                    c.execute("SELECT user_id,pick,home_team,away_team FROM football_bets WHERE fixture_id = ? AND status = 'pending'", (fid,))
                    for uid, pick, home_team, away_team in c.fetchall():
                        try:
                            await bot.send_message(uid,
                                f"⚽ <b>ГОЛ!</b>\n\n"
                                f"{hn} {hs}:{as_} {an}\n"
                                f"⏱ Минута: {minute}'\n"
                                f"🥅 Забил: <b>{scorer_team}</b>",
                                parse_mode=ParseMode.HTML)
                        except: pass
                    conn.close()
                seen_scores[fid] = (hs, as_)
            # чистим seen_scores от матчей, которые больше не pending
            conn = get_db_connection(); c = conn.cursor()
            c.execute("SELECT DISTINCT fixture_id FROM football_bets WHERE status = 'pending'")
            active = {r[0] for r in c.fetchall()}; conn.close()
            for k in list(seen_scores.keys()):
                if k not in active: del seen_scores[k]
        except Exception as e:
            print(f"fb events: {e}")
        await asyncio.sleep(60)

async def football_result_loop():
    """Каждые 2 минуты проверяет завершённые матчи и рассчитывает ставки."""
    while True:
        try:
            conn = get_db_connection(); c = conn.cursor()
            c.execute("SELECT DISTINCT fixture_id FROM football_bets WHERE status = 'pending'")
            ids = [r[0] for r in c.fetchall()]; conn.close()
            for fid in ids:
                try:
                    m = await fb_fixture(fid)
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
                for bid, uid, pick, amount, coef in c.fetchall():
                    if pick == res:
                        pay = int(amount * coef)
                        c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (pay, uid))
                        c.execute("UPDATE football_bets SET status='won',result=?,payout=? WHERE id=?", (res, pay, bid))
                        try:
                            await bot.send_message(uid,
                                f"🏆 <b>ТЫ ВЫИГРАЛ!</b>\n\n⚽ {hn} {hs}:{as_} {an}\n💰 +{format_balance(pay)}",
                                parse_mode=ParseMode.HTML)
                        except: pass
                    else:
                        c.execute("UPDATE football_bets SET status='lost',result=?,payout=0 WHERE id=?", (res, bid))
                        try:
                            await bot.send_message(uid,
                                f"❌ <b>Ставка проиграла</b>\n\n⚽ {hn} {hs}:{as_} {an}",
                                parse_mode=ParseMode.HTML)
                        except: pass
                conn.commit(); conn.close()
        except Exception as e:
            print(f"fb result: {e}")
        await asyncio.sleep(120)

async def football_reminder_loop():
    """За 15 минут до матча шлёт напоминание тем, кто ставил."""
    while True:
        try:
            conn = get_db_connection(); c = conn.cursor()
            c.execute("SELECT id,user_id,fixture_id,home_team,away_team,pick,amount FROM football_bets WHERE status = 'pending' AND reminded = 0")
            bets = c.fetchall(); conn.close()
            now = datetime.utcnow()
            for bid, uid, fid, home, away, pick, amount in bets:
                try:
                    m = await fb_fixture(fid)
                    utc = datetime.fromisoformat(m["utcDate"].replace("Z","+00:00")).replace(tzinfo=None)
                    diff = (utc - now).total_seconds() / 60.0
                    if 12 <= diff <= 18:
                        lbl = "П1" if pick == "home" else "Х" if pick == "draw" else "П2"
                        try:
                            await bot.send_message(uid,
                                f"⏰ <b>Напоминание</b>\n\n"
                                f"Матч <b>{home} — {away}</b>\n"
                                f"начнётся через ~15 минут!\n\n"
                                f"Твоя ставка: <b>{lbl}</b> на {format_balance(amount)}",
                                parse_mode=ParseMode.HTML)
                        except: pass
                        conn = get_db_connection(); c = conn.cursor()
                        c.execute("UPDATE football_bets SET reminded = 1 WHERE id = ?", (bid,))
                        conn.commit(); conn.close()
                except: continue
        except Exception as e:
            print(f"fb remind: {e}")
        await asyncio.sleep(300)

# ========= РИСОВАЛКА ПОЛЯ (PIL) для /состав =========
def _load_font(size):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
        "DejaVuSans-Bold.ttf",
    ]
    for p in paths:
        try: return ImageFont.truetype(p, size)
        except: continue
    return ImageFont.load_default()

def draw_football_field(home_name, away_name, home_squad, away_squad):
    W, H = 900, 1200
    img = Image.new("RGB", (W, H), (34, 139, 34))
    draw = ImageDraw.Draw(img)
    pad = 40
    fx0, fy0, fx1, fy1 = pad, pad + 60, W - pad, H - pad
    draw.rectangle([fx0, fy0, fx1, fy1], outline=(255,255,255), width=4)
    cy = (fy0 + fy1) // 2
    draw.line([fx0, cy, fx1, cy], fill=(255,255,255), width=3)
    r = 90
    draw.ellipse([W//2 - r, cy - r, W//2 + r, cy + r], outline=(255,255,255), width=3)
    draw.ellipse([W//2 - 6, cy - 6, W//2 + 6, cy + 6], fill=(255,255,255))
    box_w, box_h = 320, 160
    draw.rectangle([W//2 - box_w//2, fy0, W//2 + box_w//2, fy0 + box_h], outline=(255,255,255), width=3)
    draw.rectangle([W//2 - box_w//2, fy1 - box_h, W//2 + box_w//2, fy1], outline=(255,255,255), width=3)
    goal_w = 160
    draw.rectangle([W//2 - goal_w//2, fy0 - 6, W//2 + goal_w//2, fy0], fill=(255,255,255))
    draw.rectangle([W//2 - goal_w//2, fy1, W//2 + goal_w//2, fy1 + 6], fill=(255,255,255))
    font_name = _load_font(15)
    font_title = _load_font(26)
    draw.text((W//2, 15), f"{home_name}  vs  {away_name}", fill=(255,255,255), font=font_title, anchor="ma")
    field_h = fy1 - fy0
    field_w = fx1 - fx0
    def draw_player(pl, color, flip_y):
        px = fx0 + pl["x"] * field_w
        py = fy0 + ((1 - pl["y"]) * field_h if not flip_y else pl["y"] * field_h)
        r = 20
        draw.ellipse([px - r, py - r, px + r, py + r], fill=color, outline=(255,255,255), width=3)
        draw.text((px, py), pl["p"][:2], fill=(255,255,255), font=_load_font(13), anchor="mm")
        nm = pl["n"][:14]
        try:
            bbox = draw.textbbox((0,0), nm, font=font_name)
            tw = bbox[2] - bbox[0]; th = bbox[3] - bbox[1]
        except: tw, th = len(nm)*8, 15
        ty = py + r + 2
        if flip_y: ty = py - r - th - 4
        draw.rectangle([px - tw//2 - 4, ty - 2, px + tw//2 + 4, ty + th + 2], fill=(0,0,0))
        draw.text((px, ty), nm, fill=(255,255,255), font=font_name, anchor="ma")
    for pl in home_squad: draw_player(pl, (200, 30, 30), False)
    for pl in away_squad: draw_player(pl, (30, 60, 200), True)
    buf = io.BytesIO(); img.save(buf, format='PNG'); buf.seek(0)
    return BufferedInputFile(buf.getvalue(), filename="field.png")

# ========= ЗАПУСК =========
_started = {"done": False}

@app.on_event("startup")
async def on_startup():
    if _started["done"]: return
    _started["done"] = True
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE is_banned = 1")
    for (uid,) in c.fetchall(): banned_users.add(uid)
    conn.close()
    asyncio.create_task(_run_bot())
    asyncio.create_task(top3_loop())
    asyncio.create_task(taxi_reminder_loop())
    asyncio.create_task(drop_loop())
    asyncio.create_task(football_result_loop())
    asyncio.create_task(football_reminder_loop())
    asyncio.create_task(football_events_loop())
    print("="*50)
    print("🤖 Football Чел запущен")
    print("="*50)

async def _run_bot():
    try:
        print("🎯 Запускаю polling...", flush=True)
        await bot.delete_webhook(drop_pending_updates=True)
        me = await bot.get_me()
        print(f"✅ Бот подключён: @{me.username} (id={me.id})", flush=True)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        print(f"❌ POLLING CRASH: {type(e).__name__}: {e}", flush=True)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
