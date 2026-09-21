# Discord Bot

بوت Discord مبني باستخدام Python و discord.py.

## الملفات
- `bot.py` — ملف البوت الرئيسي.
- `requirements.txt` — المكتبات المطلوبة.
- `.env.example` — نموذج ملف البيئة.
- `user_points.json` — ملف حفظ النقاط.
- `.gitignore` — ملفات وبيانات لا يتم رفعها إلى GitHub.

## التشغيل
```bash
pip install -r requirements.txt
python bot.py
```

أنشئ ملف `.env` من `.env.example` وضع توكن البوت في:
`DISCORD_TOKEN=YOUR_BOT_TOKEN`

لا ترفع ملف `.env` إلى GitHub.
