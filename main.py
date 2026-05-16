import telebot
import time
import threading
import random
import json
import os
import requests

# ضع التوكن الخاص ببوتك هنا
BOT_TOKEN = "8790528411:AAG1usu5mrWLLBiSL2YUmDqY_qKMFnGFpbs"
bot = telebot.TeleBot(BOT_TOKEN)

# اسم الملف الخارجي لحفظ القنوات
CHANNELS_FILE = "subscribed_channels.json"

# ----------------- وظائف إدارة ملف القنوات الخارجي -----------------

def load_channels():
    """تحميل القنوات من الملف الخارجي عند تشغيل البوت"""
    if os.path.exists(CHANNELS_FILE):
        try:
            with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return set(data)
        except Exception as e:
            print(f"[!] خطأ في قراءة ملف القنوات: {e}")
            return set()
    return set()

def save_channels():
    """حفظ قائمة القنوات الحالية في الملف الخارجي"""
    try:
        with open(CHANNELS_FILE, "w", encoding="utf-8") as f:
            json.dump(list(subscribed_chats), f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"[!] خطأ في حفظ ملف القنوات: {e}")

# تحميل القنوات المتوفرة في الذاكرة عند بدء التشغيل
subscribed_chats = load_channels()
print(f"[*] تم تحميل {len(subscribed_chats)} قناة من الملف الخارجي.")

# ----------------- وظائف جلب البيانات من الإنترنت (APIs) -----------------

def get_random_hadith():
    """جلب حديث عشوائي من API إسلامي مفتوح"""
    try:
        # سنستخدم API موسوعة الأحاديث الشهيرة أو أحد الـ APIs المفتوحة
        url = "https://hadeethenc.com/api/v1/hadeeths/list/?language=ar&category_id=1&per_page=20"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # اختيار حديث عشوائي من القائمة وجلب تفاصيله
            random_item = random.choice(data['data'])
            hadith_id = random_item['id']
            
            # جلب نص الحديث بالكامل
            detail_url = f"https://hadeethenc.com/api/v1/hadeeths/one/?language=ar&id={hadith_id}"
            detail_res = requests.get(detail_url, timeout=10)
            if detail_res.status_code == 200:
                hadith_data = detail_res.json()
                return hadith_data['hadeeth']
    except Exception as e:
        print(f"[!] خطأ أثناء جلب الحديث من الموقع: {e}")
    
    # في حال فشل الاتصال بالموقع، نضع حديث احتياطي (Fallback)
    return "قال رسول الله ﷺ: «إنَّما الأعْمالُ بالنِّيَّاتِ، وإنَّما لِكُلِّ امْرِئٍ ما نَوَى»"

def get_random_quran_verse():
    """جلب آية ورابطها الصوتي عشوائياً"""
    try:
        # نختار رقم سورة عشوائي (من 1 إلى 114) ورقم آية عشوائي
        # لتسهيل الأمر واختيار آيات مشهورة وقصيرة، سنستخدم API إذاعة القرآن أو القراء المشهورين
        # هنا سنختار قارئ عشوائي (مثلاً الشيخ مشاري العفاسي) من موقع Mp3Quran
        sura_number = str(random.randint(1, 114)).zfill(3) # يحول الرقم إلى 3 خانات مثل 001 أو 018
        
        # قائمة ببعض القراء الأجلاء وروابط سيرفراتهم المباشرة
        reciters = [
            {"name": "مشاري العفاسي", "server": "https://server8.mp3quran.net/afs/"},
            {"name": "عبد الباسط عبد الصمد", "server": "https://server7.mp3quran.net/basit/"},
            {"name": "ماهر المعيقلي", "server": "https://server12.mp3quran.net/maher/"},
            {"name": "سعود الشريم", "server": "https://server7.mp3quran.net/shur/"}
        ]
        
        reciter = random.choice(reciters)
        audio_url = f"{reciter['server']}{sura_number}.mp3"
        
        # جلب اسم السورة باللغة العربية عبر API سريع
        sura_api = f"https://api.alquran.cloud/v1/surah/{int(sura_number)}"
        res = requests.get(sura_api, timeout=10)
        sura_name = f"سورة رقم {int(sura_number)}"
        if res.status_code == 200:
            sura_name = res.json()['data']['name']

        return {"title": f"{sura_name} بصوت الشيخ {reciter['name']}", "url": audio_url}
    except Exception as e:
        print(f"[!] خطأ أثناء جلب القرآن من الموقع: {e}")
        
    return {"title": "سورة الفاتحة", "url": "https://server8.mp3quran.net/afs/001.mp3"}

