import telebot
import json
import os
from datetime import datetime, timedelta
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))

bot = telebot.TeleBot(BOT_TOKEN)
DATA_FILE = "ishlar.json"

# ===== MA'LUMOTLAR =====
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"ishlar": [], "oxirgi_id": 0}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ===== KLAVIATURA =====
def main_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("➕ Yangi ish qo'shish"))
    kb.add(KeyboardButton("📋 Barcha ishlar"), KeyboardButton("⏳ Jarayondagi ishlar"))
    kb.add(KeyboardButton("🔍 ID bo'yicha qidirish"), KeyboardButton("✅ Ishni yakunlash"))
    kb.add(KeyboardButton("📊 Hisobot"), KeyboardButton("🗑 Ishni o'chirish"))
    return kb

def hisobot_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("📅 Bugungi hisobot"))
    kb.add(KeyboardButton("📆 Haftalik hisobot"), KeyboardButton("🗓 10 kunlik hisobot"))
    kb.add(KeyboardButton("📝 Oylik hisobot"), KeyboardButton("✏️ Sana kiritish"))
    kb.add(KeyboardButton("🔙 Orqaga"))
    return kb

user_states = {}

# ===== HISOBOT YARATISH =====
def hisobot_yaratish(ishlar, sarlavha):
    if not ishlar:
        return f"📊 {sarlavha}\n\n📭 Bu davrda ish yo'q."

    jami = len(ishlar)
    yakunlangan = [i for i in ishlar if i["holat"] == "Yakunlandi"]
    jarayonda = [i for i in ishlar if i["holat"] == "Jarayonda"]

    jami_summa = 0
    for ish in ishlar:
        try:
            narx = ish["narx"].replace(" ", "").replace(",", "")
            jami_summa += int(narx)
        except:
            pass

    yakunlangan_summa = 0
    for ish in yakunlangan:
        try:
            narx = ish["narx"].replace(" ", "").replace(",", "")
            yakunlangan_summa += int(narx)
        except:
            pass

    matn = (
        f"📊 {sarlavha}\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"📦 Jami ishlar: {jami} ta\n"
        f"✅ Yakunlangan: {len(yakunlangan)} ta\n"
        f"⏳ Jarayonda: {len(jarayonda)} ta\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"💰 Jami summa: {jami_summa:,} so'm\n"
        f"✅ Yakunlangan summa: {yakunlangan_summa:,} so'm\n"
        f"━━━━━━━━━━━━━━━━\n"
    )
    return matn

def ishlar_sanada(ishlar, bosh_sana, oxir_sana):
    natija = []
    for ish in ishlar:
        try:
            sana = datetime.strptime(ish["sana"], "%d.%m.%Y %H:%M")
            if bosh_sana <= sana <= oxir_sana:
                natija.append(ish)
        except:
            pass
    return natija

# ===== /start =====
@bot.message_handler(commands=["start"])
def start(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id,
            "👋 Xush kelibsiz!\n\n"
            "🔧 Mator blok shilish xizmati\n"
            "Quyidagi tugmalardan foydalaning:",
            reply_markup=main_keyboard())
    else:
        bot.send_message(message.chat.id, "⛔ Siz admin emassiz.")

# ===== YANGI ISH =====
@bot.message_handler(func=lambda m: m.text == "➕ Yangi ish qo'shish")
def yangi_ish(message):
    if message.from_user.id != ADMIN_ID:
        return
    user_states[message.from_user.id] = {"bosqich": "blok_nomi", "data": {}}
    bot.send_message(message.chat.id, "🔧 Blok nomini kiriting:\n(masalan: Toyota Camry 2.4)")

# ===== BARCHA ISHLAR =====
@bot.message_handler(func=lambda m: m.text == "📋 Barcha ishlar")
def barcha_ishlar(message):
    if message.from_user.id != ADMIN_ID:
        return
    data = load_data()
    if not data["ishlar"]:
        bot.send_message(message.chat.id, "📭 Hozircha ish yo'q.", reply_markup=main_keyboard())
        return
    bot.send_message(message.chat.id, f"📋 Jami: {len(data['ishlar'])} ta ish")
    for ish in data["ishlar"]:
        holat_emoji = "✅" if ish["holat"] == "Yakunlandi" else "⏳"
        bot.send_message(message.chat.id,
            f"🆔 ID: {ish['id']}\n"
            f"🔧 Blok: {ish['blok_nomi']}\n"
            f"👤 Mijoz: {ish['mijoz_ismi']}\n"
            f"📞 Tel: {ish.get('telefon', '-')}\n"
            f"💰 Narx: {ish['narx']} so'm\n"
            f"📅 Sana: {ish['sana']}\n"
            f"{holat_emoji} Holat: {ish['holat']}")

