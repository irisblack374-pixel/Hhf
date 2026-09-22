import os
import re
import math
import json
import random
import string
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv

# تحميل المتغيرات من ملف .env
load_dotenv()

# ==========================================
# ⚙️ 1. قسم الإعدادات (CONFIG SECTION)
# ==========================================
CONFIG = {
    "TOKEN": os.getenv("DISCORD_TOKEN"),
    "REVIEWS_CHANNEL_ID": 1401430709599473744, # روم التقييمات
    "TAX_CHANNEL_ID": 1380484186166657094,     # روم الضرائب
    "BOOST_CHANNEL_ID": 1460172405908701238,   # روم الداعمين
    "LOGS_CHANNEL_ID": 0                       # ID روم اللوج لإرسال التنبيهات (اختياري)
}

# لوحة الألوان
COLOR_METALLIC_DARK = 0x2C2F33
COLOR_STEEL_SILVER  = 0x8C8C8C
COLOR_GOLD_ACCENT   = 0x9E7200
COLOR_CUSTOM_GREY   = 0xA4A4A4
COLOR_RED_ALERT     = 0xE74C3C

# 👑 هيكلية الرتب والنقاط الكاملة
CLIENT_ROLES = [
    {"id": 1537649596505923594, "name": "VIP",            "points": 100},
    {"id": 1537778129756758016, "name": "Ruby Client",    "points": 50},
    {"id": 1537648357319770112, "name": "Elite Client",   "points": 30},
    {"id": 1537647921959272489, "name": "Loyal Client",   "points": 20},
    {"id": 1537645657538699375, "name": "High Client",    "points": 12},
    {"id": 1537644929507922030, "name": "Special Client", "points": 9},
    {"id": 1537643124933787688, "name": "Premium Client", "points": 6},
    {"id": 1537642937549201468, "name": "Golden Client",  "points": 3},
    {"id": 1380479580871200830, "name": "Client",         "points": 1}
]

# ==========================================
# 🛡️ 2. أنماط الكشف عن الاختراق والروابط (PATTERNS)
# ==========================================
# Pattern لرصد روابط سيرفرات ديسكورد
DISCORD_INVITE_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?(?:discord\.(?:gg|io|me|li)|discordapp\.com/invite|discord\.com/invite)/[a-zA-Z0-9\-]+",
    re.IGNORECASE
)

# كلمات وعبارات شائعة تستخدمها الحسابات المخترقة لترويج الاحتيال والعملات
SCAM_KEYWORDS = [
    "crypto", "airdrop", "free nitro", "steam promo", "giveaway", 
    "earn usdt", "binance gift", "claim now", "bitcoin bonus",
    "ربح عملات", "نيترو مجاني", "توزيع عملات", "استلم هديتك"
]

# ==========================================
# 💾 3. نظام حفظ وتخزين النقاط
# ==========================================
DATA_FILE = "user_points.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading JSON data: {e}")
            return {}
    return {}

def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving JSON data: {e}")

user_data = load_data()

# ==========================================
# 🤖 4. إعدادات البوت والـ Class المخصص
# ==========================================
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

class CustomBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="-", intents=intents)

bot = CustomBot()

def parse_amount(text: str):
    text = text.strip().lower()
    match = re.match(r"^(\d+(?:\.\d+)?)\s*([km])?$", text)
    if not match:
        return None
    val, unit = match.groups()
    val = float(val)
    if unit == 'k': val *= 1_000
    elif unit == 'm': val *= 1_000_000
    return int(val)

# ==========================================
# 🏆 5. دالة تحديث الرتبة تلقائياً
# ==========================================
async def update_user_role(member: discord.Member, total_points: int):
    guild = member.guild
    target_role_info = None

    for role_info in CLIENT_ROLES:
        if total_points >= role_info["points"]:
            target_role_info = role_info
            break

    if not target_role_info or target_role_info["id"] == 0:
        return None

    target_role = guild.get_role(target_role_info["id"])
    if not target_role:
        return None

    all_role_ids = [r["id"] for r in CLIENT_ROLES if r["id"] != 0]
    roles_to_remove = [r for r in member.roles if r.id in all_role_ids and r.id != target_role.id]

    try:
        if roles_to_remove:
            await member.remove_roles(*roles_to_remove)

        if target_role not in member.roles:
            await member.add_roles(target_role)
            return target_role.name
    except discord.Forbidden:
        print("❌ Forbidden: رتبة البوت أدنى من رتب العملاء!")
        return None
    except Exception as e:
        print(f"حدث خطأ أثناء تحديث الرتب: {e}")
        return None

    return None

