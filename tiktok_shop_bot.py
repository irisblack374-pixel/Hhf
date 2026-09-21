import os
import json
import asyncio
import logging
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
ALLOWED_CHANNEL_ID = int(os.getenv("ORDERS_CHANNEL_ID", "1376258517303951432"))
SUPPORT_ROLE_ID = int(os.getenv("SUPPORT_ROLE_ID", "0"))
TICKET_CATEGORY_ID = int(os.getenv("TICKET_CATEGORY_ID", "0"))
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", "0"))

DATA_FILE = Path("tickets.json")
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

services = {
    "مشاهدات": {500: "500", 1000: "1k", 2000: "2k", 3000: "3k", 4000: "4k", 5000: "5k", 6000: "6k", 7000: "7k", 8000: "8k", 9000: "9k", 10000: "10k"},
    "لايكات": {100: "1k", 200: "2k", 300: "3k", 400: "4k"},
    "حفظ": {100: "1k", 200: "2k", 300: "3k", 400: "4k", 500: "5k"},
    "اكسبلور": {200: "2k", 400: "5k", 600: "7k", 800: "9k", 1000: "20k"},
    "لايكات_ع_كومنت": {70: "1.7k", 80: "1.8k", 100: "2k", 200: "3k", 300: "4k", 500: "5k", 1000: "10k"},
}

def load_tickets():
    if not DATA_FILE.exists():
        return {}
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}

open_tickets = load_tickets()

def save_tickets():
    DATA_FILE.write_text(json.dumps(open_tickets, ensure_ascii=False, indent=2), encoding="utf-8")

def support_role(guild):
    return guild.get_role(SUPPORT_ROLE_ID) if SUPPORT_ROLE_ID else None

def is_support(member):
    role = support_role(member.guild)
    return member.guild_permissions.manage_channels or (role and role in member.roles)

async def send_log(guild, title, description):
    if not LOG_CHANNEL_ID:
        return
    channel = guild.get_channel(LOG_CHANNEL_ID)
    if channel:
        await channel.send(embed=discord.Embed(title=title, description=description, color=discord.Color.blurple()))

@bot.event
async def on_ready():
    logging.info("Logged in as %s", bot.user)
    await bot.change_presence(activity=discord.Game(name="TikTok Services Shop"))

@bot.command(name="قائمة")
async def list_services(ctx):
    embed = discord.Embed(title="📋 خدمات المتجر", color=discord.Color.blurple())
    for service, amounts in services.items():
        lines = [f"• **{amount}** → {desc}" for amount, desc in amounts.items()]
        embed.add_field(name=service.replace("_", " "), value="\n".join(lines), inline=False)
    embed.set_footer(text="لطلب خدمة: !طلب اسم_الخدمة الكمية")
    await ctx.send(embed=embed)

@bot.command(name="طلب")
@commands.cooldown(1, 15, commands.BucketType.user)
async def create_ticket(ctx, service_name: str, amount: int):
    if ctx.channel.id != ALLOWED_CHANNEL_ID:
        return await ctx.reply(f"⚠️ استخدم روم الطلبات: <#{ALLOWED_CHANNEL_ID}>")

    matched = next((s for s in services if s.lower() == service_name.lower()), None)
    if not matched:
        return await ctx.reply("❌ الخدمة غير موجودة. استخدم !قائمة.")

    if amount not in services[matched]:
        return await ctx.reply(f"❌ الكمية {amount} غير متوفرة لخدمة {matched}.")

    guild_key, user_key = str(ctx.guild.id), str(ctx.author.id)
    guild_tickets = open_tickets.setdefault(guild_key, {})
    existing_id = guild_tickets.get(user_key)

    if existing_id:
        existing = ctx.guild.get_channel(int(existing_id))
        if existing:
            return await ctx.reply(f"🛑 لديك تذكرة مفتوحة: {existing.mention}")
        guild_tickets.pop(user_key, None)

    category = ctx.guild.get_channel(TICKET_CATEGORY_ID) if TICKET_CATEGORY_ID else None
    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False),
        ctx.author: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
        ctx.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True),
    }

    role = support_role(ctx.guild)
    if role:
        overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

    channel = await ctx.guild.create_text_channel(
        name=f"ticket-{ctx.author.name[:18]}",
        category=category if isinstance(category, discord.CategoryChannel) else None,
        overwrites=overwrites,
        reason="TikTok shop ticket",
    )

    guild_tickets[user_key] = channel.id
    save_tickets()

    embed = discord.Embed(title="🎫 طلب جديد", color=discord.Color.green())
    embed.add_field(name="الخدمة", value=matched, inline=True)
    embed.add_field(name="الكمية", value=str(amount), inline=True)
    embed.add_field(name="الخيار", value=services[matched][amount], inline=True)
    embed.add_field(name="العميل", value=ctx.author.mention, inline=False)
    embed.set_footer(text="أرسل تفاصيل الطلب أو إثبات الدفع هنا.")
    await channel.send(content=ctx.author.mention, embed=embed)

    await ctx.reply(f"✅ تم فتح التذكرة: {channel.mention}")
    await send_log(ctx.guild, "🎫 فتح تذكرة", f"{ctx.author.mention} فتح تذكرة للخدمة {matched} ({amount}).")

