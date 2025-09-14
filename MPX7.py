"""
Telegram Feedback Bot - Clean Structure
Author: @patelmilan07 / @_patelmilan07
Date: 2025-06-20
"""

import os
import json
import logging
from typing import Dict, Set, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
)
import uuid
import random
import pathlib
import time
import platform
import subprocess

# -------------------- CONFIGURATION --------------------
TOKEN = "7604799948:AAGk93peT_ABcefBOKdp4gtKuHw4E2XnI-U"
ADMIN_IDS = {"5524867269", "7306222826", "7421957337"}
FILE_DB = "files_db.json"
FILES_DB = "files.json"
USERS_DB = "users.json"
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB

# -------------------- GLOBAL STATE --------------------
banned_users: Set[str] = set()
user_lang: Dict[str, str] = {}
forward_map: Dict[int, int] = {}
admin_upload_flags = set()

# -------------------- LOGGER --------------------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# -------------------- LANGUAGE DATA --------------------
LANGUAGES = {
    "hindi": {
        "welcome": "🚨 ᴰᵃʳᵏᴹᵃᵗʳᶦˣ™ - Feedback/File Bot [STRICT MODE ENABLED]",
        "full_welcome": (
            "🚨 ᴰᵃʳᵏᴹᵃᵗʳᶦˣ™ - फीडबैक/फाइल बोट [सख्त मोड सक्रिय]\n\n"
            "🛰️ मुख्य बेस: @bumchick78hh\n"
            "💬 वार रूम (चैट): @xxxxxxxxxxxxxxxxxxxxxxxxxxxccx\n"
            "👁️‍🗨️ कोड मास्टर: @DarkMatrix_Official\n"
            "📡 प्रूफ अपलोड यूनिट: @MPXV1_bot\n\n"
            "---\n\n"
            "🛑 चेतावनी (पढ़ो या निकलो):\n\n"
            "❌ बिना स्क्रीनशॉट = कोई फाइल नहीं\n"
            "❌ बिना फीडबैक = कोई मेथड नहीं\n"
            "💀 कोई अपवाद नहीं। कोई दया नहीं।\n\n"
            "🚀 फ्री नेट चाहिए? तो मेहनत करो।\n"
            "📸 प्रूफ भेजो, फीडबैक दो — तभी दरवाजे खुलेंगे।\n\n"
            "⚡ यह तुम्हारा खेल का मैदान नहीं है। यह 𝐂.𝐀.𝐅.𝐈 𝐍𝐇𝐞𝐭𝐰𝐨𝐫𝐦™ है।"
        ),
        "user": "👤 यूजर डैशबोर्ड\n\n🆔 ID: {user_id}\n🌐 भाषा: {lang}\n🚫 बैन: {banned}\n👥 कुल यूजर: {total}",
        "banned": "🚫 आप प्रतिबंधित हैं। कोई क्रिया नहीं।",
        "language_set": "✅ भाषा सेट हो गई है!\n\n{message}",
        "unauthorized": "❌ आप अधिकृत नहीं हैं।",
        "ban_success": "🚫 यूजर {user_id} को बैन किया गया।",
        "unban_success": "✅ यूजर {user_id} का बैन हटाया गया।",
        "broadcast_result": "📢 संदेश {count} यूजर्स को भेजा गया, {failed} असफल रहे।",
        "admin_reply_prefix": "💬 एडमिन का जवाब:\n\n",
        "reply_success": "✅ संदेश सफलतापूर्वक भेजा गया!",
        "reply_failed": "❌ संदेश भेजने में विफल।",
        "invalid_format": "⚠️ फॉर्मेट सपोर्ट नहीं है।",
        "user_not_found": "⚠️ मूल यूजर नहीं मिला।",
        "reply_instructions": "❌ कृपया यूजर के संदेश पर रिप्लाई करें।",
        "commands": (
            "📚 उपलब्ध कमांड्स:\n\n"
            "🚀 /start - बोट शुरू करें\n"
            "👤 /user - अपनी जानकारी देखें\n"
            "🌐 /language - भाषा बदलें\n"
            "📝 /feedback - फीडबैक भेजें\n"
            "❓ /help - मदद देखें\n\n"
            "🔨 एडमिन कमांड्स:\n"
            "🚫 /ban <user_id> - यूजर को बैन करें\n"
            "✅ /unban <user_id> - यूजर का बैन हटाएं\n"
            "📢 /broadcast - सभी को संदेश भेजें\n"
            "📜 /commands - सभी कमांड्स देखें"
        ),
        "help": (
            "🆘 मदद केंद्र\n\n"
            "1. फीडबैक भेजने के लिए सीधे संदेश लिखें या मीडिया भेजें\n"
            "2. भाषा बदलने के लिए /language कमांड का उपयोग करें\n"
            "3. अपनी जानकारी देखने के लिए /user कमांड का उपयोग करें\n\n"
            "समस्याएं? @DarkMatrix_Official से संपर्क करें"
        )
    },
    "english": {
        "welcome": "🚨 ᴰᵃʳᵏᴹᵃᵗʳᶦˣ™ - Feedback/File Bot [STRICT MODE ENABLED]",
        "full_welcome": (
            "🚨 ᴰᵃʳᵏᴹᵃᵗʳᶦˣ™ - Feedback/File Bot [STRICT MODE ENABLED]\n\n"
            "🛰️ Main Base: @bumchick78hh\n"
            "💬 War Room (Chat): @xxxxxxxxxxxxxxxxxxxxxxxxxxxccx\n"
            "👁️‍🗨️ Code Master: @DarkMatrix_Official\n"
            "📡 Proof Upload Unit: @MPXV1_bot\n\n"
            "---\n\n"
            "🛑 WARNING (Read or Get Lost):\n\n"
            "❌ No Screenshot = No Files\n"
            "❌ No Feedback = No Method\n"
            "💀 No Exceptions. No Mercy.\n\n"
            "🚀 You want Free Net? You EARN it.\n"
            "📸 Drop proof, leave feedback — then and only then will the gates open.\n\n"
            "⚡ This isn’t your playground. This is ᴰᵃʳᵏᴹᵃᵗʳᶦˣ™."
        ),
        "user": "👤 User Dashboard\n\n🆔 ID: {user_id}\n🌐 Language: {lang}\n🚫 Banned: {banned}\n👥 Total Users: {total}",
        "banned": "🚫 You are banned. No actions allowed.",
        "language_set": "✅ Language set!\n\n{message}",
        "unauthorized": "❌ Unauthorized.",
        "ban_success": "🚫 User {user_id} banned.",
        "unban_success": "✅ User {user_id} unbanned.",
        "broadcast_result": "📢 Message sent to {count} users, {failed} failed.",
        "admin_reply_prefix": "💬 Admin reply:\n\n",
        "reply_success": "✅ Message sent successfully!",
        "reply_failed": "❌ Failed to send message.",
        "invalid_format": "⚠️ Format not supported.",
        "user_not_found": "⚠️ Original user not found.",
        "reply_instructions": "❌ Please reply to user's message.",
        "commands": (
            "📚 Available Commands:\n\n"
            "🚀 /start - Start the bot\n"
            "👤 /user - Show your info\n"
            "🌐 /language - Change language\n"
            "📝 /feedback - Send feedback\n"
            "❓ /help - Show help\n\n"
            "🔨 Admin Commands:\n"
            "🚫 /ban <user_id> - Ban a user\n"
            "✅ /unban <user_id> - Unban a user\n"
            "📢 /broadcast - Broadcast message\n"
            "📜 /commands - Show all commands"
        ),
        "help": (
            "🆘 Help Center\n\n"
            "1. To send feedback, just type your message or send media\n"
            "2. Use /language command to change language\n"
            "3. Use /user command to see your info\n\n"
            "Problems? Contact @DarkMatrix_Official"
        )
    },
    "gujarati": {
        "welcome": "🚨 ᴰᵃʳᵏᴹᵃᵗʳᶦˣ™ - Feedback/File Bot [STRICT MODE ENABLED]",
        "full_welcome": (
            "🚨 ᴰᵃʳᵏᴹᵃᵗʳᶦˣ™ - ફીડબેક/ફાઇલ બોટ [કડક મોડ ચાલુ]\n\n"
            "🛰️ મુખ્ય બેઝ: @bumchick78hh\n"
            "💬 વોર રૂમ (ચેટ): @xxxxxxxxxxxxxxxxxxxxxxxxxxxccx\n"
            "👁️‍🗨️ કોડ માસ્ટર: @DarkMatrix_Official\n"
            "📡 પુરાવા અપલોડ યુનિટ: @MPXV1_bot\n\n"
            "---\n\n"
            "🛑 ચેતવણી (વાંચો અથવા નીકળી જાઓ):\n\n"
            "❌ સ્ક્રીનશોટ વગર = કોઈ ફાઇલ નહીં\n"
            "❌ ફીડબેક વગર = કોઈ રીત નહીં\n"
            "💀 કોઈ અપવાદ નહીં. કોઈ દયા નહીં.\n\n"
            "🚀 ફ્રી નેટ જોઈએ છે? તો કમાવવું પડશે.\n"
            "📸 પુરાવો મોકલો, ફીડબેક આપો — પછી જ દરવાજા ખુલશે.\n\n"
            "⚡ આ તમારું રમવાનું મેદાન નથી. આ છે ᴰᵃʳᵏᴹᵃᵗʳᶦˣ™."
        ),
        "user": "👤 વપરાશકર્તા ડેશબોર્ડ\n\n🆔 ID: {user_id}\n🌐 ભાષા: {lang}\n🚫 પ્રતિબંધિત: {banned}\n👥 કુલ વપરાશકર્તાઓ: {total}",
        "banned": "🚫 તમે પ્રતિબંધિત છો. કોઈપણ ક્રિયા કરવાની મંજૂરી નથી.",
        "language_set": "✅ ભાષા સેટ કરવામાં આવી છે!\n\n{message}",
        "unauthorized": "❌ અધિકૃત નથી.",
        "ban_success": "🚫 વપરાશકર્તા {user_id} પ્રતિબંધિત થયો છે.",
        "unban_success": "✅ વપરાશકર્તા {user_id} નો પ્રતિબંધ હટાવવામાં આવ્યો છે.",
        "broadcast_result": "📢 સંદેશા {count} વપરાશકર્તાઓને મોકલવામાં આવ્યો, {failed} નિષ્ફળ રહ્યો.",
        "admin_reply_prefix": "💬 પ્રશાસકની પ્રતિસાદ:\n\n",
        "reply_success": "✅ સંદેશો સફળતાપૂર્વક મોકલવામાં આવ્યો!",
        "reply_failed": "❌ સંદેશો મોકલવામાં નિષ્ફળ.",
        "invalid_format": "⚠️ ફોર્મેટને સપોર્ટ નથી કરતું.",
        "user_not_found": "⚠️ મૂળ વપરાશકર્તા મળ્યો નથી.",
        "reply_instructions": "❌ કૃપા કરીને વપરાશકર્તાના સંદેશા પર જવાબ આપો.",
        "commands": (
            "📚 ઉપલબ્ધ આદેશો:\n\n"
            "🚀 /start - બોટ શરૂ કરો\n"
            "👤 /user - તમારી માહિતી બતાવો\n"
            "🌐 /language - ભાષા બદલો\n"
            "📝 /feedback - પ્રતિસાદ મોકલો\n"
            "❓ /help - મદદ જુઓ\n\n"
            "🔨 પ્રશાસક આદેશો:\n"
            "🚫 /ban <user_id> - વપરાશકર્તાને પ્રતિબંધિત કરો\n"
            "✅ /unban <user_id> - વપરાશકર્તાની પ્રતિબંધ હટાવો\n"
            "📢 /broadcast - સંદેશા પ્રસારિત કરો\n"
            "📜 /commands - તમામ આદેશો જુઓ"
        ),
        "help": (
            "🆘 મદદ કેન્દ્ર\n\n"
            "1. પ્રતિસાદ મોકલવા માટે, ફક્ત તમારું સંદેશા ટાઇપ કરો અથવા મીડિયા મોકલો\n"
            "2. ભાષા બદલવા માટે /language આદેશનો ઉપયોગ કરો\n"
            "3. તમારી માહિતી જોવા માટે /user આદેશનો ઉપયોગ કરો\n\n"
            "સમસ્યાઓ? @DarkMatrix_Official સાથે સંપર્ક કરો"
        )
    },
    "urdu": {
        "welcome": "🚨 ᴰᵃʳᵏᴹᵃᵗʳᶦˣ™ - فیڈبیک/فائل بوٹ [سخت موڈ فعال]",
        "full_welcome": (
            "🚨 ᴰᵃʳᵏᴹᵃᵗʳᶦˣ™ - فیڈبیک/فائل بوٹ [سخت موڈ فعال]\n\n"
            "🛰️ مرکزی بیس: @bumchick78hh\n"
            "💬 وار روم (چیٹ): @xxxxxxxxxxxxxxxxxxxxxxxxxxxccx\n"
            "👁️‍🗨️ کوڈ ماسٹر: @DarkMatrix_Official\n"
            "📡 ثبوت اپلوڈ یونٹ: @MPXV1_bot\n\n"
            "---\n\n"
            "🛑 وارننگ (پڑھیں یا نکل جائیں):\n\n"
            "❌ بغیر اسکرین شاٹ = کوئی فائل نہیں\n"
            "❌ بغیر فیڈبیک = کوئی طریقہ نہیں\n"
            "💀 کوئی استثنا نہیں۔ کوئی رحم نہیں۔\n\n"
            "🚀 مفت نیٹ چاہیے؟ تو محنت کرو۔\n"
            "📸 ثبوت بھیجیں، فیڈبیک دیں — تبھی دروازے کھلیں گے۔\n\n"
            "⚡ یہ آپ کا کھیل کا میدان نہیں ہے۔ یہ ہے ᴰᵃʳᵏᴹᵃᵗʳᶦˣ™."
        ),
        "user": "👤 یوزر ڈیش بورڈ\n\n🆔 ID: {user_id}\n🌐 زبان: {lang}\n🚫 بین: {banned}\n👥 کل یوزرز: {total}",
        "banned": "🚫 آپ بین ہیں۔ کوئی عمل کی اجازت نہیں۔",
        "language_set": "✅ زبان سیٹ ہو گئی ہے!\n\n{message}",
        "unauthorized": "❌ غیر مجاز۔",
        "ban_success": "🚫 یوزر {user_id} کو بین کر دیا گیا۔",
        "unban_success": "✅ یوزر {user_id} کا بین ہٹا دیا گیا۔",
        "broadcast_result": "📢 پیغام {count} یوزرز کو بھیجا گیا، {failed} ناکام رہے۔",
        "admin_reply_prefix": "💬 ایڈمن کا جواب:\n\n",
        "reply_success": "✅ پیغام کامیابی سے بھیج دیا گیا!",
        "reply_failed": "❌ پیغام بھیجنے میں ناکام۔",
        "invalid_format": "⚠️ فارمیٹ سپورٹ نہیں ہے۔",
        "user_not_found": "⚠️ اصل یوزر نہیں ملا۔",
        "reply_instructions": "❌ براہ کرم یوزر کے پیغام پر ریپلائی کریں۔",
        "commands": (
            "📚 دستیاب کمانڈز:\n\n"
            "🚀 /start - بوٹ شروع کریں\n"
            "👤 /user - اپنی معلومات دیکھیں\n"
            "🌐 /language - زبان تبدیل کریں\n"
            "📝 /feedback - فیڈبیک بھیجیں\n"
            "❓ /help - مدد دیکھیں\n\n"
            "🔨 ایڈمن کمانڈز:\n"
            "🚫 /ban <user_id> - یوزر کو بین کریں\n"
            "✅ /unban <user_id> - یوزر کا بین ہٹائیں\n"
            "📢 /broadcast - سب کو پیغام بھیجیں\n"
            "📜 /commands - تمام کمانڈز دیکھیں"
        ),
        "help": (
            "🆘 مدد مرکز\n\n"
            "1. فیڈبیک بھیجنے کے لیے سیدھا پیغام لکھیں یا میڈیا بھیجیں\n"
            "2. زبان تبدیل کرنے کے لیے /language کمانڈ استعمال کریں\n"
            "3. اپنی معلومات دیکھنے کے لیے /user کمانڈ استعمال کریں\n\n"
            "مسائل؟ @DarkMatrix_Official سے رابطہ کریں"
        )
    },
}

