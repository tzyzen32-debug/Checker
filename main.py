import os
import json
import random
import datetime
import re
from flask import Flask
from threading import Thread
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

# --- CONFIGURATION ---
BOT_TOKEN = "8853292732:AAH7a0QsBbco8RtoOZGyD3vL2BM7yVUt5fQ"
ADMIN_ID = 7472543084
KEYS_FILE = "keys.json"
user_state = {}

# --- [KUSA] AUTO-CREATE NECESSARY FILES ---
# Gagawa ng keys.json kung wala pa
if not os.path.exists(KEYS_FILE):
    with open(KEYS_FILE, "w") as f:
        json.dump({}, f)

# Gagawa ng sample logs1.txt kung wala pa para hindi mag-error ang search
if not os.path.exists("logs1.txt"):
    with open("logs1.txt", "w") as f:
        f.write("admin:admin123\nsample_user:pass123")

# Initialize Flask and Pyrogram
flask_app = Flask(__name__)
app = Client(
    "my_bot",
    api_id=30387151,
    api_hash="527ac3a7ab796b5ed46b1a1656c1e554",
    bot_token=BOT_TOKEN
)

# --- HELPERS ---
def load_keys():
    try:
        if os.path.exists(KEYS_FILE):
            with open(KEYS_FILE, "r") as f:
                return json.load(f)
    except:
        return {}
    return {}

def save_keys(data):
    with open(KEYS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def check_user_access(user_id):
    if user_id == ADMIN_ID: return True
    keys = load_keys()
    u_id = str(user_id)
    for info in keys.values():
        if str(info.get("redeemed_by")) == u_id:
            expiry = datetime.datetime.fromisoformat(info["expiry"])
            if expiry > datetime.datetime.now():
                return True
    return False

def restricted_check(_, __, message):
    return check_user_access(message.from_user.id)

# --- FLASK WEB API ---
@flask_app.route('/check/<user_id>', methods=['GET'])
def check_id_api(user_id):
    keys = load_keys()
    u_id = str(user_id)
    
    if int(user_id) == ADMIN_ID:
        return f"VERIFIED|ADMIN", 200
        
    for info in keys.values():
        if str(info.get("redeemed_by")) == u_id:
            expiry_str = info["expiry"]
            expiry_dt = datetime.datetime.fromisoformat(expiry_str)
            if expiry_dt > datetime.datetime.now():
                return f"VERIFIED|{expiry_str}", 200
            else:
                return "EXPIRED", 403
                
    return "DENIED", 403

# --- BOT COMMANDS ---
@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    if check_user_access(message.from_user.id):
        await message.reply("✅ **Access Active!**\nGamitin ang `/search` para magsimula.")
    else:
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🛒 Buy Access Key", url="https://t.me/ASHxDeath")]])
        await message.reply(
            "👋 **Welcome!**\n\nKailangan mo ng key para magamit ang bot.\nGamitin ang `/redeem <key>`.", 
            reply_markup=keyboard
        )

@app.on_message(filters.command("search") & filters.create(restricted_check))
async def search_menu(client, message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎲 Roblox", callback_data="keyword_roblox"), InlineKeyboardButton("🔥 MLBB", callback_data="keyword_mobilelegends")],
        [InlineKeyboardButton("🛡 Garena", callback_data="expand_garena"), InlineKeyboardButton("🌐 Socials", callback_data="expand_socmeds")],
        [InlineKeyboardButton("🎮 Gaming", callback_data="expand_gaming")]
    ])
    await message.reply("🔎 **Database Search**\nPumili ng kategorya:", reply_markup=keyboard)

@app.on_message(filters.command("generate") & filters.user(ADMIN_ID))
async def gen_key(client, message):
    try:
        args = message.text.split()
        if len(args) < 2: return await message.reply("Gamit: `/generate 1d` o `/generate 1h`")
        time_val = args[1]
        amount = int(time_val[:-1])
        unit = time_val[-1].lower()
        delta = datetime.timedelta(days=amount) if unit == 'd' else datetime.timedelta(hours=amount)
        expiry = (datetime.datetime.now() + delta).isoformat()
        key = "PREM-" + "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=10))
        keys = load_keys()
        keys[key] = {"expiry": expiry, "redeemed_by": None}
        save_keys(keys)
        await message.reply(f"✅ **Key Generated:** `{key}`\n⏳ **Valid for:** {time_val}")
    except:
        await message.reply("❌ Format error. Example: `/generate 30d`")

@app.on_message(filters.command("redeem"))
async def redeem_cmd(client, message):
    args = message.text.split()
    if len(args) < 2: return await message.reply("Gamit: `/redeem YOUR_KEY`")
    key_input = args[1]
    keys = load_keys()
    u_id = str(message.from_user.id)
    if key_input in keys and keys[key_input]["redeemed_by"] is None:
        keys[key_input]["redeemed_by"] = u_id
        save_keys(keys)
        await message.reply("✅ **Success!** May access ka na.")
    else:
        await message.reply("❌ Invalid o nagamit na ang key.")

@app.on_callback_query(filters.regex("^back_to_main$"))
async def back_main(client, cb):
    await search_menu(client, cb.message)

@app.on_callback_query(filters.regex("^keyword_"))
async def handle_search(client, cb):
    kw = cb.data.split("_")[1]
    await cb.message.edit_text(f"⏳ Searching database for: `{kw}`...")
    
    log_files = sorted([f for f in os.listdir() if re.fullmatch(r"logs\d+\.txt", f)])
    results = []
    
    for log in log_files:
        with open(log, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if kw.lower() in line.lower(): 
                    results.append(line.strip())
    
    if not results:
        return await cb.message.edit_text(f"❌ No matches found for `{kw}`.")
    
    res_path = f"results_{kw}.txt"
    with open(res_path, "w") as f: f.write("\n".join(results[:500]))
    
    await client.send_document(cb.message.chat.id, res_path, caption=f"✅ Found: {len(results)}")
    os.remove(res_path)

# --- RUNNER ---
def run_flask():
    flask_app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

if __name__ == "__main__":
    Thread(target=run_flask).start()
    print("Bot and Web API starting...")
    app.run()
