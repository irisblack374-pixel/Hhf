# Hhf

بوت Discord متعدد الاستخدامات للإدارة والأدوات، مبني باستخدام Python وdiscord.py.

## ✨ المميزات

- 🤖 نظام مساعدة وأوامر مرتب.
- 🛡️ أوامر إدارة للسيرفر.
- 🧹 حذف الرسائل.
- 👢 طرد الأعضاء وحظرهم وفك الحظر.
- 🔒 قفل وفتح الرومات.
- 🐢 Slowmode.
- 📢 إعلانات Embed.
- 📊 تصويتات 👍 و👎.
- 👤 معلومات الأعضاء والسيرفر.
- 🖼️ عرض Avatar.
- 🏓 Ping وقياس سرعة البوت.
- ⏱️ معرفة مدة تشغيل البوت.
- 🔐 التوكن محفوظ في متغيرات البيئة.

## 📁 الملفات

```
Hhf/
├── bot.py
├── requirements.txt
├── Procfile
├── .env.example
├── .gitignore
└── README.md
```

## 🛠️ المتطلبات

- Python 3.11 أو أحدث.
- Bot Token من Discord Developer Portal.
- تفعيل Message Content Intent.
- تفعيل Server Members Intent إذا كنت تحتاج أوامر الأعضاء.

## ⚙️ إعداد التوكن

لا تضع توكن البوت داخل GitHub.

في الاستضافة أضف:

```env
DISCORD_TOKEN=ضع_توكن_البوت_هنا
PREFIX=!
```

## 🚀 التشغيل

ثبّت المكتبات:

```bash
pip install -r requirements.txt
```

ثم شغّل:

```bash
python bot.py
```

وعلى الاستضافات التي تدعم Procfile سيستخدم المشروع:

```
worker: python3 bot.py
```

## 📋 الأوامر

### 📌 عام

```
!help
!ping
!server
!userinfo [@عضو]
!avatar [@عضو]
!uptime
```

### 🛡️ الإدارة

```
!clear <عدد>
!kick @عضو [سبب]
!ban @عضو [سبب]
!unban <ID>
!lock
!unlock
!slowmode <ثواني>
```

### 📢 الأدوات

```
!say <النص>
!announce <النص>
!poll <السؤال>
```

أوامر الإدارة تحتاج صلاحيات Discord المناسبة، مثل Manage Messages أو Kick Members أو Ban Members أو Manage Channels.

## 🔐 الأمان

- لا ترفع ملف `.env` إلى GitHub.
- لا تكتب `DISCORD_TOKEN` داخل الكود.
- استخدم متغيرات البيئة في الاستضافة.
- إذا انكشف التوكن، قم بتغييره فورًا من Discord Developer Portal.

## 📄 الحقوق والترخيص

© 2026 Hhf. All rights reserved.

هذا المشروع مملوك لصاحب المشروع.  
يُمنع نسخ المشروع أو إعادة نشره أو بيعه أو استخدامه كمشروع تجاري بدون إذن صاحب المشروع.