# ==========================================
# 👑 6. أوامر النقاط (!addp, !removep, !p)
# ==========================================
@bot.command(name="addp", aliases=["addpoints"])
@commands.has_permissions(administrator=True)
async def add_points(ctx, member: discord.Member, points: int = 1):
    if points <= 0:
        await ctx.send("❌ يرجى إدخال عدد نقاط أكبر من 0.")
        return

    user_id = str(member.id)
    user_data[user_id] = user_data.get(user_id, 0) + points
    save_data(user_data)

    current_points = user_data[user_id]
    new_role_name = await update_user_role(member, current_points)

    embed = discord.Embed(
        title="🎉 تم إضافة نقاط جديدة",
        description=f"تم إضافة **`{points}`** نقطة لـ {member.mention}\nمجموع النقاط الحالي: **`{current_points}`** PTS",
        color=COLOR_STEEL_SILVER
    )
    if new_role_name:
        embed.add_field(name="👑 ترقية جديدة!", value=f"تم ترقية العميل إلى رتبة: **{new_role_name}**", inline=False)

    await ctx.send(embed=embed)

    reviews_channel_url = f"https://discord.com/channels/{ctx.guild.id}/{CONFIG['REVIEWS_CHANNEL_ID']}"

    dm_message = (
        f"أهلاً {member.mention} 👋\n\n"
        f"<:ronaldo_drinks:1461719703843242219> لقد حصلت على `{points}` نقطة جديدة\n\n"
        f"<:9_:1464682523350138922> مجموع نقاطك الآن: `{current_points}`\n\n"
        f"<a:by_noobot:1461115489227899107> لا تنسَ تقييمنا هنا: {reviews_channel_url}"
    )

    try:
        await member.send(dm_message)
    except discord.Forbidden:
        await ctx.send(f"⚠️ تعذر إرسال رسالة الخاص لـ {member.mention} لأن خاص العضو مغلق.")

@bot.command(name="removep", aliases=["removepoints"])
@commands.has_permissions(administrator=True)
async def remove_points(ctx, member: discord.Member, amount: int = 1):
    user_id = str(member.id)
    current_pts = user_data.get(user_id, 0)

    new_pts = max(0, current_pts - amount)
    user_data[user_id] = new_pts
    save_data(user_data)

    await update_user_role(member, new_pts)

    await ctx.send(f"📉 تم خصم `{amount}` نقطة من {member.mention}. النقاط الحالية: `{new_pts}`.")

@bot.command(name="p", aliases=["points"])
async def show_points(ctx, member: discord.Member = None):
    member = member or ctx.author
    user_id = str(member.id)
    pts = user_data.get(user_id, 0)

    await ctx.send(str(pts))

# ==========================================
# 🗣️ 7. أوامر التقليد والإرسال (!say & !embed)
# ==========================================
@bot.command(name="say")
@commands.has_permissions(administrator=True)
async def say(ctx, *, message: str):
    try: await ctx.message.delete()
    except Exception: pass
    await ctx.send(message)

@bot.command(name="embed")
async def send_embed(ctx):
    content = ctx.message.content
    text = content.replace("!embed", "", 1).strip()
    attachments = ctx.message.attachments
    try: await ctx.message.delete()
    except Exception: pass

    if not text and not attachments:
        msg = await ctx.send("❌ يرجى كتابة نص أو إرفاق صورة مع الأمر.")
        await asyncio.sleep(3)
        await msg.delete()
        return

    embed = discord.Embed(description=text if text else "", color=COLOR_CUSTOM_GREY)
    if attachments: embed.set_image(url=attachments[0].url)
    await ctx.send(embed=embed)

