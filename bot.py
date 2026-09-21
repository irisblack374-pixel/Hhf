import os
import json
import time
import asyncio
import logging
from pathlib import Path
from datetime import timedelta
from collections import defaultdict, deque

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = os.getenv("PREFIX", "!")
START_TIME = time.time()

DATA = Path("data")
DATA.mkdir(exist_ok=True)

CONFIG_FILE = DATA / "config.json"
WARNS_FILE = DATA / "warnings.json"
TICKETS_FILE = DATA / "tickets.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(
    command_prefix=PREFIX,
    intents=intents,
    help_command=None,
    case_insensitive=True,
)

spam_cache = defaultdict(lambda: deque(maxlen=12))


def load_json(path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def save_json(path, data):
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


configs = load_json(CONFIG_FILE, {})
warnings_db = load_json(WARNS_FILE, {})
tickets_db = load_json(TICKETS_FILE, {})


def cfg(guild):
    gid = str(guild.id)
    if gid not in configs:
        configs[gid] = {
            "logs": 0,
            "welcome": 0,
            "suggestions": 0,
            "ticket_category": 0,
            "welcome_text": "أهلًا بك {member} في {server}! 🎉",
            "automod": True,
            "antilink": False,
            "antispam": True,
        }
        save_json(CONFIG_FILE, configs)
    return configs[gid]


def manager(member):
    p = member.guild_permissions
    return p.administrator or p.manage_guild or p.manage_messages


def embed(title, description="", color=None):
    e = discord.Embed(
        title=title,
        description=description,
        color=color or discord.Color.blurple(),
        timestamp=discord.utils.utcnow(),
    )
    e.set_footer(text="Hhf • Management System")
    return e


async def ok(ctx, text):
    await ctx.send(embed=embed("✅ تم", text, discord.Color.green()))


async def error(ctx, text):
    await ctx.reply(
        embed=embed("❌ تعذر تنفيذ الأمر", text, discord.Color.red()),
        mention_author=False,
    )


async def log(guild, title, description, color=None):
    channel_id = int(cfg(guild).get("logs", 0) or 0)
    channel = guild.get_channel(channel_id) if channel_id else None
    if not channel:
        return
    try:
        await channel.send(embed=embed(title, description[:4000], color))
    except (discord.Forbidden, discord.HTTPException):
        pass


def ticket_owner(guild, channel_id):
    for uid, cid in tickets_db.get(str(guild.id), {}).items():
        if int(cid) == int(channel_id):
            return int(uid)
    return None


class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="إغلاق التذكرة",
        emoji="🔒",
        style=discord.ButtonStyle.danger,
        custom_id="hhf_close_ticket",
    )
    async def close(self, interaction, button):
        guild = interaction.guild
        channel = interaction.channel

        if not guild or not isinstance(channel, discord.TextChannel):
            return await interaction.response.send_message(
                "❌ لا يمكن استخدام الزر هنا.",
                ephemeral=True,
            )

        owner = ticket_owner(guild, channel.id)
        if owner is None:
            return await interaction.response.send_message(
                "❌ هذه ليست تذكرة مسجلة.",
                ephemeral=True,
            )

        if interaction.user.id != owner and not manager(interaction.user):
            return await interaction.response.send_message(
                "❌ لا تملك صلاحية إغلاق هذه التذكرة.",
                ephemeral=True,
            )

        await interaction.response.send_message(
            "🔒 سيتم إغلاق التذكرة خلال 3 ثوانٍ."
        )

        tickets_db.get(str(guild.id), {}).pop(str(owner), None)
        save_json(TICKETS_FILE, tickets_db)

        await log(
            guild,
            "🎫 Ticket Closed",
            f"{interaction.user.mention} أغلق {channel.mention}.",
            discord.Color.orange(),
        )

        await asyncio.sleep(3)

        try:
            await channel.delete(reason=f"Ticket closed by {interaction.user}")
        except discord.HTTPException:
            pass


class HelpSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="عام",
                emoji="📌",
                value="general",
                description="معلومات وأدوات عامة",
            ),
            discord.SelectOption(
                label="إدارة",
                emoji="🛡️",
                value="moderation",
                description="العقوبات والإدارة",
            ),
            discord.SelectOption(
                label="حماية",
                emoji="🔐",
                value="security",
                description="AutoMod و Anti-Link و Anti-Spam",
            ),
            discord.SelectOption(
                label="تذاكر",
                emoji="🎫",
                value="tickets",
                description="نظام الدعم والتذاكر",
            ),
            discord.SelectOption(
                label="إعدادات",
                emoji="⚙️",
                value="settings",
                description="إعدادات السيرفر",
            ),
            discord.SelectOption(
                label="أدوات",
                emoji="🔧",
                value="tools",
                description="أدوات الإدارة والمجتمع",
            ),
        ]
        super().__init__(
            placeholder="اختر قسم الأوامر...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction):
        pages = {
            "general": (
                "📌 الأوامر العامة",
                f"{PREFIX}ping\n{PREFIX}uptime\n{PREFIX}botinfo\n"
                f"{PREFIX}server\n{PREFIX}userinfo [@عضو]\n"
                f"{PREFIX}avatar [@عضو]\n{PREFIX}rolelist\n"
                f"{PREFIX}channels\n{PREFIX}icon",
            ),
            "moderation": (
                "🛡️ الإدارة",
                f"{PREFIX}clear <عدد>\n{PREFIX}kick @عضو [سبب]\n"
                f"{PREFIX}ban @عضو [سبب]\n{PREFIX}unban <ID>\n"
                f"{PREFIX}timeout @عضو <دقائق> [سبب]\n"
                f"{PREFIX}untimeout @عضو\n{PREFIX}warn @عضو [سبب]\n"
                f"{PREFIX}warnings [@عضو]\n{PREFIX}unwarn @عضو <رقم>\n"
                f"{PREFIX}lock\n{PREFIX}unlock\n{PREFIX}slowmode <ثواني>",
            ),
            "security": (
                "🔐 الحماية",
                f"{PREFIX}automod on/off\n"
                f"{PREFIX}antilink on/off\n"
                f"{PREFIX}antispam on/off",
            ),
            "tickets": (
                "🎫 التذاكر",
                f"{PREFIX}ticket\n"
                "داخل التذكرة يوجد زر إغلاق مباشر.",
            ),
            "settings": (
                "⚙️ الإعدادات",
                f"{PREFIX}setlog #روم\n"
                f"{PREFIX}setwelcome #روم\n"
                f"{PREFIX}welcome_msg <النص>\n"
                f"{PREFIX}setsuggest #روم\n"
                f"{PREFIX}setcategory #تصنيف\n"
                f"{PREFIX}config",
            ),
            "tools": (
                "🔧 الأدوات",
                f"{PREFIX}say <النص>\n{PREFIX}announce <النص>\n"
                f"{PREFIX}poll <السؤال>\n{PREFIX}suggest <الاقتراح>\n"
                f"{PREFIX}createchannel <الاسم>\n{PREFIX}deletechannel\n"
                f"{PREFIX}rolelist\n{PREFIX}channels\n{PREFIX}icon\n"
                f"{PREFIX}serverstats",
            ),
        }

        title, text = pages[self.values[0]]
        await interaction.response.edit_message(
            embed=embed(title, text),
            view=self.view,
        )


class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(HelpSelect())


@bot.event
async def on_ready():
    logging.info("Logged in as %s (%s)", bot.user, bot.user.id)
    bot.add_view(TicketView())

    if not status_loop.is_running():
        status_loop.start()

    await bot.change_presence(
        activity=discord.Game(name=f"{PREFIX}help • Hhf")
    )


@tasks.loop(minutes=5)
async def status_loop():
    await bot.change_presence(
        activity=discord.Game(
            name=f"{PREFIX}help • {len(bot.guilds)} servers"
        )
    )


@bot.event
async def on_member_join(member):
    config = cfg(member.guild)
    channel_id = int(config.get("welcome", 0) or 0)
    channel = member.guild.get_channel(channel_id) if channel_id else None

    if channel:
        text = config.get("welcome_text", "أهلًا بك {member} في {server}! 🎉")
        text = text.replace("{member}", member.mention)
        text = text.replace("{server}", member.guild.name)

        e = embed("👋 عضو جديد", text, discord.Color.green())
        e.set_thumbnail(url=member.display_avatar.url)

        try:
            await channel.send(embed=e)
        except discord.HTTPException:
            pass

    await log(
        member.guild,
        "👋 دخول عضو",
        f"{member.mention} دخل السيرفر.",
        discord.Color.green(),
    )


@bot.event
async def on_member_remove(member):
    await log(
        member.guild,
        "🚪 خروج عضو",
        f"{member} غادر السيرفر.",
        discord.Color.orange(),
    )


@bot.event
async def on_message_delete(message):
    if not message.guild or message.author.bot:
        return

    text = message.content or "لا يوجد نص متاح."
    await log(
        message.guild,
        "🗑️ حذف رسالة",
        f"**العضو:** {message.author.mention}\n"
        f"**الروم:** {message.channel.mention}\n"
        f"**المحتوى:** {text[:1500]}",
        discord.Color.orange(),
    )


@bot.event
async def on_message_edit(before, after):
    if not before.guild or before.author.bot:
        return
    if before.content == after.content:
        return

    await log(
        before.guild,
        "✏️ تعديل رسالة",
        f"**العضو:** {before.author.mention}\n"
        f"**الروم:** {before.channel.mention}\n"
        f"**قبل:** {before.content[:700]}\n"
        f"**بعد:** {after.content[:700]}",
        discord.Color.gold(),
    )


@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    config = cfg(message.guild)

    if config.get("automod") and not manager(message.author):
        content = message.content.lower()

        if config.get("antilink") and any(
            x in content
            for x in ("http://", "https://", "discord.gg/", "www.")
        ):
            try:
                await message.delete()
                await message.channel.send(
                    f"{message.author.mention} ❌ الروابط غير مسموحة.",
                    delete_after=5,
                )
            except discord.HTTPException:
                pass
            return

        if config.get("antispam"):
            now = time.monotonic()
            queue = spam_cache[message.author.id]
            queue.append(now)

            while queue and now - queue[0] > 6:
                queue.popleft()

            if len(queue) >= 7:
                queue.clear()
                try:
                    await message.author.timeout(
                        timedelta(seconds=10),
                        reason="Hhf Anti-Spam",
                    )
                    await message.channel.send(
                        f"🚫 تم تقييد {message.author.mention} لمدة 10 ثوانٍ بسبب السبام.",
                        delete_after=6,
                    )
                except (discord.Forbidden, discord.HTTPException):
                    pass
                return

    await bot.process_commands(message)


@bot.command(name="help")
async def help_command(ctx):
    e = embed(
        "🤖 Hhf • مركز المساعدة",
        "اختر القسم من القائمة لعرض الأوامر.",
    )
    e.add_field(
        name="✨ النظام",
        value=(
            "إدارة • حماية • Tickets • Logs • ترحيب • اقتراحات\n"
            "إعدادات محفوظة لكل سيرفر"
        ),
        inline=False,
    )
    e.add_field(
        name="📖 مثال",
        value=f"اكتب {PREFIX}ping للتجربة.",
        inline=False,
    )
    await ctx.send(embed=e, view=HelpView())


@bot.command()
async def ping(ctx):
    ms = round(bot.latency * 1000)
    await ctx.send(
        embed=embed(
            "🏓 Pong!",
            f"Latency: **{ms}ms**",
            discord.Color.green(),
        )
    )


@bot.command()
async def uptime(ctx):
    total = int(time.time() - START_TIME)
    days, total = divmod(total, 86400)
    hours, total = divmod(total, 3600)
    minutes, seconds = divmod(total, 60)

    await ctx.send(
        embed=embed(
            "⏱️ Uptime",
            f"**{days}d {hours}h {minutes}m {seconds}s**",
        )
    )


@bot.command()
async def botinfo(ctx):
    e = embed("🤖 Hhf • معلومات البوت")
    e.add_field(name="🌐 السيرفرات", value=str(len(bot.guilds)))
    e.add_field(name="👥 المستخدمون", value=str(len(bot.users)))
    e.add_field(name="📚 discord.py", value=discord.__version__)
    e.add_field(name="⚡ Prefix", value=PREFIX)
    await ctx.send(embed=e)


@bot.command()
async def server(ctx):
    g = ctx.guild
    e = embed("📊 معلومات السيرفر", g.name)
    e.add_field(name="👥 الأعضاء", value=str(g.member_count))
    e.add_field(name="💬 الرومات", value=str(len(g.channels)))
    e.add_field(name="🎭 الرتب", value=str(len(g.roles)))
    e.add_field(name="🆔 ID", value=str(g.id))
    if g.icon:
        e.set_thumbnail(url=g.icon.url)
    await ctx.send(embed=e)


@bot.command()
async def userinfo(ctx, member: discord.Member = None):
    member = member or ctx.author
    e = embed("👤 معلومات العضو", str(member))
    e.set_thumbnail(url=member.display_avatar.url)
    e.add_field(name="🆔 ID", value=str(member.id), inline=False)
    e.add_field(
        name="📅 إنشاء الحساب",
        value=discord.utils.format_dt(member.created_at, "F"),
        inline=False,
    )
    e.add_field(name="🎭 أعلى رتبة", value=member.top_role.mention, inline=False)
    await ctx.send(embed=e)


@bot.command()
async def avatar(ctx, member: discord.Member = None):
    member = member or ctx.author
    e = embed("🖼️ الصورة الشخصية", str(member))
    e.set_image(url=member.display_avatar.url)
    await ctx.send(embed=e)


@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    if not 1 <= amount <= 100:
        return await error(ctx, "استخدم رقمًا من 1 إلى 100.")

    deleted = await ctx.channel.purge(limit=amount + 1)
    count = max(len(deleted) - 1, 0)

    await ctx.send(
        embed=embed(
            "🧹 تم التنظيف",
            f"تم حذف **{count}** رسالة.",
            discord.Color.green(),
        ),
        delete_after=5,
    )

    await log(
        ctx.guild,
        "🧹 Clear",
        f"{ctx.author.mention} حذف {count} رسالة في {ctx.channel.mention}.",
    )


@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="بدون سبب"):
    if member == ctx.author or member == ctx.guild.owner:
        return await error(ctx, "لا يمكنك تنفيذ هذا الإجراء على هذا العضو.")

    await member.kick(reason=reason)

    await ctx.send(
        embed=embed(
            "👢 تم الطرد",
            f"**العضو:** {member.mention}\n**السبب:** {reason}",
            discord.Color.orange(),
        )
    )

    await log(
        ctx.guild,
        "👢 Kick",
        f"{ctx.author.mention} طرد {member.mention}.\nالسبب: {reason}",
        discord.Color.orange(),
    )


