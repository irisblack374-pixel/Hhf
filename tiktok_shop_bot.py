import discord
from discord.ext import commands
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

ALLOWED_CHANNEL_ID = 1376258517303951432  # رقم روم الطلبات عندك
SUPPORT_ROLE_ID = 987654321098765432     # حط رقم رتبة الدعم عندك

# تعريف الخدمات مع الأسعار حسب الكمية والوصف
services = {
    "مشاهدات": {
        500: "500  <:Pro:1381726405657886841>",
        1000: "1k <:Pro:1381726405657886841>",
        2000: "2k <:Pro:1381726405657886841>",
        3000: "3k <:Pro:1381726405657886841>",
        4000: "4k <:Pro:1381726405657886841>",
        5000: "5k <:Pro:1381726405657886841>",
        6000: "6k <:Pro:1381726405657886841>",
        7000: "7k <:Pro:1381726405657886841>",
        8000: "8k <:Pro:1381726405657886841>",
        9000: "9k <:Pro:1381726405657886841>",
        10000: "10k <:Pro:1381726405657886841>",
    },
    "لايكات": {
        100: "1k <:Pro:1381726405657886841>",
        200: "2k <:Pro:1381726405657886841>",
        300: "3k <:Pro:1381726405657886841>",
        400: "4k <:Pro:1381726405657886841>",
    },
    "حفظ": {
        100: "1k <:Pro:1381726405657886841>",
        200: "2k <:Pro:1381726405657886841>",
        300: "3k <:Pro:1381726405657886841>",
        400: "4k <:Pro:1381726405657886841>",
        500: "5k <:Pro:1381726405657886841>",
    },
    "اكسبلور": {
        200: "2k <:Pro:1381726405657886841>",
        400: "5k <:Pro:1381726405657886841>",
        600: "7k <:Pro:1381726405657886841>",
        800: "9k <:Pro:1381726405657886841>",
        1000: "20k <:Pro:1381726405657886841>",
    },
    "لايكات_ع_كومنت": {
        70: "1.7k <:Pro:1381726405657886841>",
        80: "1.8k <:Pro:1381726405657886841>",
        100: "2k <:Pro:1381726405657886841>",
        200: "3k <:Pro:1381726405657886841>",
        300: "4k <:Pro:1381726405657886841>",
        500: "5k <:Pro:1381726405657886841>",
        1000: "10k <:Pro:1381726405657886841>",
    },
}

open_tickets = {}

@bot.event
async def on_ready():
    print(f'✅ بوت تيك توك جاهز كـ {bot.user}')
    await bot.change_presence(activity=discord.Game(name="TikTok Services Shop 2025"))

@bot.command()
async def قائمة(ctx):
    msg = """**📋 قائمة خدمات تيك توك المتوفرة والكميات:**"""
    for service, amounts in services.items():
        msg += f"\n**{service}**:\n"
        for amt, desc in amounts.items():
            msg += f" - {amt} = {desc}\n"
    msg += "\nلطلب خدمة: `!طلب اسم_الخدمة الكمية`"
    await ctx.send(msg)

@bot.command()
async def طلب(ctx, service_name: str, amount: int):
    if ctx.channel.id != ALLOWED_CHANNEL_ID:
        await ctx.send(f"⚠️ يرجى استخدام روم الطلبات: <#{ALLOWED_CHANNEL_ID}>")
        return

    service_name = service_name.lower()
    matched_service = None
    for s in services:
        if s.lower() == service_name:
            matched_service = s
            break

    if not matched_service:
        await ctx.send("❌ الخدمة غير موجودة، استخدم الأمر `!قائمة` لعرض الخدمات.")
        return

    if amount not in services[matched_service]:
        await ctx.send(f"❌ الكمية {amount} غير متوفرة لخدمة {matched_service}.")
        return

    price_description = services[matched_service][amount]

    guild_id = ctx.guild.id
    user_id = ctx.author.id

    if guild_id not in open_tickets:
        open_tickets[guild_id] = {}

    if user_id in open_tickets[guild_id]:
        channel = bot.get_channel(open_tickets[guild_id][user_id])
        await ctx.send(f"🛑 لديك تذكرة مفتوحة: {channel.mention}")
        return

    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        ctx.guild.get_role(SUPPORT_ROLE_ID): discord.PermissionOverwrite(read_messages=True, send_messages=True),
        bot.user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }

    ticket_channel = await ctx.guild.create_text_channel(f"ticket-{ctx.author.name}", overwrites=overwrites, reason="فتح تذكرة طلب خدمة تيك توك")

    open_tickets[guild_id][user_id] = ticket_channel.id

    await ticket_channel.send(f"""مرحباً {ctx.author.mention}!
تم فتح تذكرتك لطلب خدمة: **{matched_service}**
الكمية: **{amount}**
السعر/الوصف: {price_description}
يرجى إرسال إثبات الدفع هنا، وسيتم الرد عليك بأقرب وقت.""")

    await ctx.send(f"✅ تم فتح تذكرة طلب في {ticket_channel.mention}")

@bot.command()
async def إغلاق(ctx):
    guild_id = ctx.guild.id
    user_id = ctx.author.id

    if guild_id in open_tickets and user_id in open_tickets[guild_id]:
        channel_id = open_tickets[guild_id][user_id]
        if ctx.channel.id != channel_id:
            await ctx.send("❌ أمر الإغلاق يجب استخدامه داخل قناة التذكرة الخاصة بك.")
            return

        await ctx.send("🔒 جاري إغلاق التذكرة...")

        del open_tickets[guild_id][user_id]

        await asyncio.sleep(3)
        await ctx.channel.delete(reason="إغلاق تذكرة من قبل المستخدم")
    else:
        await ctx.send("❌ لا توجد تذكرة مفتوحة لك.")

@bot.command()
async def تقييم(ctx, rating: int):
    if rating < 1 or rating > 5:
        await ctx.send("❌ الرجاء اختيار تقييم بين 1 و 5 فقط.")
        return
    await ctx.send(f"🌟 شكراً على تقييمك {ctx.author.mention}! تقييمك: {rating}/5")

@bot.command()
@commands.has_role(SUPPORT_ROLE_ID)
async def إعلان(ctx, *, message: str):
    channel = bot.get_channel(ALLOWED_CHANNEL_ID)
    if channel:
        await channel.send(f"""📢 إعلان من الإدارة:
{message}""")
    else:
        await ctx.send("❌ لم أتمكن من العثور على روم الطلبات.")

@إعلان.error
async def إعلان_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("❌ هذا الأمر خاص بالإدارة فقط.")

# ضع توكن البوت الصحيح هنا بين علامات الاقتباس
bot.run("MTM5ODAwNTgxODIwODU1MTA4NA.G-Hr3D._d8gG1247U7u3LxSXDeANw52L3mIIKVgUQNiyY") 
