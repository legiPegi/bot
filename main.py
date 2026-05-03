import telebot
import json
import os
import random
import qrcode
import io
from datetime import datetime, timedelta
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))

bot = telebot.TeleBot(BOT_TOKEN)
DATA_FILE = "ishlar.json"

# ===== MA'LUMOTLAR =====
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"ishlar": [], "ishlatilgan_idlar": []}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ===== UNIKAL 4 XONALI ID =====
def yangi_id_yaratish(data):
    ishlatilgan = data.get("ishlatilgan_idlar", [])
    while True:
        yangi = random.randint(1000, 9999)
        if yangi not in ishlatilgan:
            ishlatilgan.append(yangi)
            data["ishlatilgan_idlar"] = ishlatilgan
            return yangi

# ===== QR KOD YARATISH =====
def qr_yaratish(ish):
    matn = (
        f"ID: {ish['id']}\n"
        f"Blok: {ish['blok_nomi']}\n"
        f"Mijoz: {ish['mijoz_ismi']}\n"
        f"Tel: {ish['telefon']}\n"
        f"Narx: {ish['narx']} so'm\n"
        f"Sana: {ish['sana']}\n"
        f"Holat: {ish['holat']}"
    )
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(matn)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

# ===== EXCEL HISOBOT YARATISH =====
def excel_hisobot_yaratish(ishlar, sarlavha):
    """Ishlar ro'yxatidan Excel fayl yaratish"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Hisobot"
    
    # Stil tanlovlari
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    thin_border = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin')
    )
    
    # Sarlavha qatori
    headers = ['ID', 'Blok nomi', 'Mijoz ismi', 'Telefon', 'Narx (so\'m)', 'Qabul sanasi', 'Holat', 'Yakunlangan sana']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.border = thin_border
    
    # Ma'lumotlarni to'ldirish
    row_num = 2
    for ish in ishlar:
        # Holatga qarab qator rangi
        row_fill = None
        if ish['holat'] == 'Yakunlandi':
            row_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
        elif ish['holat'] == 'Jarayonda':
            row_fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
        
        ws.cell(row=row_num, column=1, value=ish['id'])
        ws.cell(row=row_num, column=2, value=ish['blok_nomi'])
        ws.cell(row=row_num, column=3, value=ish['mijoz_ismi'])
        ws.cell(row=row_num, column=4, value=ish.get('telefon', '-'))
        ws.cell(row=row_num, column=5, value=ish['narx'])
        ws.cell(row=row_num, column=6, value=ish['sana'])
        ws.cell(row=row_num, column=7, value=ish['holat'])
        ws.cell(row=row_num, column=8, value=ish.get('yakunlangan_sana', '-'))
        
        for col in range(1, 9):
            cell = ws.cell(row=row_num, column=col)
            cell.border = thin_border
            if row_fill:
                cell.fill = row_fill
            if col == 5:
                cell.alignment = Alignment(horizontal='right')
        
        row_num += 1
    
    # Ustunlarni avtomat kengaytirish
    for col in ws.columns:
        max_length = 0
        col_letter = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 30)
        ws.column_dimensions[col_letter].width = adjusted_width
    
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output

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
    kb.add(KeyboardButton("📎 Excel yuklab olish"))
    kb.add(KeyboardButton("🔙 Orqaga"))
    return kb

user_states = {}

# ===== HISOBOT =====
def hisobot_yaratish(ishlar, sarlavha):
    if not ishlar:
        return f"📊 {sarlavha}\n\n📭 Bu davrda ish yo'q."
    jami = len(ishlar)
    yakunlangan = [i for i in ishlar if i["holat"] == "Yakunlandi"]
    jarayonda = [i for i in ishlar if i["holat"] == "Jarayonda"]
    jami_summa = 0
    for ish in ishlar:
        try:
            jami_summa += int(ish["narx"].replace(" ", "").replace(",", ""))
        except:
            pass
    yakunlangan_summa = 0
    for ish in yakunlangan:
        try:
            yakunlangan_summa += int(ish["narx"].replace(" ", "").replace(",", ""))
        except:
            pass
    return (
        f"📊 {sarlavha}\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"📦 Jami ishlar: {jami} ta\n"
        f"✅ Yakunlangan: {len(yakunlangan)} ta\n"
        f"⏳ Jarayonda: {len(jarayonda)} ta\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"💰 Jami summa: {jami_summa:,} so'm\n"
        f"✅ Yakunlangan summa: {yakunlangan_summa:,} so'm\n"
        f"━━━━━━━━━━━━━━━━"
    )

def ishlar_sanada(ishlar, bosh, oxir):
    natija = []
    for ish in ishlar:
        try:
            sana = datetime.strptime(ish["sana"], "%d.%m.%Y %H:%M")
            if bosh <= sana <= oxir:
                natija.append(ish)
        except:
            pass
    return natija

def send_excel_report(message, ishlar, sarlavha):
    """Excel faylni yuborish"""
    if not ishlar:
        bot.send_message(message.chat.id, f"📭 {sarlavha} uchun ma'lumot topilmadi.", reply_markup=hisobot_keyboard())
        return
    try:
        excel_file = excel_hisobot_yaratish(ishlar, sarlavha)
        bot.send_document(
            message.chat.id, 
            excel_file, 
            visible_file_name=f"hisobot_{sarlavha.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            caption=f"📊 {sarlavha} - {len(ishlar)} ta ish",
            reply_markup=main_keyboard()
        )
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Excel fayl yaratishda xatolik: {str(e)}", reply_markup=hisobot_keyboard())

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
    bot.send_message(message.chat.id, "🔍 Ish ID sini kiriting (4 xonali raqam):")

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

# ===== HISOBOT =====
@bot.message_handler(func=lambda m: m.text == "📊 Hisobot")
def hisobot_menu(message):
    if message.from_user.id != ADMIN_ID:
        return
    user_states[message.from_user.id] = {"bosqich": "hisobot_menu"}
    bot.send_message(message.chat.id, "📊 Hisobot turini tanlang:", reply_markup=hisobot_keyboard())

@bot.message_handler(func=lambda m: m.text == "🔙 Orqaga")
def orqaga(message):
    # Agar Excel rejimida bo'lsa, rejimni tozalash
    if message.from_user.id in user_states:
        del user_states[message.from_user.id]
    bot.send_message(message.chat.id, "🏠 Asosiy menyu:", reply_markup=main_keyboard())

# ===== EXCEL YUKLAB OLISH =====
@bot.message_handler(func=lambda m: m.text == "📎 Excel yuklab olish")
def excel_yuklab_olish(message):
    if message.from_user.id != ADMIN_ID:
        return
    user_states[message.from_user.id] = {"bosqich": "excel_hisobot", "excel_mode": True}
    bot.send_message(message.chat.id, "📊 Qaysi hisobotni Excelda yuklamoqchisiz?", reply_markup=hisobot_keyboard())

# ===== HISOBOT TUGMALARI =====
@bot.message_handler(func=lambda m: m.text == "📅 Bugungi hisobot")
def bugungi(message):
    data = load_data()
    bosh = datetime.now().replace(hour=0, minute=0, second=0)
    ishlar = ishlar_sanada(data["ishlar"], bosh, datetime.now())
    
    state = user_states.get(message.from_user.id)
    if state and state.get("excel_mode"):
        send_excel_report(message, ishlar, f"Bugungi hisobot ({datetime.now().strftime('%d.%m.%Y')})")
        del user_states[message.from_user.id]
    else:
        bot.send_message(message.chat.id, hisobot_yaratish(ishlar, f"Bugungi hisobot ({datetime.now().strftime('%d.%m.%Y')})"), reply_markup=hisobot_keyboard())

@bot.message_handler(func=lambda m: m.text == "📆 Haftalik hisobot")
def haftalik(message):
    data = load_data()
    ishlar = ishlar_sanada(data["ishlar"], datetime.now() - timedelta(days=7), datetime.now())
    
    state = user_states.get(message.from_user.id)
    if state and state.get("excel_mode"):
        send_excel_report(message, ishlar, "Haftalik hisobot (7 kun)")
        del user_states[message.from_user.id]
    else:
        bot.send_message(message.chat.id, hisobot_yaratish(ishlar, "Haftalik hisobot (7 kun)"), reply_markup=hisobot_keyboard())

@bot.message_handler(func=lambda m: m.text == "🗓 10 kunlik hisobot")
def o_nkunlik(message):
    data = load_data()
    ishlar = ishlar_sanada(data["ishlar"], datetime.now() - timedelta(days=10), datetime.now())
    
    state = user_states.get(message.from_user.id)
    if state and state.get("excel_mode"):
        send_excel_report(message, ishlar, "10 kunlik hisobot")
        del user_states[message.from_user.id]
    else:
        bot.send_message(message.chat.id, hisobot_yaratish(ishlar, "10 kunlik hisobot"), reply_markup=hisobot_keyboard())

@bot.message_handler(func=lambda m: m.text == "📝 Oylik hisobot")
def oylik(message):
    data = load_data()
    ishlar = ishlar_sanada(data["ishlar"], datetime.now() - timedelta(days=30), datetime.now())
    
    state = user_states.get(message.from_user.id)
    if state and state.get("excel_mode"):
        send_excel_report(message, ishlar, "Oylik hisobot (30 kun)")
        del user_states[message.from_user.id]
    else:
        bot.send_message(message.chat.id, hisobot_yaratish(ishlar, "Oylik hisobot (30 kun)"), reply_markup=hisobot_keyboard())

@bot.message_handler(func=lambda m: m.text == "✏️ Sana kiritish")
def sana_kiritish(message):
    state = user_states.get(message.from_user.id)
    excel_mode = state.get("excel_mode", False) if state else False
    
    user_states[message.from_user.id] = {
        "bosqich": "sana_bosh", 
        "data": {},
        "excel_mode": excel_mode
    }
    bot.send_message(message.chat.id, "📅 Boshlanish sanasini kiriting:\nFormat: 01.05.2025")

# ===== BOSQICHMA-BOSQICH =====
@bot.message_handler(func=lambda m: m.from_user.id in user_states)
def handle_steps(message):
    uid = message.from_user.id
    state = user_states.get(uid)
    if not state:
        return
    bosqich = state["bosqich"]
    text = message.text.strip()

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
                qr_buf = qr_yaratish(ish)
                bot.send_photo(message.chat.id, qr_buf, caption=f"🔲 ID {ish['id']} uchun QR kod")
            else:
                bot.send_message(message.chat.id, f"❌ ID {mid} topilmadi.", reply_markup=main_keyboard())
        except:
            bot.send_message(message.chat.id, "⚠️ Faqat raqam kiriting!", reply_markup=main_keyboard())
        del user_states[uid]

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
                        qr_buf = qr_yaratish(ish)
                        bot.send_photo(message.chat.id, qr_buf, caption=f"🔲 ID {ish['id']} — Yakunlandi ✅")
                    topildi = True
                    break
            if not topildi:
                bot.send_message(message.chat.id, f"❌ ID {mid} topilmadi.", reply_markup=main_keyboard())
        except:
            bot.send_message(message.chat.id, "⚠️ Faqat raqam kiriting!", reply_markup=main_keyboard())
        del user_states[uid]

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

    elif bosqich == "sana_bosh":
        try:
            datetime.strptime(text, "%d.%m.%Y")
            state["data"]["bosh"] = text
            state["bosqich"] = "sana_oxir"
            bot.send_message(message.chat.id, "📅 Tugash sanasini kiriting:\nFormat: 31.05.2025")
        except:
            bot.send_message(message.chat.id, "⚠️ Format xato! Masalan: 01.05.2025")

    elif bosqich == "sana_oxir":
        try:
            bosh = datetime.strptime(state["data"]["bosh"], "%d.%m.%Y")
            oxir = datetime.strptime(text, "%d.%m.%Y").replace(hour=23, minute=59)
            data = load_data()
            ishlar = ishlar_sanada(data["ishlar"], bosh, oxir)
            
            if state.get("excel_mode"):
                send_excel_report(message, ishlar, f"Hisobot: {state['data']['bosh']} — {text}")
            else:
                matn = hisobot_yaratish(ishlar, f"Hisobot: {state['data']['bosh']} — {text}")
                bot.send_message(message.chat.id, matn, reply_markup=hisobot_keyboard())
            del user_states[uid]
        except:
            bot.send_message(message.chat.id, "⚠️ Format xato! Masalan: 31.05.2025")

    elif bosqich == "blok_nomi":
        state["data"]["blok_nomi"] = text
        state["bosqich"] = "mijoz_ismi"
        bot.send_message(message.chat.id, "👤 Mijoz ismini kiriting:")

    elif bosqich == "mijoz_ismi":
        state["data"]["mijoz_ismi"] = text
        state["bosqich"] = "telefon"
        bot.send_message(message.chat.id, "📞 Mijoz telefon raqamini kiriting:")

    elif bosqich == "telefon":
        state["data"]["telefon"] = text
        state["bosqich"] = "narx"
        bot.send_message(message.chat.id, "💰 Kelishilgan narxni kiriting (so'm):")

    elif bosqich == "narx":
        state["data"]["narx"] = text
        data = load_data()
        yangi_id = yangi_id_yaratish(data)
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

        qr_buf = qr_yaratish(yangi_ish_data)
        bot.send_photo(message.chat.id, qr_buf,
            caption=f"🔲 Mijozga beriladigan QR kod\nID: {yangi_id}")

    elif bosqich == "hisobot_menu":
        # Hisobot menyusida Excel rejimini tozalash
        if "excel_mode" in state:
            del state["excel_mode"]
        # Bu yerda hech narsa qilmaymiz, chunki tugmalar bilan ishlaymiz
        pass

    elif bosqich == "excel_hisobot":
        # Excel hisobot menyusida, tugmalar bilan ishlaymiz
        pass

# ===== BOTNI ISHGA TUSHIRISH =====
if __name__ == "__main__":
    print("Bot ishga tushdi...")
    bot.infinity_polling()