@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="بدون سبب"):
    if member == ctx.author or member == ctx.guild.owner:
        return await error(ctx, "لا يمكنك تنفيذ هذا الإجراء على هذا العضو.")

    await member.ban(reason=reason, delete_message_seconds=0)

    await ctx.send(
        embed=embed(
            "🔨 تم الحظر",
            f"**العضو:** {member.mention}\n**السبب:** {reason}",
            discord.Color.red(),
        )
    )

    await log(
        ctx.guild,
        "🔨 Ban",
        f"{ctx.author.mention} حظر {member.mention}.\nالسبب: {reason}",
        discord.Color.red(),
    )


@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: int):
    try:
        user = await bot.fetch_user(user_id)
        await ctx.guild.unban(user)
    except discord.NotFound:
        return await error(ctx, "المستخدم غير موجود في قائمة المحظورين.")
    except discord.Forbidden:
        return await error(ctx, "البوت لا يملك صلاحية فك الحظر.")

    await ctx.send(
        embed=embed(
            "🔓 تم فك الحظر",
            f"تم فك حظر **{user}**.",
            discord.Color.green(),
        )
    )


@bot.command()
@commands.has_permissions(moderate_members=True)
async def timeout(
    ctx,
    member: discord.Member,
    minutes: int,
    *,
    reason="بدون سبب",
):
    if not 1 <= minutes <= 40320:
        return await error(ctx, "المدة من 1 إلى 40320 دقيقة.")

    await member.timeout(timedelta(minutes=minutes), reason=reason)

    await ctx.send(
        embed=embed(
            "⏳ تم التقييد",
            f"**العضو:** {member.mention}\n"
            f"**المدة:** {minutes} دقيقة\n"
            f"**السبب:** {reason}",
            discord.Color.orange(),
        )
    )


