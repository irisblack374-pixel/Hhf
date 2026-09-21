<div align="center">

# 🤖 Hhf

### 🛡️ Discord Moderation • 🧰 Utilities • 📢 Server Tools

<p>
  <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/discord.py-2.x-5865F2?style=for-the-badge&logo=discord&logoColor=white" />
</p>

**بوت Discord متعدد الاستخدامات لإدارة السيرفر وتوفير أدوات مفيدة للأعضاء والإدارة.**

</div>

---

## 👀 ما هو Hhf؟

**Hhf** هو بوت Discord مبني باستخدام **Python وdiscord.py**.

فكرته ببساطة:

> 🏠 **يساعدك في إدارة السيرفر + يوفر أوامر وأدوات للأعضاء.**

بدل استخدام عدة بوتات لأشياء بسيطة، يجمع Hhf مجموعة من الأدوات في بوت واحد.

---

## ✨ ماذا يستطيع البوت أن يفعل؟

### 🛡️ 1. إدارة السيرفر

| الأمر | ماذا يفعل؟ |
|---|---|
| !clear | 🧹 يحذف عددًا من الرسائل |
| !kick | 👢 يطرد عضوًا |
| !ban | 🔨 يحظر عضوًا |
| !unban | 🔓 يفك حظر عضو |
| !lock | 🔒 يقفل الروم |
| !unlock | 🔓 يفتح الروم |
| !slowmode | 🐢 يضع Slowmode للروم |

> 🔐 هذه الأوامر تحتاج صلاحيات Discord المناسبة.

### 🧰 2. معلومات وأدوات

| الأمر | ماذا يفعل؟ |
|---|---|
| !ping | 🏓 يعرض استجابة البوت |
| !server | 🏠 يعرض معلومات السيرفر |
| !userinfo | 👤 يعرض معلومات عضو |
| !avatar | 🖼️ يعرض صورة الحساب |
| !uptime | ⏱️ يعرض مدة تشغيل البوت |
| !help | ❓ يعرض المساعدة |

### 📢 3. أدوات التفاعل

| الأمر | ماذا يفعل؟ |
|---|---|
| !say | 💬 يجعل البوت يرسل نصًا |
| !announce | 📣 ينشئ إعلانًا |
| !poll | 📊 ينشئ تصويتًا |

---

## 🎮 مثال سريع

إذا كتبت:

    !ping

يرد البوت بشيء مثل:

    🏓 Pong!
    Latency: 45ms

ومثال آخر:

    !userinfo @User

يعرض معلومات العضو بدل البحث عنها يدويًا.

---

## 🧩 كيف يعمل Hhf؟

    👤 المستخدم
         │
         ▼
    💬 يكتب الأمر
         │
         ▼
    🤖 Hhf يستقبل الأمر
         │
         ▼
    🧠 Python + discord.py
         │
         ▼
    ⚡ تنفيذ العملية
         │
         ▼
    💬 البوت يرسل النتيجة

---

## 🧰 التقنيات المستخدمة

| التقنية | الاستخدام |
|---|---|
| 🐍 Python | لغة برمجة البوت |
| 💬 discord.py | الاتصال بـ Discord |
| 🔐 .env | حفظ الإعدادات السرية |
| ☁️ Procfile | تشغيل البوت على بعض الاستضافات |

---

## 📂 شكل المشروع

    Hhf/
    │
    ├── 🤖 bot.py
    │   └── الكود الرئيسي للبوت
    │
    ├── 📦 requirements.txt
    │   └── المكتبات المطلوبة
    │
    ├── ☁️ Procfile
    │   └── أمر تشغيل البوت للاستضافة
    │
    ├── 🔐 .env.example
    │   └── مثال لإعدادات البيئة
    │
    ├── 🚫 .gitignore
    │   └── ملفات لا يجب رفعها
    │
    └── 📖 README.md
        └── شرح المشروع

---

## 🚀 تشغيل المشروع

### 💻 على الكمبيوتر

**1️⃣ حمّل المشروع**

    git clone https://github.com/irisblack374-pixel/Hhf.git
    cd Hhf

**2️⃣ ثبّت المكتبات**

    pip install -r requirements.txt

**3️⃣ أنشئ ملف .env**

ضع داخله:

    DISCORD_TOKEN=YOUR_BOT_TOKEN
    PREFIX=!

**4️⃣ شغّل البوت**

    python bot.py

إذا ظهر أن البوت متصل، يكون التشغيل ناجحًا. ✅

---

## 🔑 إعداد Discord

قبل تشغيل البوت، تحتاج إنشاء Bot من **Discord Developer Portal**.

ثم فعّل الـIntents المطلوبة حسب الأوامر المستخدمة، خصوصًا:

- 💬 **Message Content Intent**
- 👥 **Server Members Intent** عند الحاجة

ولا تضع التوكن الحقيقي داخل GitHub.

---

## 🔐 الأمان مهم جدًا

❌ لا ترفع ملف .env.

❌ لا تكتب التوكن داخل bot.py.

✅ استخدم متغيرات البيئة:

    DISCORD_TOKEN=YOUR_BOT_TOKEN

إذا انكشف التوكن، قم بتغييره فورًا من Discord Developer Portal.

---

## 🗺️ التطوير القادم

- [ ] 🛡️ إضافة أدوات Moderation أكثر
- [ ] 🧰 إضافة Utilities جديدة
- [ ] ⚠️ تحسين نظام الأخطاء
- [ ] 🧪 إضافة اختبارات
- [ ] 📖 توثيق الأوامر بشكل أكبر
- [ ] ⚙️ إضافة إعدادات أكثر للسيرفر

---

## ⭐ لماذا Hhf؟

لأن الهدف هو جعل الأدوات الأساسية للسيرفر **سهلة، واضحة، وفي مكان واحد**.

    Discord Server
          │
          ▼
       🤖 Hhf
       ├── 🛡️ Moderation
       ├── 🧰 Utilities
       ├── 📢 Tools
       └── ❓ Help

---

<div align="center">

### 🚀 Hhf

**Simple tools. Clear commands. One Discord bot.**

⭐ إذا أعجبك المشروع، يمكنك استكشاف المستودع وتجربته.

</div>