# ===== JARAYONDAGI ISHLAR =====
@bot.message_handler(func=lambda m: m.text == "⏳ Jarayondagi ishlar")
def jarayondagi_ishlar(message):
    if message.from_user.id != ADMIN_ID:
        return
    data = load_data()
    jarayon = [i for i in data["ishlar"] if i["holat"] == "Jarayonda"]
    if not jarayon:
        bot.send_message(message.chat.id, "✅ Jarayondagi ish yo'q.", reply_markup=main_keyboard())
        return
    bot.send_message(message.chat.id, f"⏳ Jarayondagi ishlar: {len(jarayon)} ta")
    for ish in jarayon:
        bot.send_message(message.chat.id,
            f"🆔 ID: {ish['id']}\n"
            f"🔧 Blok: {ish['blok_nomi']}\n"
            f"👤 Mijoz: {ish['mijoz_ismi']}\n"
            f"📞 Tel: {ish.get('telefon', '-')}\n"
            f"💰 Narx: {ish['narx']} so'm\n"
            f"📅 Sana: {ish['sana']}\n"
            f"⏳ Holat: Jarayonda")

# ===== ID BO'YICHA QIDIRISH =====
@bot.message_handler(func=lambda m: m.text == "🔍 ID bo'yicha qidirish")
def qidirish_boshlash(message):
    if message.from_user.id != ADMIN_ID:
        return
    user_states[message.from_user.id] = {"bosqich": "qidirish"}
    bot.send_message(message.chat.id, "🔍 Ish ID sini kiriting:")

# ===== ISHNI YAKUNLASH =====
@bot.message_handler(func=lambda m: m.text == "✅ Ishni yakunlash")
def yakunlash_boshlash(message):
    if message.from_user.id != ADMIN_ID:
        return
    user_states[message.from_user.id] = {"bosqich": "yakunlash"}
    bot.send_message(message.chat.id, "✅ Yakunlanmoqchi bo'lgan ish ID sini kiriting:")

# ===== ISHNI O'CHIRISH =====
@bot.message_handler(func=lambda m: m.text == "🗑 Ishni o'chirish")
def ochirish_boshlash(message):
    if message.from_user.id != ADMIN_ID:
        return
    user_states[message.from_user.id] = {"bosqich": "ochirish"}
    bot.send_message(message.chat.id, "🗑 O'chirmoqchi bo'lgan ish ID sini kiriting:")

# ===== HISOBOT MENYUSI =====
@bot.message_handler(func=lambda m: m.text == "📊 Hisobot")
def hisobot_menu(message):
    if message.from_user.id != ADMIN_ID:
        return
    bot.send_message(message.chat.id, "📊 Hisobot turini tanlang:", reply_markup=hisobot_keyboard())

@bot.message_handler(func=lambda m: m.text == "🔙 Orqaga")
def orqaga(message):
    bot.send_message(message.chat.id, "🏠 Asosiy menyu:", reply_markup=main_keyboard())

@bot.message_handler(func=lambda m: m.text == "📅 Bugungi hisobot")
def bugungi_hisobot(message):
    if message.from_user.id != ADMIN_ID:
        return
    data = load_data()
    bugun = datetime.now().replace(hour=0, minute=0, second=0)
    oxir = datetime.now()
    ishlar = ishlar_sanada(data["ishlar"], bugun, oxir)
    matn = hisobot_yaratish(ishlar, f"Bugungi hisobot ({datetime.now().strftime('%d.%m.%Y')})")
    bot.send_message(message.chat.id, matn, reply_markup=hisobot_keyboard())

@bot.message_handler(func=lambda m: m.text == "📆 Haftalik hisobot")
def haftalik_hisobot(message):
    if message.from_user.id != ADMIN_ID:
        return
    data = load_data()
    oxir = datetime.now()
    bosh = oxir - timedelta(days=7)
    ishlar = ishlar_sanada(data["ishlar"], bosh, oxir)
    matn = hisobot_yaratish(ishlar, f"Haftalik hisobot (oxirgi 7 kun)")
    bot.send_message(message.chat.id, matn, reply_markup=hisobot_keyboard())