@bot.command()
@commands.has_permissions(moderate_members=True)
async def untimeout(ctx, member: discord.Member):
    await member.timeout(None)
    await ctx.send(
        embed=embed(
            "✅ انتهى التقييد",
            f"تمت إزالة Timeout عن {member.mention}.",
            discord.Color.green(),
        )
    )


@bot.command()
@commands.has_permissions(manage_channels=True)
async def lock(ctx):
    overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
    overwrite.send_messages = False
    await ctx.channel.set_permissions(
        ctx.guild.default_role,
        overwrite=overwrite,
    )
    await ok(ctx, "تم قفل الروم أمام الأعضاء.")


@bot.command()
@commands.has_permissions(manage_channels=True)
async def unlock(ctx):
    overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
    overwrite.send_messages = None
    await ctx.channel.set_permissions(
        ctx.guild.default_role,
        overwrite=overwrite,
    )
    await ok(ctx, "تم فتح الروم أمام الأعضاء.")


@bot.command()
@commands.has_permissions(manage_channels=True)
async def slowmode(ctx, seconds: int):
    if not 0 <= seconds <= 21600:
        return await error(ctx, "استخدم 0 إلى 21600 ثانية.")

    await ctx.channel.edit(slowmode_delay=seconds)
    await ok(ctx, f"تم ضبط Slowmode على **{seconds} ثانية**.")