# Supported languages for selection (code, label, emoji)
LANG_CHOICES = [
    ("hindi", "🇮🇳 Hindi"),
    ("gujarati", "🇮🇳 Gujarati"),
    ("english", "🇺🇸 English"),
    ("urdu", "🇵🇰 Urdu"),
]

# -------------------- UTILITY FUNCTIONS --------------------
def get_user_language(user_id: str) -> str:
    """Get user's preferred language, default to English if not set."""
    return user_lang.get(user_id, "english")

def get_message(user_id: str, key: str, **kwargs: Any) -> str:
    """Get localized message for user."""
    lang = get_user_language(user_id)
    return LANGUAGES.get(lang, LANGUAGES["english"]).get(key, "").format(**kwargs)

def is_admin(user_id: str) -> bool:
    """Check if user is admin."""
    return user_id in ADMIN_IDS

def is_banned(user_id: str) -> bool:
    """Check if user is banned."""
    return user_id in banned_users

# -------------------- FILE DB UTILS --------------------
def ensure_file_db():
    if not os.path.exists(FILE_DB):
        with open(FILE_DB, "w") as f:
            json.dump({}, f)

def save_file(file_id, file_info):
    ensure_file_db()
    with open(FILE_DB, "r") as f:
        data = json.load(f)
    data[file_id] = file_info
    with open(FILE_DB, "w") as f:
        json.dump(data, f)