@bot.message_handler(func=lambda m: m.text == "🗓 10 kunlik hisobot")
def o_nkunlik_hisobot(message):
    if message.from_user.id != ADMIN_ID:
        return
    data = load_data()
    oxir = datetime.now()
    bosh = oxir - timedelta(days=10)
    ishlar = ishlar_sanada(data["ishlar"], bosh, oxir)
    matn = hisobot_yaratish(ishlar, f"10 kunlik hisobot")
    bot.send_message(message.chat.id, matn, reply_markup=hisobot_keyboard())

@bot.message_handler(func=lambda m: m.text == "📝 Oylik hisobot")
def oylik_hisobot(message):
    if message.from_user.id != ADMIN_ID:
        return
    data = load_data()
    oxir = datetime.now()
    bosh = oxir - timedelta(days=30)
    ishlar = ishlar_sanada(data["ishlar"], bosh, oxir)
    matn = hisobot_yaratish(ishlar, f"Oylik hisobot (oxirgi 30 kun)")
    bot.send_message(message.chat.id, matn, reply_markup=hisobot_keyboard())

@bot.message_handler(func=lambda m: m.text == "✏️ Sana kiritish")
def sana_kiritish(message):
    if message.from_user.id != ADMIN_ID:
        return
    user_states[message.from_user.id] = {"bosqich": "sana_bosh"}
    bot.send_message(message.chat.id,
        "📅 Boshlanish sanasini kiriting:\n"
        "Format: 01.05.2025")