@bot.command()
@commands.has_permissions(manage_messages=True)
async def say(ctx, *, text):
    try:
        await ctx.message.delete()
    except discord.HTTPException:
        pass
    await ctx.send(text)


@bot.command()
@commands.has_permissions(manage_guild=True)
async def announce(ctx, *, text):
    e = embed("📢 إعلان", text, discord.Color.gold())
    e.set_author(
        name=str(ctx.author),
        icon_url=ctx.author.display_avatar.url,
    )
    await ctx.send(embed=e)


@bot.command()
@commands.has_permissions(manage_messages=True)
async def poll(ctx, *, question):
    e = embed(
        "📊 تصويت",
        f"**{question}**\n\n👍 موافق\n👎 غير موافق",
    )
    message = await ctx.send(embed=e)
    await message.add_reaction("👍")
    await message.add_reaction("👎")


@bot.command()
@commands.has_permissions(manage_messages=True)
async def warn(ctx, member: discord.Member, *, reason="بدون سبب"):
    guild_data = warnings_db.setdefault(str(ctx.guild.id), {})
    entries = guild_data.setdefault(str(member.id), [])

    entries.append(
        {
            "reason": reason,
            "by": ctx.author.id,
            "time": int(time.time()),
        }
    )
    save_json(WARNS_FILE, warnings_db)

    e = embed(
        "⚠️ تحذير",
        f"**العضو:** {member.mention}\n"
        f"**السبب:** {reason}\n"
        f"**إجمالي التحذيرات:** {len(entries)}",
        discord.Color.orange(),
    )
    await ctx.send(embed=e)

    await log(
        ctx.guild,
        "⚠️ Warning",
        f"{ctx.author.mention} حذر {member.mention}.\nالسبب: {reason}",
        discord.Color.orange(),
    )


@bot.command()
@commands.has_permissions(manage_messages=True)
async def warnings(ctx, member: discord.Member = None):
    member = member or ctx.author
    entries = warnings_db.get(str(ctx.guild.id), {}).get(
        str(member.id),
        [],
    )

    if not entries:
        return await ctx.send(
            embed=embed(
                "📋 سجل التحذيرات",
                f"لا توجد تحذيرات على {member.mention}.",
                discord.Color.green(),
            )
        )

    lines = []
    for index, item in enumerate(entries[-10:], 1):
        lines.append(
            f"**{index}.** {item.get('reason', 'بدون سبب')}"
        )

    e = embed("📋 سجل التحذيرات", "\n".join(lines), discord.Color.orange())
    e.set_author(
        name=str(member),
        icon_url=member.display_avatar.url,
    )
    await ctx.send(embed=e)


