import os
import time
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = os.getenv("PREFIX", "!")
START_TIME = time.time()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None, case_insensitive=True)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} | {bot.user.id}")
    await bot.change_presence(activity=discord.Game(name=f"{PREFIX}help"))

@bot.command(name="help")
async def help_command(ctx):
    embed = discord.Embed(title="🤖 Hhf Bot", description="بوت إدارة ومساعدة متكامل لسيرفر Discord.", color=discord.Color.blurple())
    embed.add_field(name="📌 عام", value=f"{PREFIX}ping — سرعة البوت\n{PREFIX}server — معلومات السيرفر\n{PREFIX}userinfo [@عضو] — معلومات العضو\n{PREFIX}avatar [@عضو] — صورة العضو\n{PREFIX}uptime — مدة التشغيل", inline=False)
    embed.add_field(name="🛡️ إدارة", value=f"{PREFIX}clear <عدد> — حذف رسائل\n{PREFIX}kick @عضو [سبب] — طرد عضو\n{PREFIX}ban @عضو [سبب] — حظر عضو\n{PREFIX}unban <ID> — فك حظر عضو\n{PREFIX}lock — قفل الروم\n{PREFIX}unlock — فتح الروم\n{PREFIX}slowmode <ثواني> — Slowmode", inline=False)
    embed.add_field(name="📢 أدوات", value=f"{PREFIX}say <نص> — إرسال رسالة\n{PREFIX}announce <نص> — إعلان Embed\n{PREFIX}poll <سؤال> — إنشاء تصويت", inline=False)
    embed.set_footer(text="Hhf • Management Bot")
    await ctx.send(embed=embed)

@bot.command()
async def ping(ctx):
    await ctx.send(f"Pong! {round(bot.latency * 1000)}ms")

@bot.command()
async def uptime(ctx):
    seconds = int(time.time() - START_TIME)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    await ctx.send(f"مدة التشغيل: {days}d {hours}h {minutes}m {seconds}s")

@bot.command()
async def server(ctx):
    guild = ctx.guild
    embed = discord.Embed(title=f"📊 {guild.name}", color=discord.Color.blurple())
    embed.add_field(name="👑 المالك", value=guild.owner.mention if guild.owner else "غير معروف")
    embed.add_field(name="👥 الأعضاء", value=str(guild.member_count))
    embed.add_field(name="💬 الرومات", value=str(len(guild.channels)))
    embed.add_field(name="🎭 الرتب", value=str(len(guild.roles)))
    embed.add_field(name="🆔 ID", value=str(guild.id), inline=False)
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    await ctx.send(embed=embed)

@bot.command()
async def userinfo(ctx, member: discord.Member = None):
    member = member or ctx.author
    embed = discord.Embed(title=f"👤 {member}", color=member.color)
    embed.add_field(name="🆔 ID", value=str(member.id), inline=False)
    embed.add_field(name="📅 انضم للسيرفر", value=discord.utils.format_dt(member.joined_at, "F") if member.joined_at else "غير معروف", inline=False)
    embed.add_field(name="🎭 أعلى رتبة", value=member.top_role.mention, inline=False)
    embed.set_thumbnail(url=member.display_avatar.url)
    await ctx.send(embed=embed)

@bot.command()
async def avatar(ctx, member: discord.Member = None):
    member = member or ctx.author
    embed = discord.Embed(title=f"🖼️ Avatar — {member}", color=discord.Color.blurple())
    embed.set_image(url=member.display_avatar.url)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    if amount < 1 or amount > 100:
        return await ctx.reply("❌ العدد يجب أن يكون بين 1 و100.")
    deleted = await ctx.channel.purge(limit=amount + 1)
    msg = await ctx.send(f"تم حذف {len(deleted) - 1} رسالة.")
    await msg.delete(delay=3)

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="بدون سبب"):
    if member == ctx.author or member == ctx.guild.owner:
        return await ctx.reply("❌ لا يمكنك طرد هذا العضو.")
    await member.kick(reason=reason)
    await ctx.send(f"👢 تم طرد {member.mention}\nالسبب: {reason}")

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="بدون سبب"):
    if member == ctx.author or member == ctx.guild.owner:
        return await ctx.reply("❌ لا يمكنك حظر هذا العضو.")
    await member.ban(reason=reason)
    await ctx.send(f"🔨 تم حظر {member.mention}\nالسبب: {reason}")

@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: int):
    try:
        user = await bot.fetch_user(user_id)
        await ctx.guild.unban(user)
        await ctx.send(f"تم فك حظر {user}.")
    except discord.NotFound:
        await ctx.reply("❌ لم أجد هذا العضو ضمن قائمة المحظورين.")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def lock(ctx):
    overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
    overwrite.send_messages = False
    await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
    await ctx.send("🔒 تم قفل الروم.")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def unlock(ctx):
    overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
    overwrite.send_messages = None
    await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
    await ctx.send("🔓 تم فتح الروم.")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def slowmode(ctx, seconds: int):
    if seconds < 0 or seconds > 21600:
        return await ctx.reply("❌ استخدم رقمًا بين 0 و21600.")
    await ctx.channel.edit(slowmode_delay=seconds)
    await ctx.send(f"🐢 تم ضبط Slowmode على {seconds} ثانية.")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def say(ctx, *, message: str):
    await ctx.message.delete()
    await ctx.send(message)

@bot.command()
@commands.has_permissions(manage_guild=True)
async def announce(ctx, *, message: str):
    embed = discord.Embed(title="📢 إعلان", description=message, color=discord.Color.gold())
    embed.set_footer(text=f"بواسطة {ctx.author}")
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_messages=True)
async def poll(ctx, *, question: str):
    embed = discord.Embed(title="📊 تصويت", description=question, color=discord.Color.blurple())
    embed.set_footer(text=f"بواسطة {ctx.author}")
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("👍")
    await msg.add_reaction("👎")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingPermissions):
        return await ctx.reply("❌ هذا الأمر يحتاج صلاحيات مناسبة.")
    if isinstance(error, commands.MissingRequiredArgument):
        return await ctx.reply(f"❌ يوجد متغير ناقص. استخدم {PREFIX}help.")
    if isinstance(error, commands.BadArgument):
        return await ctx.reply("❌ تأكد من كتابة البيانات بالطريقة الصحيحة.")
    if isinstance(error, commands.CommandInvokeError):
        print(f"Command error: {error.original}")
        return await ctx.reply("❌ حدث خطأ أثناء تنفيذ الأمر.")

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN غير موجود في متغيرات البيئة.")

bot.run(TOKEN)