@bot.command(name="إغلاق")
async def close_ticket(ctx):
    if not ctx.guild:
        return
    guild_key, user_key = str(ctx.guild.id), str(ctx.author.id)
    ticket_owner = next((uid for uid, cid in open_tickets.get(guild_key, {}).items() if int(cid) == ctx.channel.id), None)

    if not ticket_owner:
        return await ctx.reply("❌ هذه ليست تذكرة مسجلة.")
    if ticket_owner != user_key and not is_support(ctx.author):
        return await ctx.reply("❌ لا يمكنك إغلاق هذه التذكرة.")

    open_tickets[guild_key].pop(ticket_owner, None)
    save_tickets()
    await ctx.reply("🔒 سيتم إغلاق التذكرة خلال 3 ثوانٍ.")
    await send_log(ctx.guild, "🔒 إغلاق تذكرة", f"{ctx.author.mention} أغلق {ctx.channel.mention}.")
    await asyncio.sleep(3)
    await ctx.channel.delete(reason=f"Ticket closed by {ctx.author}")

@bot.command(name="تقييم")
async def rating(ctx, rating: int):
    if not 1 <= rating <= 5:
        return await ctx.reply("❌ التقييم يجب أن يكون من 1 إلى 5.")
    await ctx.send(f"🌟 شكراً على تقييمك {ctx.author.mention}! تقييمك: {rating}/5")

@bot.command(name="إعلان")
@commands.has_permissions(manage_guild=True)
async def announce(ctx, *, message: str):
    channel = bot.get_channel(ALLOWED_CHANNEL_ID)
    if not channel:
        return await ctx.reply("❌ لم أجد روم الطلبات.")
    await channel.send(embed=discord.Embed(title="📢 إعلان من الإدارة", description=message, color=discord.Color.gold()))
    await ctx.reply("✅ تم إرسال الإعلان.")

@bot.command(name="help")
async def help_command(ctx):
    embed = discord.Embed(title="🤖 أوامر البوت", color=discord.Color.blurple())
    embed.add_field(name="🛒 المتجر", value="!قائمة\n!طلب <الخدمة> <الكمية>", inline=False)
    embed.add_field(name="🎫 التذاكر", value="!إغلاق", inline=False)
    embed.add_field(name="⭐ التقييم", value="!تقييم <1-5>", inline=False)
    embed.add_field(name="🛡️ الإدارة", value="!إعلان <النص>", inline=False)
    await ctx.send(embed=embed)

@create_ticket.error
async def create_ticket_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.reply(f"⏳ انتظر {error.retry_after:.0f} ثانية قبل إنشاء طلب آخر.")
    elif isinstance(error, commands.BadArgument):
        await ctx.reply("❌ الاستخدام الصحيح: !طلب اسم_الخدمة الكمية")

@announce.error
async def announce_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply("❌ هذا الأمر مخصص للإدارة فقط.")

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN غير موجود في متغيرات البيئة.")

bot.run(TOKEN)