# ==========================================
# ⭐ 8. ميزة نظام التقييمات (REVIEWS MODULE)
# ==========================================
class StarRatingView(discord.ui.View):
    def __init__(self, author: discord.User, review_text: str):
        super().__init__(timeout=300)
        self.author = author
        self.review_text = review_text

    async def handle_rating(self, interaction: discord.Interaction, stars_count: int):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ هذا التقييم ليس لك!", ephemeral=True)
            return

        stars_display = "⭐" * stars_count + "⬛" * (5 - stars_count)

        embed = discord.Embed(
            title="💬 تقييم جديد", description=self.review_text, color=COLOR_GOLD_ACCENT
        )
        embed.add_field(name="التقييم:", value=f"{stars_display} (`{stars_count}/5`)", inline=False)
        embed.set_author(name=self.author.display_name, icon_url=self.author.display_avatar.url)
        embed.set_footer(text=f"ID العميل: {self.author.id}")
        embed.timestamp = discord.utils.utcnow()

        await interaction.response.edit_message(content=None, embed=embed, view=None)

        message = interaction.message
        reactions = ["LG236:1464269475078602814", "Heart:1481752602420183109"]
        for react in reactions:
            try: await message.add_reaction(react)
            except Exception: pass

    @discord.ui.button(label="1 ⭐", style=discord.ButtonStyle.secondary, row=0)
    async def star_1(self, interaction: discord.Interaction, button: discord.ui.Button): await self.handle_rating(interaction, 1)

    @discord.ui.button(label="2 ⭐", style=discord.ButtonStyle.secondary, row=0)
    async def star_2(self, interaction: discord.Interaction, button: discord.ui.Button): await self.handle_rating(interaction, 2)

    @discord.ui.button(label="3 ⭐", style=discord.ButtonStyle.secondary, row=0)
    async def star_3(self, interaction: discord.Interaction, button: discord.ui.Button): await self.handle_rating(interaction, 3)

    @discord.ui.button(label="4 ⭐", style=discord.ButtonStyle.secondary, row=1)
    async def star_4(self, interaction: discord.Interaction, button: discord.ui.Button): await self.handle_rating(interaction, 4)

    @discord.ui.button(label="5 ⭐", style=discord.ButtonStyle.secondary, row=1)
    async def star_5(self, interaction: discord.Interaction, button: discord.ui.Button): await self.handle_rating(interaction, 5)

# ==========================================
# 🔐 أوامر الإدارة: التحويل والنداء
# ==========================================
ADMIN_ROLE_ID = 1380478810826211412
TRANSFER_TARGET_ID = 1125275172618899588
TRANSFER_DESTINATION_ID = 1401256824941842442

async def admin_only(ctx):
    role = ctx.guild.get_role(ADMIN_ROLE_ID) if ctx.guild else None
    if role is None or role not in ctx.author.roles:
        await ctx.send("❌ هذا الأمر مخصص للإدارة فقط.")
        return False
    return True

@bot.command(name="حول")
async def transfer_amount(ctx, amount: str):
    if not await admin_only(ctx):
        return

    value = parse_amount(amount)
    if value is None or value <= 0:
        await ctx.send("❌ يرجى إدخال مبلغ صحيح، مثل: `-حول 100m`")
        return

    transfer_text = f"t {TRANSFER_TARGET_ID} {value}"
    embed = discord.Embed(
        description=(
            f"**حول ل**\n"
            f"`{transfer_text}`\n\n"
            f"**يرجى التحويل هنا** <#{TRANSFER_DESTINATION_ID}>"
        ),
        color=COLOR_CUSTOM_GREY
    )
    await ctx.send(embed=embed)
    await ctx.send(transfer_text)

@bot.command(name="قيم")
async def rate_command(ctx):
    await ctx.send(
        "شكرا لثقتك فينا<:LG236:1464269475078602814>\\n\\n"
        "إذا كل شيء تمام معك والمنتج عجبك، لا تنسى تعطينا تقييمك ب خمس نجوم <a:yellowstar:1551498079675355189>  \\n"
        "https://discord.com/channels/1380470925698273352/1401430709599473744\\n"
        "تقييمك يفرق معنا كثير ويساعدنا \\n"
        "نستمر ونقدم الأفضل <:I_42:1514777044372951121>"
    )

@bot.command(name="تعال")
async def call_member(ctx, member: discord.Member):
    if not await admin_only(ctx):
        return

    try:
        await ctx.message.delete()
    except Exception:
        pass

    await ctx.send(
        embed=discord.Embed(
            description=f"<a:Emojis:1464682594649116887> **تم إرسال النداء لـ {member.mention}**",
            color=0x57F287
        )
    )

    ticket_url = ctx.channel.jump_url
    dm_message = (
        f"<a:Emojis:1464682594649116887> **تم استدعاؤك من الإدارة**\n\n"
        f"📩 تم إرسال نداء لك داخل السيرفر، يرجى التوجه إلى التكت للمتابعة.\n\n"
        f"🔗 **اضغط هنا للانتقال مباشرة:**\n{ticket_url}\n\n"
        f"✨ ننتظرك داخل التكت."
    )

    try:
        await member.send(dm_message)
    except discord.Forbidden:
        await ctx.send(f"⚠️ تعذر إرسال رسالة الخاص لـ {member.mention} لأن خاص العضو مغلق.")

