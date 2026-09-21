import re
import time
from collections import defaultdict, deque
from datetime import timedelta

import discord
from discord.ext import commands


DEFAULT_BAD_WORDS = {
    "idiot",
    "stupid",
    "moron",
}

URL_RE = re.compile(r"(https?://|www\.|discord\.gg/)", re.I)


class SecurityCog(commands.Cog):
    """Extra server protection: insults, spam, suspicious joins and raid detection."""

    def __init__(self, bot):
        self.bot = bot
        self.join_cache = defaultdict(lambda: deque())
        self.msg_cache = defaultdict(lambda: deque(maxlen=15))
        self.strikes = defaultdict(lambda: defaultdict(int))

    def cfg(self, guild):
        if hasattr(self.bot, "cfg"):
            return self.bot.cfg(guild)
        return {}

    def is_manager(self, member):
        p = member.guild_permissions
        return p.administrator or p.manage_guild or p.manage_messages

    async def send_log(self, guild, title, description, color=discord.Color.orange()):
        if hasattr(self.bot, "log"):
            await self.bot.log(guild, title, description, color)

    async def punish(self, message, reason):
        member = message.author
        key = (message.guild.id, member.id)
        self.strikes[key][reason] += 1
        count = self.strikes[key][reason]

        try:
            await message.delete()
        except (discord.Forbidden, discord.NotFound, discord.HTTPException):
            pass

        if count >= 3:
            try:
                await member.timeout(
                    timedelta(minutes=10),
                    reason=f"Hhf Security: {reason}",
                )
                action = "Timeout 10 دقائق"
            except (discord.Forbidden, discord.HTTPException):
                action = "تم حذف الرسالة فقط"
        else:
            action = "تحذير"

        try:
            await message.channel.send(
                f"{member.mention} ⚠️ تم اتخاذ إجراء بسبب مخالفة الحماية ({action}).",
                delete_after=5,
            )
        except discord.HTTPException:
            pass

        await self.send_log(
            message.guild,
            "🛡️ Security Action",
            f"**العضو:** {member.mention}\n"
            f"**السبب:** {reason}\n"
            f"**المخالفات:** {count}\n"
            f"**الإجراء:** {action}",
            discord.Color.red(),
        )

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.guild or message.author.bot:
            return

        member = message.author
        if self.is_manager(member):
            return

        config = self.cfg(message.guild)
        if not config.get("security", True):
            return

        content = message.content.casefold()

        # Configurable insult filter. The default list is intentionally small;
        # server owners can extend it through the security settings command.
        words = set(config.get("bad_words", DEFAULT_BAD_WORDS))
        normalized = re.sub(r"[^\w\s]", " ", content)
        if any(re.search(r"(?<!\w)" + re.escape(word.casefold()) + r"(?!\w)", normalized)
               for word in words if word):
            await self.punish(message, "لغة مسيئة")
            return

        if config.get("security_antilink", False) and URL_RE.search(content):
            await self.punish(message, "رابط غير مسموح")
            return

        if config.get("security_antispam", True):
            now = time.monotonic()
            cache = self.msg_cache[(message.guild.id, member.id)]
            cache.append(now)
            while cache and now - cache[0] > 8:
                cache.popleft()

            if len(cache) >= 8:
                cache.clear()
                try:
                    await member.timeout(
                        timedelta(seconds=30),
                        reason="Hhf Security: message spam",
                    )
                except (discord.Forbidden, discord.HTTPException):
                    pass
                try:
                    await message.delete()
                except (discord.Forbidden, discord.NotFound, discord.HTTPException):
                    pass
                await self.send_log(
                    message.guild,
                    "🚨 Anti-Spam",
                    f"{member.mention} تجاوز حد الرسائل وتمت محاولة تقييده 30 ثانية.",
                    discord.Color.red(),
                )

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.bot:
            return

        config = self.cfg(member.guild)
        if not config.get("security", True):
            return

        now = time.monotonic()
        joins = self.join_cache[member.guild.id]
        joins.append(now)

        while joins and now - joins[0] > 30:
            joins.popleft()

        account_age_days = (discord.utils.utcnow() - member.created_at).total_seconds() / 86400
        recent_account = account_age_days < 7

        if len(joins) >= 8:
            await self.send_log(
                member.guild,
                "🚨 احتمال Raid",
                f"دخل **{len(joins)}** أعضاء خلال 30 ثانية.\n"
                "تم رصد موجة دخول غير معتادة.",
                discord.Color.red(),
            )

        if recent_account:
            await self.send_log(
                member.guild,
                "⚠️ حساب حديث",
                f"{member.mention} حسابه أُنشئ منذ **{account_age_days:.1f} يوم**.\n"
                "هذا مؤشر مراقبة فقط وليس دليلًا أن الحساب مخترق.",
                discord.Color.gold(),
            )

        if len(joins) >= 12:
            try:
                await member.timeout(
                    timedelta(minutes=5),
                    reason="Hhf Security: suspected raid join burst",
                )
            except (discord.Forbidden, discord.HTTPException):
                pass


async def setup_security(bot):
    await bot.add_cog(SecurityCog(bot))