def get_file_info(file_id):
    ensure_file_db()
    with open(FILE_DB, "r") as f:
        data = json.load(f)
    return data.get(file_id)

# -------------------- FILE UPLOAD UTILS --------------------
# Ensure files.json exists
if not os.path.exists(FILES_DB):
    with open(FILES_DB, "w") as f:
        json.dump({}, f)

def save_uploaded_file(unique_id, file_info):
    with open(FILES_DB, "r") as f:
        data = json.load(f)
    data[unique_id] = file_info
    with open(FILES_DB, "w") as f:
        json.dump(data, f)

def get_uploaded_file(unique_id):
    with open(FILES_DB, "r") as f:
        data = json.load(f)
    return data.get(unique_id)

# -------------------- USER REGISTRATION & STATS --------------------
def ensure_users_db():
    if not os.path.exists(USERS_DB):
        with open(USERS_DB, "w") as f:
            json.dump({}, f)

def save_user_info(user_id, lang):
    try:
        if os.path.exists(USERS_DB):
            with open(USERS_DB, "r") as f:
                data = json.load(f)
        else:
            data = {}
        data[user_id] = {
            "user_id": user_id,
            "language": lang,
            "registered": int(time.time())
        }
        with open(USERS_DB, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving user info: {e}")

def register_user(user_id: str, lang: str = "english"):
    """Register a new user if not already registered."""
    if user_id not in user_lang:
        user_lang[user_id] = lang
        save_user_info(user_id, lang)
        logger.info(f"Registered new user: {user_id} with lang: {lang}")

def get_total_users() -> int:
    return len(user_lang)

def get_banned_users() -> list:
    return list(banned_users)

def get_stats() -> dict:
    return {
        "total_users": get_total_users(),
        "banned_users": len(banned_users),
        "languages": {lang: list(user_lang.values()).count(lang) for lang in LANGUAGES.keys()}
    }

# -------------------- ADMIN: BAN, UNBAN, BROADCAST --------------------
async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    admin_id = str(update.effective_user.id)
    if not is_admin(admin_id):
        await update.message.reply_text(get_message(admin_id, "unauthorized"))
        return
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /ban <user_id>")
        return
    user_id = context.args[0]
    banned_users.add(user_id)
    await update.message.reply_text(get_message(admin_id, "ban_success", user_id=user_id))

async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    admin_id = str(update.effective_user.id)
    if not is_admin(admin_id):
        await update.message.reply_text(get_message(admin_id, "unauthorized"))
        return
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /unban <user_id>")
        return
    user_id = context.args[0]
    banned_users.discard(user_id)
    await update.message.reply_text(get_message(admin_id, "unban_success", user_id=user_id))

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    admin_id = str(update.effective_user.id)
    if not is_admin(admin_id):
        await update.message.reply_text(get_message(admin_id, "unauthorized"))
        return
    if not update.message.reply_to_message and not context.args:
        await update.message.reply_text("⚠️ Usage: Reply to a message or type /broadcast <message>")
        return
    msg = update.message.reply_to_message if update.message.reply_to_message else update.message
    msg_text = " ".join(context.args) if context.args else None
    count = 0
    failed = 0
    for uid in list(user_lang.keys()):
        try:
            if update.message.reply_to_message:
                await context.bot.copy_message(chat_id=int(uid), from_chat_id=update.message.chat_id, message_id=msg.message_id)
            else:
                await context.bot.send_message(chat_id=int(uid), text=msg_text)
            count += 1
        except Exception as e:
            failed += 1
            logger.warning(f"Broadcast to {uid} failed: {e}")
    await update.message.reply_text(get_message(admin_id, "broadcast_result", count=count, failed=failed))

# -------------------- ADMIN: STATS & BANLIST --------------------
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    admin_id = str(update.effective_user.id)
    if not is_admin(admin_id):
        await update.message.reply_text(get_message(admin_id, "unauthorized"))
        return
    stats = get_stats()
    msg = (
        f"📊 <b>Bot Stats</b>\n"
        f"👥 Total Users: <b>{stats['total_users']}</b>\n"
        f"🚫 Banned Users: <b>{stats['banned_users']}</b>\n"
        f"🌐 Languages: " + ", ".join([f"{k}: {v}" for k, v in stats['languages'].items()])
    )
    await update.message.reply_text(msg, parse_mode="HTML")

async def banlist_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    admin_id = str(update.effective_user.id)
    if not is_admin(admin_id):
        await update.message.reply_text(get_message(admin_id, "unauthorized"))
        return
    if not banned_users:
        await update.message.reply_text("✅ No users are currently banned.")
        return
    msg = "🚫 <b>Banned Users:</b>\n" + "\n".join(banned_users)
    await update.message.reply_text(msg, parse_mode="HTML")

# -------------------- ENHANCED USER HANDLERS --------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    register_user(user_id)
    if is_banned(user_id):
        await update.message.reply_text(get_message(user_id, "banned"))
        return

    # Build language keyboard dynamically
    keyboard = []
    row = []
    for idx, (code, label) in enumerate(LANG_CHOICES):
        row.append(InlineKeyboardButton(label, callback_data=f"lang_{code}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    await update.message.reply_text(
        "🌐 اپنی زبان منتخب کریں / Select Your Language:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    # After language selection, show command keyboard
    # (This will be triggered in language_selected)

async def language_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    lang = query.data.replace("lang_", "")
    user_lang[user_id] = lang
    save_user_info(user_id, lang)
    welcome_msg = LANGUAGES.get(lang, LANGUAGES.get("english", {})).get("welcome", "Welcome!")
    full_welcome = LANGUAGES.get(lang, LANGUAGES.get("english", {})).get("full_welcome", "Welcome!")
    await query.edit_message_text(
        get_message(user_id, "language_set", message=welcome_msg),
        parse_mode="HTML"
    )
    await context.bot.send_message(
        chat_id=int(user_id),
        text=full_welcome,
        parse_mode="HTML",
        reply_markup=get_command_keyboard(user_id)
    )

async def change_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)

    if is_banned(user_id):
        await update.message.reply_text(get_message(user_id, "banned"))
        return

    await start(update, context)

async def user_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_id = str(user.id)
    lang = get_user_language(user_id)
    banned = "Yes 🚫" if is_banned(user_id) else "No ✅"
    total = len(user_lang)

    await update.message.reply_text(
        get_message(user_id, "user", user_id=user_id, lang=lang.capitalize(), banned=banned, total=total),
        parse_mode="HTML"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    await update.message.reply_text(get_message(user_id, "help"), parse_mode="HTML")

async def feedback_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)

    if is_banned(user_id):
        await update.message.reply_text(get_message(user_id, "banned"))
        return

    await update.message.reply_text(get_message(user_id, "welcome"), parse_mode="HTML")

# -------------------- HANDLERS: MESSAGES --------------------
async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_id = str(user.id)
    register_user(user_id)
    if is_banned(user_id):
        await update.message.reply_text(get_message(user_id, "banned"))
        return

    for admin_id in ADMIN_IDS:
        try:
            if update.message.text:
                sent = await context.bot.send_message(
                    chat_id=int(admin_id),
                    text=(
                        f"📩 From: {user.full_name} (@{user.username or 'NoUsername'})\n"
                        f"🆔 ID: {user.id}\n\n"
                        f"📝 {update.message.text}"
                    ),
                    parse_mode="HTML"
                )
            else:
                sent = await context.bot.forward_message(
                    chat_id=int(admin_id),
                    from_chat_id=user.id,
                    message_id=update.message.message_id
                )
            forward_map[sent.message_id] = user.id
        except Exception as e:
            logger.error(f"Forward Error to admin {admin_id}: {e}")

async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    admin_id = str(update.effective_user.id)

    if not is_admin(admin_id):
        await update.message.reply_text(get_message(admin_id, "unauthorized"))
        return

    msg = update.message
    if not msg.reply_to_message:
        await update.message.reply_text(get_message(admin_id, "reply_instructions"))
        return

    reply_msg_id = msg.reply_to_message.message_id
    user_id = forward_map.get(reply_msg_id)

    if not user_id:
        await update.message.reply_text(get_message(admin_id, "user_not_found"))
        return

    try:
        prefix = get_message(admin_id, "admin_reply_prefix")
        kwargs = {"chat_id": user_id, "parse_mode": "HTML"}

        if msg.text:
            await context.bot.send_message(text=prefix + msg.text, **kwargs)
        elif msg.photo:
            await context.bot.send_photo(photo=msg.photo[-1].file_id, caption=prefix + (msg.caption or ""), **kwargs)
        elif msg.document:
            await context.bot.send_document(document=msg.document.file_id, caption=prefix + (msg.caption or ""), **kwargs)
        elif msg.video:
            await context.bot.send_video(video=msg.video.file_id, caption=prefix + (msg.caption or ""), **kwargs)
        elif msg.audio:
            await context.bot.send_audio(audio=msg.audio.file_id, caption=prefix + (msg.caption or ""), **kwargs)
        elif msg.voice:
            await context.bot.send_voice(voice=msg.voice.file_id, caption=prefix + (msg.caption or ""), **kwargs)
        elif msg.sticker:
            await context.bot.send_sticker(chat_id=user_id, sticker=msg.sticker.file_id)
        else:
            await update.message.reply_text(get_message(admin_id, "invalid_format"))
            return

        await update.message.reply_text(get_message(admin_id, "reply_success"))
    except Exception as e:
        logger.error(f"Reply Error: {e}")
        await update.message.reply_text(get_message(admin_id, "reply_failed"))

# -------------------- FILE SHARING SYSTEM (SIMPLE, ROBUST) --------------------
import json as _json
from uuid import uuid4 as _uuid4

FILES_DB = "files.json"

async def upload_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text("📤 Send me a file to upload (Max 500MB).")
        context.user_data['awaiting_upload'] = True
    except Exception as e:
        logger.error(f"/upload error: {e}")
        await update.message.reply_text("❌ Error: Could not start upload process.")

async def handle_file_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('awaiting_upload'):
        return
    user_id = str(update.effective_user.id)
    file = update.message.document or update.message.video or update.message.audio or (update.message.photo[-1] if update.message.photo else None)
    if not file:
        await update.message.reply_text("❌ Unsupported file type.")
        context.user_data['awaiting_upload'] = False
        return
    if getattr(file, 'file_size', 0) > 500 * 1024 * 1024:
        await update.message.reply_text("❌ File too large! Max 500MB.")
        context.user_data['awaiting_upload'] = False
        return
    file_id = file.file_id
    file_name = getattr(file, 'file_name', 'Unnamed')
    file_type = 'photo' if update.message.photo else (
        'document' if update.message.document else (
            'video' if update.message.video else (
                'audio' if update.message.audio else 'unknown')))
    unique_id = str(_uuid4())[:10]
    # Load existing data
    try:
        if os.path.exists(FILES_DB):
            with open(FILES_DB, "r") as f:
                data = _json.load(f)
        else:
            data = {}
        # Save file info
        data[unique_id] = {
            "file_id": file_id,
            "file_name": file_name,
            "file_type": file_type,
            "uploader_id": user_id
        }
        with open(FILES_DB, "w") as f:
            _json.dump(data, f, indent=2)
        bot_username = (await context.bot.get_me()).username
        link = f"https://t.me/{bot_username}?start=file_{unique_id}"
        logger.info(f"File uploaded: {file_id} by {user_id}, link: {link}")
        await update.message.reply_text(f"✅ Your file is saved.\n🔗 Share this link:\n{link}")
    except Exception as e:
        logger.error(f"File upload error: {e}")
        await update.message.reply_text("❌ Error: Could not save file or generate link.")
    context.user_data['awaiting_upload'] = False

async def extended_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if args and args[0].startswith("file_"):
        file_key = args[0][5:]
        if os.path.exists(FILES_DB):
            with open(FILES_DB, "r") as f:
                data = _json.load(f)
            file_info = data.get(file_key)
            if file_info:
                try:
                    if file_info["file_type"] == "photo":
                        await context.bot.send_photo(update.effective_chat.id, photo=file_info["file_id"])
                    elif file_info["file_type"] == "video":
                        await context.bot.send_video(update.effective_chat.id, video=file_info["file_id"], caption=file_info["file_name"])
                    elif file_info["file_type"] == "audio":
                        await context.bot.send_audio(update.effective_chat.id, audio=file_info["file_id"], caption=file_info["file_name"])
                    else:
                        await context.bot.send_document(update.effective_chat.id, document=file_info["file_id"], filename=file_info["file_name"])
                    return
                except Exception as e:
                    await update.message.reply_text(f"❌ Error sending file: {e}")
                    return
        await update.message.reply_text("❌ File not found or link expired.")
    else:
        await start(update, context)

# --- FUN & UTILITY COMMANDS ---

async def myfiles_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not os.path.exists(FILES_DB):
        await update.message.reply_text("You have not uploaded any files yet.")
        return
    with open(FILES_DB, "r") as f:
        data = _json.load(f)
    user_files = [(k, v) for k, v in data.items() if v.get("uploader_id") == user_id]
    if not user_files:
        await update.message.reply_text("You have not uploaded any files yet.")
        return
    bot_username = (await context.bot.get_me()).username
    msg = "\n".join([
        f"{i+1}. {v['file_name']} ({v['file_type']})\n🔗 https://t.me/{bot_username}?start=file_{k}"
        for i, (k, v) in enumerate(user_files)
    ])
    await update.message.reply_text(f"Your files:\n{msg}")

async def randomfile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not os.path.exists(FILES_DB):
        await update.message.reply_text("No files in the database yet.")
        return
    with open(FILES_DB, "r") as f:
        data = _json.load(f)
    if not data:
        await update.message.reply_text("No files in the database yet.")
        return
    k, v = random.choice(list(data.items()))
    bot_username = (await context.bot.get_me()).username
    link = f"https://t.me/{bot_username}?start=file_{k}"
    await update.message.reply_text(f"Random file: {v['file_name']} ({v['file_type']})\n🔗 {link}")

async def deletefile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /deletefile <file_id>")
        return
    file_id = args[0]
    if not os.path.exists(FILES_DB):
        await update.message.reply_text("No files found.")
        return
    with open(FILES_DB, "r") as f:
        data = _json.load(f)
    file_info = data.get(file_id)
    if not file_info:
        await update.message.reply_text("File not found.")
        return
    if file_info.get("uploader_id") != user_id:
        await update.message.reply_text("You can only delete your own files.")
        return
    del data[file_id]
    with open(FILES_DB, "w") as f:
        _json.dump(data, f, indent=2)
    await update.message.reply_text("File deleted successfully.")

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 ᴰᵃʳᵏᴹᵃᵗʳᶦˣ™ - Feedback/File Bot\nCreated by @patelmilan07\nUpload, share, and manage files easily!\nEnjoy!",
        parse_mode="HTML"
    )

async def fileinfo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /fileinfo <file_id>")
        return
    file_id = args[0]
    if not os.path.exists(FILES_DB):
        await update.message.reply_text("No files found.")
        return
    with open(FILES_DB, "r") as f:
        data = _json.load(f)
    file_info = data.get(file_id)
    if not file_info:
        await update.message.reply_text("File not found.")
        return
    msg = f"<b>File Info</b>\nName: {file_info['file_name']}\nType: {file_info['file_type']}\nUploader: {file_info['uploader_id']}\nID: {file_id}"
    await update.message.reply_text(msg, parse_mode="HTML")

async def commands_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    lang_code = get_user_language(user_id)
    lang_file = f"lang/{lang_code[:2]}.json"
    if not os.path.exists(lang_file):
        lang_file = "lang/en.json"
    try:
        with open(lang_file, "r") as f:
            lang_data = json.load(f)
    except Exception:
        with open("lang/en.json", "r") as f:
            lang_data = json.load(f)
    def escape_html(text):
        return text.replace("<", "&lt;").replace(">", "&gt;")
    def get_cmd(key, subkey):
        try:
            return escape_html(lang_data["commands"][key][subkey])
        except Exception:
            with open("lang/en.json", "r") as f:
                en_data = json.load(f)
            return escape_html(en_data["commands"].get(key, {}).get(subkey, f"/{key}"))
    def get_section(section):
        try:
            return escape_html(lang_data["sections"][section])
        except Exception:
            with open("lang/en.json", "r") as f:
                en_data = json.load(f)
            return escape_html(en_data["sections"].get(section, section.title()))
    # User commands (remove uptime)
    user_cmds = [
        "start", "help", "about", "user", "language", "feedback", "commands"
    ]
    file_cmds = [
        "upload", "myfiles", "randomfile", "deletefile", "fileinfo"
    ]
    # Admin commands (add uptime)
    admin_cmds = [
        "ban", "unban", "broadcast", "stats", "banlist", "uptime"
    ]
    msg = f"<b>{get_section('user')}</b>\n"
    for cmd in user_cmds:
        msg += f"{get_cmd(cmd, 'label')} - {get_cmd(cmd, 'desc')}\n"
    msg += f"\n<b>{get_section('file')}</b>\n"
    for cmd in file_cmds:
        msg += f"{get_cmd(cmd, 'label')} - {get_cmd(cmd, 'desc')}\n"
    if is_admin(user_id):
        msg += f"\n<b>{get_section('admin')}</b>\n"
        for cmd in admin_cmds:
            msg += f"{get_cmd(cmd, 'label')} - {get_cmd(cmd, 'desc')}\n"
    await update.message.reply_text(msg.strip(), parse_mode="HTML")

# Utility to get localized command labels for keyboard
COMMON_COMMANDS = ["commands", "help", "language", "about"]
def get_command_keyboard(user_id: str):
    lang_code = get_user_language(user_id)
    lang_file = f"lang/{lang_code[:2]}.json"
    if not os.path.exists(lang_file):
        lang_file = "lang/en.json"
    try:
        with open(lang_file, "r") as f:
            lang_data = json.load(f)
    except Exception:
        with open("lang/en.json", "r") as f:
            lang_data = json.load(f)
    row = [lang_data["commands"].get(cmd, {}).get("label", f"/{cmd}") for cmd in COMMON_COMMANDS]
    return ReplyKeyboardMarkup([row], resize_keyboard=True)

# Track bot start time for uptime
BOT_START_TIME = time.time()

# Track last 10 reply times (ms)
LAST_REPLY_TIMES = []

# Utility to record reply time
def record_reply_time(start_time):
    elapsed = int((time.time() - start_time) * 1000)
    LAST_REPLY_TIMES.append(elapsed)
    if len(LAST_REPLY_TIMES) > 10:
        LAST_REPLY_TIMES.pop(0)

# --- Patch all user-facing reply handlers to record reply time ---
from functools import wraps

def track_reply_time(func):
    @wraps(func)
    async def wrapper(update, context, *args, **kwargs):
        start_time = time.time()
        result = await func(update, context, *args, **kwargs)
        # Only track if this is a user message (not admin, not callback)
        if hasattr(update, 'message') and update.message and update.message.chat.type == 'private':
            record_reply_time(start_time)
        return result
    return wrapper

# Patch main user commands
start = track_reply_time(start)
change_language = track_reply_time(change_language)
user_dashboard = track_reply_time(user_dashboard)
help_command = track_reply_time(help_command)
feedback_command = track_reply_time(feedback_command)
commands_command = track_reply_time(commands_command)
about_command = track_reply_time(about_command)

# Patch file commands
myfiles_command = track_reply_time(myfiles_command)
randomfile_command = track_reply_time(randomfile_command)
deletefile_command = track_reply_time(deletefile_command)
fileinfo_command = track_reply_time(fileinfo_command)

# Patch upload
upload_command = track_reply_time(upload_command)

# Patch handle_user_message
handle_user_message = track_reply_time(handle_user_message)

# Patch extended_start
extended_start = track_reply_time(extended_start)

# Patch language_selected (for callback)
language_selected = track_reply_time(language_selected)

# Update uptime_command to show avg reply time

def uptime_command_factory():
    async def uptime_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Send a dummy request to Telegram to measure real ping
        ping_start = time.time()
        await context.bot.get_me()
        ping_end = time.time()
        ms = int((ping_end - ping_start) * 1000)
        uptime_seconds = int(time.time() - BOT_START_TIME)
        uptime_str = time.strftime('%H:%M:%S', time.gmtime(uptime_seconds))
        sysinfo = f"<b>System:</b> {platform.system()} {platform.release()} ({platform.machine()})\n"
        sysinfo += f"<b>Python:</b> {platform.python_version()}\n"
        try:
            hostname = platform.node()
            sysinfo += f"<b>Hostname:</b> {hostname}\n"
        except Exception:
            pass
        try:
            with open('/proc/uptime', 'r') as f:
                seconds = float(f.readline().split()[0])
                sys_uptime = time.strftime('%H:%M:%S', time.gmtime(seconds))
                sysinfo += f"<b>VPS Uptime:</b> {sys_uptime}\n"
        except Exception:
            pass
        try:
            df = subprocess.check_output(['df', '-h', '/']).decode()
            lines = df.split('\n')[1].split()
            sysinfo += f"<b>Disk:</b> {lines[2]}/{lines[1]} used ({lines[4]})\n"
        except Exception:
            pass
        try:
            mem = subprocess.check_output(['free', '-h']).decode().split('\n')[1].split()
            sysinfo += f"<b>RAM:</b> {mem[2]}/{mem[1]} used\n"
        except Exception:
            pass
        # CPU info
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = [line for line in f if 'model name' in line]
                if cpuinfo:
                    sysinfo += f"<b>CPU:</b> {cpuinfo[0].split(':')[1].strip()}\n"
        except Exception:
            pass
        # Load average
        try:
            with open('/proc/loadavg', 'r') as f:
                load = f.read().split()[:3]
                sysinfo += f"<b>Load Avg:</b> {' '.join(load)}\n"
        except Exception:
            pass
        # Process count
        try:
            proc_count = len([name for name in os.listdir('/proc') if name.isdigit()])
            sysinfo += f"<b>Processes:</b> {proc_count}\n"
        except Exception:
            pass
        # Average reply time
        if LAST_REPLY_TIMES:
            avg_reply = sum(LAST_REPLY_TIMES) / len(LAST_REPLY_TIMES)
            sysinfo += f"<b>Avg Reply Time:</b> {int(avg_reply)} ms\n"
        else:
            sysinfo += f"<b>Avg Reply Time:</b> N/A\n"
        msg = (
            f"<b>🤖 Bot Uptime:</b> {uptime_str}\n"
            f"<b>Ping:</b> {ms} ms\n"
            f"{sysinfo}"
        )
        await update.message.reply_text(msg, parse_mode="HTML")
    return uptime_command

uptime_command = uptime_command_factory()

# -------------------- MAIN FUNCTION --------------------
def main() -> None:
    application = ApplicationBuilder().token(TOKEN).build()

    # File upload handlers
    application.add_handler(CommandHandler("upload", upload_command))

    # Start handler (with file sharing)
    application.add_handler(CommandHandler("start", extended_start))

    # User commands
    application.add_handler(CommandHandler("user", user_dashboard))
    application.add_handler(CommandHandler("language", change_language))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("feedback", feedback_command))
    application.add_handler(CommandHandler("commands", commands_command))  # Add new

    # Admin commands
    application.add_handler(CommandHandler("ban", ban_user))
    application.add_handler(CommandHandler("unban", unban_user))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("banlist", banlist_command))
    application.add_handler(CommandHandler("uptime", uptime_command))

    # Fun & utility commands
    application.add_handler(CommandHandler("myfiles", myfiles_command))
    application.add_handler(CommandHandler("randomfile", randomfile_command))
    application.add_handler(CommandHandler("deletefile", deletefile_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CommandHandler("fileinfo", fileinfo_command))

    # Callback for language selection
    application.add_handler(CallbackQueryHandler(language_selected, pattern="^lang_"))

    # Message handlers
    application.add_handler(MessageHandler(filters.ChatType.PRIVATE & (filters.Document.ALL | filters.VIDEO | filters.AUDIO), handle_file_upload))
    application.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.REPLY, handle_admin_reply))
    application.add_handler(MessageHandler(filters.ChatType.PRIVATE & ~filters.COMMAND, handle_user_message))

    # Start the Bot
    application.run_polling()
    logger.info("Bot started and running...")

if __name__ == "__main__":
    main()