# ==========================================
# 🚀 9. الأحداث ونظام التفاعلات والحماية (EVENTS & PROTECTION)
# ==========================================
@bot.event
async def on_message(message: discord.Message):
    # تجاهل رسائل البوتات تماماً لمنع الحلقات، مع إبقاء أوامر البوت خارج أي فلترة تلقائية.
    if message.author.bot:
        return

    # أوامر البوت تبدأ بـ "-" حسب إعداد command_prefix.
    # يتم تمريرها مباشرة إلى نظام الأوامر حتى لا يؤثر AutoMod عليها.
    command_prefix = bot.command_prefix
    if isinstance(command_prefix, str) and message.content.startswith(command_prefix):
        await bot.process_commands(message)
        return

    # الإداريون مستثنون من الفلترة التلقائية، مع إبقاء بقية معالجة الرسالة كما هي.
    if message.author.guild_permissions.administrator:
        return

    content_lower = message.content.lower()

    # 1️⃣ نظام حماية روابط السيرفرات (Anti-Discord Invite)
    if DISCORD_INVITE_PATTERN.search(message.content):
        try:
            await message.delete()
            warning = await message.channel.send(
                f"⚠️ {message.author.mention} يُمنع نشر روابط سيرفرات ديسكورد هنا!"
            )
            await asyncio.sleep(5)
            await warning.delete()
        except Exception as e:
            print(f"Error handling invite link: {e}")
        return

    # 2️⃣ نظام كشف الحسابات المخترقة ورسائل الاحتيال (Anti-Scam / Hacked Accounts)
    has_link = "http://" in content_lower or "https://" in content_lower
    has_scam_keyword = any(kw in content_lower for kw in SCAM_KEYWORDS)

    # إذا كانت الرسالة تحتوي على رابط + كلمة احتيالية شائعة
    if has_link and has_scam_keyword:
        try:
            await message.delete()
            alert = await message.channel.send(
                f"🚨 {message.author.mention} تم حذف رسالتك تلقائياً لاحتوائها على محتوى مريب قد يشير إلى اختراق الحساب."
            )
            await asyncio.sleep(7)
            await alert.delete()
        except Exception as e:
            print(f"Error handling scam message: {e}")
        return

    # 3️⃣ معالجة الأحداث العادية للسيرفر
    if getattr(message.type, "name", "") in ("premium_guild_subscription", "premium_guild_tier_1", "premium_guild_tier_2", "premium_guild_tier_3"):
        boost_channel = message.guild.get_channel(CONFIG["BOOST_CHANNEL_ID"])
        if boost_channel and message.channel.id == CONFIG["BOOST_CHANNEL_ID"]:
            msg = f"> **__Thanks For Support Us <:LG236:1464269475078602814> {message.author.mention}__**"
            await boost_channel.send(msg)
        return

    if message.channel.id == CONFIG["TAX_CHANNEL_ID"]:
        amount = parse_amount(message.content)
        if amount is not None and amount > 0:
            total_needed = math.ceil((amount * 20) / 19 + 1)
            await message.channel.send(str(total_needed))
            return

    if message.channel.id == CONFIG["REVIEWS_CHANNEL_ID"]:
        review_text = message.content
        author = message.author
        try: await message.delete()
        except Exception: pass

        view = StarRatingView(author=author, review_text=review_text)
        await message.channel.send(
            content=f"👋 أهلاً {author.mention}، يرجى اختيار تقييمك للخدمة عبر الأزرار أدناه:",
            view=view
        )

    await bot.process_commands(message)

# ==========================================
# 🚀 10. التشغيل
# ==========================================
@bot.event
async def on_ready():
    print("---------------------------------------")
    print(f"✅ تم تشغيل البوت بنجاح باسم: {bot.user}")
    print(f"🆔 ID البوت: {bot.user.id}")
    print("🛡️ نظام الحماية ضد الروابط والاحتيال مفعل بالكامل!")
    print("---------------------------------------")

if __name__ == "__main__":
    token = CONFIG["TOKEN"]
    if not token:
        print("❌ خطأ: لم يتم العثور على DISCORD_TOKEN في ملف .env")
    else:
        bot.run(token)