# ===== BOSQICHMA-BOSQICH =====
@bot.message_handler(func=lambda m: m.from_user.id in user_states)
def handle_steps(message):
    uid = message.from_user.id
    state = user_states.get(uid)
    if not state:
        return
    bosqich = state["bosqich"]
    text = message.text.strip()

    # QIDIRISH
    if bosqich == "qidirish":
        try:
            mid = int(text)
            data = load_data()
            ish = next((i for i in data["ishlar"] if i["id"] == mid), None)
            if ish:
                holat_emoji = "✅" if ish["holat"] == "Yakunlandi" else "⏳"
                bot.send_message(message.chat.id,
                    f"✅ Topildi!\n\n"
                    f"🆔 ID: {ish['id']}\n"
                    f"🔧 Blok: {ish['blok_nomi']}\n"
                    f"👤 Mijoz: {ish['mijoz_ismi']}\n"
                    f"📞 Tel: {ish.get('telefon', '-')}\n"
                    f"💰 Narx: {ish['narx']} so'm\n"
                    f"📅 Sana: {ish['sana']}\n"
                    f"{holat_emoji} Holat: {ish['holat']}",
                    reply_markup=main_keyboard())
            else:
                bot.send_message(message.chat.id, f"❌ ID {mid} topilmadi.", reply_markup=main_keyboard())
        except:
            bot.send_message(message.chat.id, "⚠️ Faqat raqam kiriting!", reply_markup=main_keyboard())
        del user_states[uid]

    # YAKUNLASH
    elif bosqich == "yakunlash":
        try:
            mid = int(text)
            data = load_data()
            topildi = False
            for ish in data["ishlar"]:
                if ish["id"] == mid:
                    if ish["holat"] == "Yakunlandi":
                        bot.send_message(message.chat.id, f"ℹ️ ID {mid} allaqachon yakunlangan.", reply_markup=main_keyboard())
                    else:
                        ish["holat"] = "Yakunlandi"
                        ish["yakunlangan_sana"] = datetime.now().strftime("%d.%m.%Y %H:%M")
                        save_data(data)
                        bot.send_message(message.chat.id,
                            f"✅ Ish yakunlandi!\n\n"
                            f"🆔 ID: {ish['id']}\n"
                            f"🔧 Blok: {ish['blok_nomi']}\n"
                            f"👤 Mijoz: {ish['mijoz_ismi']}\n"
                            f"📞 Tel: {ish.get('telefon', '-')}\n"
                            f"💰 Narx: {ish['narx']} so'm\n"
                            f"📅 Qabul: {ish['sana']}\n"
                            f"✅ Yakunlandi: {ish['yakunlangan_sana']}",
                            reply_markup=main_keyboard())
                    topildi = True
                    break
            if not topildi:
                bot.send_message(message.chat.id, f"❌ ID {mid} topilmadi.", reply_markup=main_keyboard())
        except:
            bot.send_message(message.chat.id, "⚠️ Faqat raqam kiriting!", reply_markup=main_keyboard())
        del user_states[uid]

    # O'CHIRISH
    elif bosqich == "ochirish":
        try:
            mid = int(text)
            data = load_data()
            oldin = len(data["ishlar"])
            data["ishlar"] = [i for i in data["ishlar"] if i["id"] != mid]
            if len(data["ishlar"]) < oldin:
                save_data(data)
                bot.send_message(message.chat.id, f"✅ ID {mid} o'chirildi.", reply_markup=main_keyboard())
            else:
                bot.send_message(message.chat.id, f"❌ ID {mid} topilmadi.", reply_markup=main_keyboard())
        except:
            bot.send_message(message.chat.id, "⚠️ Faqat raqam kiriting!", reply_markup=main_keyboard())
        del user_states[uid]

    # SANA KIRITISH - BOSH
    elif bosqich == "sana_bosh":
        try:
            datetime.strptime(text, "%d.%m.%Y")
            state["data"]["bosh"] = text
            state["bosqich"] = "sana_oxir"
            bot.send_message(message.chat.id,
                "📅 Tugash sanasini kiriting:\n"
                "Format: 31.05.2025")
        except:
            bot.send_message(message.chat.id, "⚠️ Format xato! Masalan: 01.05.2025")

    # SANA KIRITISH - OXIR
    elif bosqich == "sana_oxir":
        try:
            bosh = datetime.strptime(state["data"]["bosh"], "%d.%m.%Y")
            oxir = datetime.strptime(text, "%d.%m.%Y").replace(hour=23, minute=59)
            data = load_data()
            ishlar = ishlar_sanada(data["ishlar"], bosh, oxir)
            sarlavha = f"Hisobot: {state['data']['bosh']} — {text}"
            matn = hisobot_yaratish(ishlar, sarlavha)
            bot.send_message(message.chat.id, matn, reply_markup=hisobot_keyboard())
            del user_states[uid]
        except:
            bot.send_message(message.chat.id, "⚠️ Format xato! Masalan: 31.05.2025")

    # YANGI ISH - BLOK NOMI
    elif bosqich == "blok_nomi":
        state["data"]["blok_nomi"] = text
        state["bosqich"] = "mijoz_ismi"
        bot.send_message(message.chat.id, "👤 Mijoz ismini kiriting:")

    # YANGI ISH - MIJOZ ISMI
    elif bosqich == "mijoz_ismi":
        state["data"]["mijoz_ismi"] = text
        state["bosqich"] = "telefon"
        bot.send_message(message.chat.id, "📞 Mijoz telefon raqamini kiriting:")

    # YANGI ISH - TELEFON
    elif bosqich == "telefon":
        state["data"]["telefon"] = text
        state["bosqich"] = "narx"
        bot.send_message(message.chat.id, "💰 Kelishilgan narxni kiriting (so'm):")

    # YANGI ISH - NARX
    elif bosqich == "narx":
        state["data"]["narx"] = text
        data = load_data()
        data["oxirgi_id"] += 1
        yangi_id = data["oxirgi_id"]
        sana = datetime.now().strftime("%d.%m.%Y %H:%M")

        yangi_ish_data = {
            "id": yangi_id,
            "blok_nomi": state["data"]["blok_nomi"],
            "mijoz_ismi": state["data"]["mijoz_ismi"],
            "telefon": state["data"]["telefon"],
            "narx": state["data"]["narx"],
            "sana": sana,
            "holat": "Jarayonda",
            "yakunlangan_sana": ""
        }
        data["ishlar"].append(yangi_ish_data)
        save_data(data)
        del user_states[uid]

        bot.send_message(message.chat.id,
            f"✅ Ish qo'shildi!\n\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"🆔 ID: {yangi_id}\n"
            f"🔧 Blok: {yangi_ish_data['blok_nomi']}\n"
            f"👤 Mijoz: {yangi_ish_data['mijoz_ismi']}\n"
            f"📞 Tel: {yangi_ish_data['telefon']}\n"
            f"💰 Narx: {yangi_ish_data['narx']} so'm\n"
            f"📅 Sana: {yangi_ish_data['sana']}\n"
            f"⏳ Holat: Jarayonda\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📌 Mijozga bering: ID {yangi_id}",
            reply_markup=main_keyboard())

bot.polling()