@bot.command()
@commands.has_permissions(manage_messages=True)
async def unwarn(ctx, member: discord.Member, number: int):
    entries = warnings_db.get(str(ctx.guild.id), {}).get(
        str(member.id),
        [],
    )

    if not 1 <= number <= len(entries):
        return await error(ctx, "رقم التحذير غير صحيح.")

    removed = entries.pop(number - 1)
    save_json(WARNS_FILE, warnings_db)

    await ok(
        ctx,
        f"تم حذف التحذير: **{removed.get('reason', 'بدون سبب')}**",
    )


@bot.command()
@commands.has_permissions(manage_guild=True)
async def setlog(ctx, channel: discord.TextChannel):
    cfg(ctx.guild)["logs"] = channel.id
    save_json(CONFIG_FILE, configs)
    await ok(ctx, f"تم تعيين {channel.mention} كروم Logs.")


@bot.command()
@commands.has_permissions(manage_guild=True)
async def setwelcome(ctx, channel: discord.TextChannel):
    cfg(ctx.guild)["welcome"] = channel.id
    save_json(CONFIG_FILE, configs)
    await ok(ctx, f"تم تعيين {channel.mention} كروم ترحيب.")


@bot.command()
@commands.has_permissions(manage_guild=True)
async def welcome_msg(ctx, *, text):
    if len(text) > 1000:
        return await error(ctx, "رسالة الترحيب طويلة جدًا.")

    cfg(ctx.guild)["welcome_text"] = text
    save_json(CONFIG_FILE, configs)
    await ok(ctx, "تم حفظ رسالة الترحيب.")


@bot.command()
@commands.has_permissions(manage_guild=True)
async def setsuggest(ctx, channel: discord.TextChannel):
    cfg(ctx.guild)["suggestions"] = channel.id
    save_json(CONFIG_FILE, configs)
    await ok(ctx, f"تم تعيين {channel.mention} كروم اقتراحات.")


@bot.command()
@commands.has_permissions(manage_guild=True)
async def setcategory(ctx, category: discord.CategoryChannel):
    cfg(ctx.guild)["ticket_category"] = category.id
    save_json(CONFIG_FILE, configs)
    await ok(ctx, f"تم تعيين تصنيف **{category.name}** للتذاكر.")


@bot.command()
@commands.has_permissions(manage_guild=True)
async def automod(ctx, mode: str):
    mode = mode.lower()
    if mode not in ("on", "off"):
        return await error(ctx, "الاستخدام: !automod on أو !automod off")

    cfg(ctx.guild)["automod"] = mode == "on"
    save_json(CONFIG_FILE, configs)
    await ok(ctx, f"AutoMod: **{'مفعل' if mode == 'on' else 'متوقف'}**")


@bot.command()
@commands.has_permissions(manage_guild=True)
async def antilink(ctx, mode: str):
    mode = mode.lower()
    if mode not in ("on", "off"):
        return await error(ctx, "الاستخدام: !antilink on أو !antilink off")

    cfg(ctx.guild)["antilink"] = mode == "on"
    save_json(CONFIG_FILE, configs)
    await ok(ctx, f"Anti-Link: **{'مفعل' if mode == 'on' else 'متوقف'}**")


@bot.command()
@commands.has_permissions(manage_guild=True)
async def antispam(ctx, mode: str):
    mode = mode.lower()
    if mode not in ("on", "off"):
        return await error(ctx, "الاستخدام: !antispam on أو !antispam off")

    cfg(ctx.guild)["antispam"] = mode == "on"
    save_json(CONFIG_FILE, configs)
    await ok(ctx, f"Anti-Spam: **{'مفعل' if mode == 'on' else 'متوقف'}**")