# ----------------- التعامل مع تليجرام -----------------

@bot.my_chat_member_handler()
def handle_bot_added(update):
    chat_id = update.chat.id
    status = update.new_chat_member.status
    
    if status in ['administrator', 'member']:
        if chat_id not in subscribed_chats:
            subscribed_chats.add(chat_id)
            save_channels() # حفظ في الملف الخارجي فوراً
            print(f"[+] تم حفظ قناة جديدة: {chat_id}")
            try:
                bot.send_message(chat_id, "جزاكم الله خيراً على إضافة البوت. سيتم النشر التلقائي للقرآن والأحاديث هنا.")
            except Exception:
                pass
                
    elif status in ['left', 'kicked']:
        if chat_id in subscribed_chats:
            subscribed_chats.remove(chat_id)
            save_channels() # تحديث الملف الخارجي وحذفها
            print(f"[-] تم حذف القناة: {chat_id}")
@bot.message_handler(commands=['start'])
def send_photo(message):
    user_id = message.from_user.id
    firstname = message.from_user.first_name
    mention = f'<a href="tg://user?id={user_id}">{firstname}</a>'
    markup = InlineKeyboardMarkup(row_width=2)
    btn1 = InlineKeyboardButton('➕ اضف البوت لقناتك', url='https://t.me/Al_Quran_Alkareem_bot?startchannel=true')
    btn2 = InlineKeyboardButton('💎 قناة البوت', url='https://t.me/mox_source')
    btn3 = InlineKeyboardButton('🧑‍💻 المطور', url='https://t.me/qf9_0')
    markup.add(btn1)
    markup.add(btn2, btn3)

    bot.send_photo(message.chat.id, photo=open('logo.jpg', 'rb'), caption=f"""
<b>👋 مرحبا بك عزيزي {mention}

📖 في بوت القرآن الكريم 

📚 وظيفة البوت نشر آيات قرآنية تلقائيا

📌اضغط على زر اضف البوت لقناتك لاضافة البوت لقناتك ، اعطي للبوت جميع صلاحيات النشر وسيقوم بالنشر في الوقت المحدد ...</b>
""", reply_to_message_id=message.message_id, parse_mode='HTML', reply_markup=markup)

# ----------------- دالة النشر التلقائي المستمر -----------------

def auto_publisher():
    while True:
        # النشر كل ساعة (3600 ثانية)
        # للتجربة غيرها إلى 30 أو 60 ثانية
        time.sleep(120)
        
        if not subscribed_chats:
            continue
            
        print("[*] يتم جلب محتوى جديد الآن من المواقع...")
        post_type = random.choice(['hadith', 'audio'])
        
        content = None
        if post_type == 'hadith':
            content = get_random_hadith()
        else:
            content = get_random_quran_verse()
            
        # إرسال المحتوى لكل القنوات المخزنة
        for chat_id in list(subscribed_chats):
            try:
                if post_type == 'hadith':
                    bot.send_message(chat_id, f"📖 **حديث شريف:**\n\n{content}")
                else:
                    bot.send_audio(chat_id, content['url'], caption=f"🎧 **تلاوة خاشعة:** {content['title']}")
                print(f"[+] تم النشر بنجاح في القناة: {chat_id}")
            except Exception as e:
                print(f"[!] لم نتمكن من النشر في {chat_id} (ربما أزالوا البوت): {e}")
                # اختياري: يمكنك مسح القناة إذا تبين أن البوت طُرد منها نهائياً لمنع تكرار الخطأ
                # subscribed_chats.remove(chat_id)
                # save_channels()

# تشغيل الجدولة في الخلفية
threading.Thread(target=auto_publisher, daemon=True).start()

print("[*] البوت جاهز ويعمل...")
bot.infinity_polling()
