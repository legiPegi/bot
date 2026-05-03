import telebot
import json
import os
from datetime import datetime

BOT_TOKEN = os.environ.get("8611229526:AAHR4-m-sQpiyCNoyGGdDumR6EoJniVB9VU")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))

bot = telebot.TeleBot(BOT_TOKEN)
DATA_FILE = "mahsulotlar.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"mahsulotlar": [], "oxirgi_id": 0}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

user_states = {}

@bot.message_handler(commands=["start"])
def start(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id,
            "👋 Xush kelibsiz, Admin!\n\n"
            "📦 /qoshish — Yangi mahsulot qo'shish\n"
            "📋 /royxat — Barcha mahsulotlar\n"
            "🗑 /del [ID] — Mahsulot o'chirish")
    else:
        bot.send_message(message.chat.id, "⛔ Siz admin emassiz.")

@bot.message_handler(commands=["qoshish"])
def qoshish(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "⛔ Ruxsat yo'q.")
        return
    user_states[message.from_user.id] = {"bosqich": "nom", "data": {}}
    bot.send_message(message.chat.id, "📦 Mahsulot nomini kiriting:")

@bot.message_handler(func=lambda m: m.from_user.id in user_states)
def handle_steps(message):
    uid = message.from_user.id
    state = user_states.get(uid)
    if not state:
        return
    bosqich = state["bosqich"]
    text = message.text.strip()

    if bosqich == "nom":
        state["data"]["nom"] = text
        state["bosqich"] = "egasi"
        bot.send_message(message.chat.id, "👤 Egasining ismini kiriting:")
    elif bosqich == "egasi":
        state["data"]["egasi"] = text
        state["bosqich"] = "telefon"
        bot.send_message(message.chat.id, "📞 Telefon raqamini kiriting:")
    elif bosqich == "telefon":
        state["data"]["telefon"] = text
        state["bosqich"] = "narx"
        bot.send_message(message.chat.id, "💰 Narxini kiriting (so'm):")
    elif bosqich == "narx":
        state["data"]["narx"] = text
        state["bosqich"] = None
        data = load_data()
        data["oxirgi_id"] += 1
        yangi_id = data["oxirgi_id"]
        sana = datetime.now().strftime("%d.%m.%Y %H:%M")
        mahsulot = {
            "id": yangi_id,
            "nom": state["data"]["nom"],
            "egasi": state["data"]["egasi"],
            "telefon": state["data"]["telefon"],
            "narx": state["data"]["narx"],
            "sana": sana
        }
        data["mahsulotlar"].append(mahsulot)
        save_data(data)
        del user_states[uid]
        bot.send_message(message.chat.id,
            f"✅ Mahsulot saqlandi!\n\n"
            f"🆔 ID: {yangi_id}\n"
            f"📦 Nom: {mahsulot['nom']}\n"
            f"👤 Egasi: {mahsulot['egasi']}\n"
            f"📞 Telefon: {mahsulot['telefon']}\n"
            f"💰 Narx: {mahsulot['narx']} so'm\n"
            f"📅 Sana: {mahsulot['sana']}")

@bot.message_handler(commands=["royxat"])
def royxat(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "⛔ Ruxsat yo'q.")
        return
    data = load_data()
    if not data["mahsulotlar"]:
        bot.send_message(message.chat.id, "📭 Hozircha mahsulot yo'q.")
        return
    for m in data["mahsulotlar"]:
        bot.send_message(message.chat.id,
            f"🆔 ID: {m['id']}\n"
            f"📦 {m['nom']}\n"
            f"👤 {m['egasi']}\n"
            f"📞 {m['telefon']}\n"
            f"💰 {m['narx']} so'm\n"
            f"📅 {m['sana']}")

@bot.message_handler(commands=["del"])
def delete_by_id(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        mid = int(message.text.split()[1])
        data = load_data()
        oldin = len(data["mahsulotlar"])
        data["mahsulotlar"] = [m for m in data["mahsulotlar"] if m["id"] != mid]
        if len(data["mahsulotlar"]) < oldin:
            save_data(data)
            bot.send_message(message.chat.id, f"✅ ID {mid} o'chirildi.")
        else:
            bot.send_message(message.chat.id, f"❌ ID {mid} topilmadi.")
    except:
        bot.send_message(message.chat.id, "⚠️ To'g'ri yozing: /del 3")

bot.polling()
