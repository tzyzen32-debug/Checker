import os
import json
import random
import datetime
import pytz
import asyncio
import io
import main
import sys
import re
from collections import Counter

from pyrogram import Client, filters, errors
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

# --- CONFIGURATION ---
BOT_TOKEN = "8853292732:AAH7a0QsBbco8RtoOZGyD3vL2BM7yVUt5fQ"
ADMIN_ID = 7472543084
KEYS_FILE = "keys.json"
user_state = {}

# Nilagay ko na dito yung API ID at API HASH mo
app = Client(
    "my_bot",
    api_id=30387151,
    api_hash="527ac3a7ab796b5ed46b1a1656c1e554",
    bot_token=BOT_TOKEN
)

# --- DATABASE HELPERS ---
def load_keys():
    return json.load(open(KEYS_FILE)) if os.path.exists(KEYS_FILE) else {}

def save_keys(data):
    with open(KEYS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def check_user_access(user_id):
    keys = load_keys()
    u_id = str(user_id)
    if user_id == ADMIN_ID: return True
    for info in keys.values():
        if str(info.get("redeemed_by")) == u_id:
            if datetime.datetime.fromisoformat(info["expiry"]) > datetime.datetime.now():
                return True
    return False

def restricted_check(_, __, message):
    return check_user_access(message.from_user.id)

# --- CORE COMMANDS ---

@app.on_message(filters.command("start"))
async def start(client, message):
    if check_user_access(message.from_user.id):
        await message.reply("✅ Welcome back! Active access.")
    else:
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Buy Key", url="https://t.me/ASHxDeath")]])
        await message.reply("👋 Welcome! Use `/redeem <key>` to start.", reply_markup=keyboard)

@app.on_message(filters.command("generate") & filters.user(ADMIN_ID))
async def generate_key(client, message):
    try:
        args = message.text.split()
        if len(args) != 2: return await message.reply("❌ Usage: `/generate 1d` (d=days, h=hours)")
        unit, amount = args[1][-1].lower(), int(args[1][:-1])
        delta = {"d": datetime.timedelta(days=amount), "h": datetime.timedelta(hours=amount)}.get(unit)
        expiry = (datetime.datetime.now() + delta).isoformat()
        key = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=15))
        keys = load_keys(); keys[key] = {"expiry": expiry, "redeemed_by": None}; save_keys(keys)
        await message.reply(f"✅ Key: `{key}`\n⏳ Expires: {expiry}")
    except: await message.reply("❌ Error generating key.")

@app.on_message(filters.command("redeem"))
async def redeem_key(client, message):
    args = message.text.split()
    if len(args) != 2: return await message.reply("❌ Usage: `/redeem <key>`")
    key, u_id, keys = args[1], str(message.from_user.id), load_keys()
    if key in keys and not keys[key]["redeemed_by"]:
        keys[key]["redeemed_by"] = u_id
        save_keys(keys)
        await message.reply("✅ Success! Access granted.")
    else: await message.reply("❌ Invalid or already used key.")

# --- SEARCH SYSTEM ---

@app.on_message(filters.command("search") & filters.create(restricted_check))
async def search_menu(client, message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎲 Roblox", callback_data="keyword_roblox"), InlineKeyboardButton("🔥 MLBB", callback_data="keyword_mobilelegends")],
        [InlineKeyboardButton("🛡 Garena", callback_data="expand_garena"), InlineKeyboardButton("🌐 Socials", callback_data="expand_socmeds")],
        [InlineKeyboardButton("🎮 Gaming", callback_data="expand_gaming")]
    ])
    await message.reply("🔎 Choose Category:", reply_markup=keyboard)

@app.on_callback_query(filters.regex("^expand_"))
async def expand_menus(client, callback_query):
    data = callback_query.data
    if "garena" in data:
        btns = [[InlineKeyboardButton("🎮 Garena.com", callback_data="keyword_garena.com")], [InlineKeyboardButton("🔙 Back", callback_data="back_to_main")]]
        await callback_query.message.edit_text("🛡 Garena Categories:", reply_markup=InlineKeyboardMarkup(btns))
    elif "socmeds" in data:
        btns = [[InlineKeyboardButton("📘 Facebook", callback_data="keyword_facebook.com"), InlineKeyboardButton("📸 Instagram", callback_data="keyword_instagram.com")], [InlineKeyboardButton("🔙 Back", callback_data="back_to_main")]]
        await callback_query.message.edit_text("🌐 Social Media:", reply_markup=InlineKeyboardMarkup(btns))
    elif "gaming" in data:
        btns = [[InlineKeyboardButton("🎮 Riot Games", callback_data="keyword_riotgames.com"), InlineKeyboardButton("🕹 Steam", callback_data="keyword_steampowered.com")], [InlineKeyboardButton("🔙 Back", callback_data="back_to_main")]]
        await callback_query.message.edit_text("🎮 Gaming Categories:", reply_markup=InlineKeyboardMarkup(btns))

@app.on_callback_query(filters.regex("^back_to_main$"))
async def back_main(client, cb): await search_menu(client, cb.message)

@app.on_callback_query(filters.regex("^keyword_"))
async def handle_search(client, cb):
    kw = cb.data.split("_")[1]
    await cb.message.edit_text(f"⏳ Searching for `{kw}`...")
    log_files = sorted([f for f in os.listdir() if re.fullmatch(r"logs\d+\.txt", f)])
    results = []
    for log in log_files:
        if os.path.exists(log):
            with open(log, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if kw.lower() in line.lower(): 
                        parts = line.strip().split(":")
                        results.append(":".join(parts[-2:]) if len(parts) >= 2 else line.strip())
    
    if not results: return await cb.message.edit_text(f"❌ No matches for `{kw}`.")
    
    res_path = f"results_{kw}.txt"
    sample_size = min(len(results), 500)
    with open(res_path, "w", encoding="utf-8") as f: 
        f.write("\n".join(random.sample(results, sample_size)))
    
    await client.send_document(cb.message.chat.id, res_path, caption=f"🔎 Keyword: `{kw}`\n✅ Found: {len(results)}")
    os.remove(res_path)

# --- FILE CLEANER ---

@app.on_message(filters.command("removeurl") & filters.create(restricted_check))
async def remove_url_req(client, message):
    user_state[message.from_user.id] = "awaiting_file"
    await message.reply("📂 Send the .txt file to clean (Remove URL).")

@app.on_message(filters.document & filters.create(restricted_check))
async def process_doc(client, message):
    if user_state.get(message.from_user.id) != "awaiting_file": return
    user_state.pop(message.from_user.id)
    path = await message.download()
    with open(path, "r", encoding="utf-8", errors="ignore") as f: lines = f.readlines()
    cleaned = []
    for l in lines:
        parts = l.strip().split(':')
        cleaned.append(f"{parts[-2]}:{parts[-1]}" if len(parts) >= 2 else l.strip())
    
    out_path = "cleaned_accounts.txt"
    with open(out_path, "w", encoding="utf-8") as f: f.write("\n".join(cleaned))
    await client.send_document(message.chat.id, out_path, caption="✅ URLs removed.")
    os.remove(path); os.remove(out_path)

print("Bot is starting with your API credentials...")
app.run()