@bot.command()
async def ticket(ctx):
    guild = ctx.guild
    gid = str(guild.id)
    uid = str(ctx.author.id)

    old = tickets_db.get(gid, {}).get(uid)
    if old and guild.get_channel(int(old)):
        return await error(ctx, f"لديك تذكرة مفتوحة بالفعل: <#{old}>")

    category_id = int(cfg(guild).get("ticket_category", 0) or 0)
    category = guild.get_channel(category_id) if category_id else None
    if not isinstance(category, discord.CategoryChannel):
        category = None

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(
            view_channel=False
        ),
        ctx.author: discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            read_message_history=True,
            attach_files=True,
        ),
        guild.me: discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            read_message_history=True,
            manage_channels=True,
        ),
    }

    channel = await guild.create_text_channel(
        f"ticket-{ctx.author.name[:18]}",
        category=category,
        overwrites=overwrites,
        reason=f"Ticket created by {ctx.author}",
    )

    tickets_db.setdefault(gid, {})[uid] = channel.id
    save_json(TICKETS_FILE, tickets_db)

    e = embed(
        "🎫 مركز الدعم",
        "أهلًا بك! اكتب تفاصيل طلبك هنا وسيتم التعامل معه من فريق الإدارة.",
    )
    e.add_field(
        name="🔒 الإغلاق",
        value="استخدم زر إغلاق التذكرة عند الانتهاء.",
        inline=False,
    )
    e.set_footer(text=f"Ticket Owner: {ctx.author}")

    await channel.send(
        content=ctx.author.mention,
        embed=e,
        view=TicketView(),
    )

    await ctx.reply(
        embed=embed(
            "🎫 تم إنشاء التذكرة",
            f"تذكرتك: {channel.mention}",
            discord.Color.green(),
        ),
        mention_author=False,
    )

    await log(
        guild,
        "🎫 Ticket Created",
        f"{ctx.author.mention} أنشأ {channel.mention}.",
        discord.Color.green(),
    )


@bot.command()
async def close(ctx):
    owner = ticket_owner(ctx.guild, ctx.channel.id)

    if owner is None:
        return await error(ctx, "هذا الروم ليس تذكرة مسجلة.")

    if ctx.author.id != owner and not manager(ctx.author):
        return await error(ctx, "لا يمكنك إغلاق هذه التذكرة.")

    tickets_db.get(str(ctx.guild.id), {}).pop(str(owner), None)
    save_json(TICKETS_FILE, tickets_db)

    await ctx.send("🔒 سيتم إغلاق التذكرة خلال 3 ثوانٍ.")
    await asyncio.sleep(3)

    try:
        await ctx.channel.delete(reason=f"Ticket closed by {ctx.author}")
    except discord.HTTPException:
        pass


@bot.command()
async def suggest(ctx, *, text):
    channel_id = int(cfg(ctx.guild).get("suggestions", 0) or 0)
    channel = ctx.guild.get_channel(channel_id) if channel_id else None

    if not channel:
        return await error(
            ctx,
            f"عيّن روم الاقتراحات أولًا باستخدام {PREFIX}setsuggest #الروم",
        )

    e = embed("💡 اقتراح جديد", text[:2000])
    e.set_author(
        name=str(ctx.author),
        icon_url=ctx.author.display_avatar.url,
    )

    message = await channel.send(embed=e)
    await message.add_reaction("👍")
    await message.add_reaction("👎")

    await ok(ctx, "تم إرسال اقتراحك.")


@bot.command()
@commands.has_permissions(manage_channels=True)
async def createchannel(ctx, *, name):
    name = name.strip().replace(" ", "-")[:90]
    channel = await ctx.guild.create_text_channel(
        name,
        reason=f"Created by {ctx.author}",
    )
    await ok(ctx, f"تم إنشاء {channel.mention}.")


@bot.command()
@commands.has_permissions(manage_channels=True)
async def deletechannel(ctx):
    await ctx.channel.delete(reason=f"Deleted by {ctx.author}")


@bot.command()
async def rolelist(ctx):
    roles = [
        role.mention
        for role in reversed(ctx.guild.roles)
        if role != ctx.guild.default_role
    ]
    text = ", ".join(roles) if roles else "لا توجد رتب إضافية."
    await ctx.send(embed=embed("🎭 رتب السيرفر", text[:4000]))


@bot.command()
async def channels(ctx):
    text = (
        f"💬 Text: **{len(ctx.guild.text_channels)}**\n"
        f"🔊 Voice: **{len(ctx.guild.voice_channels)}**\n"
        f"📁 Categories: **{len(ctx.guild.categories)}**"
    )
    await ctx.send(embed=embed("📚 إحصائيات الرومات", text))


@bot.command()
async def icon(ctx):
    if not ctx.guild.icon:
        return await error(ctx, "السيرفر لا يملك صورة.")

    e = embed("🖼️ أيقونة السيرفر", ctx.guild.name)
    e.set_image(url=ctx.guild.icon.url)
    await ctx.send(embed=e)


@bot.command()
@commands.has_permissions(manage_guild=True)
async def serverstats(ctx):
    humans = sum(not member.bot for member in ctx.guild.members)
    bots = sum(member.bot for member in ctx.guild.members)

    e = embed("📈 إحصائيات السيرفر")
    e.add_field(name="👤 Humans", value=str(humans))
    e.add_field(name="🤖 Bots", value=str(bots))
    e.add_field(name="👥 Total", value=str(ctx.guild.member_count))
    e.add_field(name="💬 Text", value=str(len(ctx.guild.text_channels)))
    e.add_field(name="🔊 Voice", value=str(len(ctx.guild.voice_channels)))
    e.add_field(name="🎭 Roles", value=str(len(ctx.guild.roles)))
    await ctx.send(embed=e)


@bot.command()
@commands.has_permissions(manage_guild=True)
async def config(ctx):
    settings = cfg(ctx.guild)

    def channel_text(key):
        value = int(settings.get(key, 0) or 0)
        return f"<#{value}>" if value else "غير معين"

    e = embed(
        "⚙️ إعدادات Hhf",
        "هذه هي الإعدادات الحالية للسيرفر.",
    )
    e.add_field(name="📋 Logs", value=channel_text("logs"))
    e.add_field(name="👋 Welcome", value=channel_text("welcome"))
    e.add_field(name="💡 Suggestions", value=channel_text("suggestions"))
    e.add_field(name="🎫 Ticket Category", value=channel_text("ticket_category"))
    e.add_field(
        name="🛡️ AutoMod",
        value="🟢 ON" if settings["automod"] else "🔴 OFF",
    )
    e.add_field(
        name="🔗 Anti-Link",
        value="🟢 ON" if settings["antilink"] else "🔴 OFF",
    )
    e.add_field(
        name="🚫 Anti-Spam",
        value="🟢 ON" if settings["antispam"] else "🔴 OFF",
    )
    await ctx.send(embed=e)


@bot.event
async def on_command_error(ctx, exc):
    if isinstance(exc, commands.CommandNotFound):
        return

    if isinstance(exc, commands.MissingPermissions):
        return await error(ctx, "لا تملك صلاحية استخدام هذا الأمر.")

    if isinstance(exc, commands.BotMissingPermissions):
        return await error(ctx, "البوت لا يملك إحدى الصلاحيات المطلوبة.")

    if isinstance(exc, commands.MissingRequiredArgument):
        return await error(ctx, f"هناك متغير ناقص. استخدم {PREFIX}help")

    if isinstance(exc, commands.BadArgument):
        return await error(
            ctx,
            "أحد المدخلات غير صحيح. تأكد من المنشن أو الرقم أو الروم.",
        )

    if isinstance(exc, discord.Forbidden):
        return await error(
            ctx,
            "Discord رفض العملية بسبب الصلاحيات أو ترتيب الرتب.",
        )

    logging.exception("Unhandled command error", exc_info=exc)

    try:
        await error(ctx, "حدث خطأ غير متوقع أثناء تنفيذ الأمر.")
    except discord.HTTPException:
        pass


if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN غير موجود في متغيرات البيئة.")

bot.run(TOKEN)
