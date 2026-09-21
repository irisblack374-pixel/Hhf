import asyncio
import discord
from discord.ext import commands
from datetime import timedelta
from collections import defaultdict, deque
import time


class ProtectionCog(commands.Cog):
    """Anti-Nuke, role/channel protection and automatic raid lockdown."""

    def __init__(self, bot):
        self.bot = bot
        self.action_cache = defaultdict(lambda: deque())
        self.join_cache = defaultdict(lambda: deque())
        self.locked = set()
        self.snapshots = {}

    def cfg(self, guild):
        return self.bot.cfg(guild)

    async def log(self, guild, title, text, color=discord.Color.red()):
        await self.bot.log(guild, title, text, color)

    def enabled(self, guild, key, default=True):
        return bool(self.cfg(guild).get(key, default))

    def manager(self, member):
        p = member.guild_permissions
        return p.administrator or p.manage_guild

    async def actor_from_audit(self, guild, action):
        try:
            async for entry in guild.audit_logs(limit=5, action=action):
                if time.time() - entry.created_at.timestamp() <= 15:
                    return entry.user
        except (discord.Forbidden, discord.HTTPException):
            return None
        return None

    async def punish_actor(self, guild, actor, reason):
        if not actor or actor.id == guild.owner_id or actor == guild.me:
            return
        if isinstance(actor, discord.Member):
            try:
                await actor.timeout(timedelta(minutes=30), reason=f"Hhf Anti-Nuke: {reason}")
            except (discord.Forbidden, discord.HTTPException):
                pass
        await self.log(
            guild, "🚨 Anti-Nuke Action",
            f"**المنفذ:** {actor.mention if hasattr(actor, 'mention') else actor}\n"
            f"**السبب:** {reason}",
            discord.Color.red()
        )

    async def record_action(self, guild, actor, reason, limit=3, window=20):
        if not actor:
            return False
        key = (guild.id, actor.id, reason)
        q = self.action_cache[key]
        now = time.monotonic()
        q.append(now)
        while q and now - q[0] > window:
            q.popleft()
        if len(q) >= limit:
            await self.punish_actor(guild, actor, reason)
            return True
        return False

    async def lockdown(self, guild, reason):
        if guild.id in self.locked:
            return
        self.locked.add(guild.id)

        changed = 0
        for channel in guild.text_channels:
            try:
                overwrite = channel.overwrites_for(guild.default_role)
                overwrite.send_messages = False
                overwrite.add_reactions = False
                await channel.set_permissions(
                    guild.default_role,
                    overwrite=overwrite,
                    reason=f"Hhf Raid Lockdown: {reason}",
                )
                changed += 1
            except (discord.Forbidden, discord.HTTPException):
                continue

        self.cfg(guild)["lockdown"] = True
        self.bot.save_json(self.bot.CONFIG_FILE, self.bot.configs)

        await self.log(
            guild, "🔒 RAID LOCKDOWN",
            f"تم تفعيل القفل التلقائي بسبب: **{reason}**\n"
            f"تم قفل **{changed}** روم نصي.",
            discord.Color.red()
        )

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.bot or not self.enabled(member.guild, "raid_protection", True):
            return

        q = self.join_cache[member.guild.id]
        now = time.monotonic()
        q.append(now)
        while q and now - q[0] > 30:
            q.popleft()

        if len(q) >= int(self.cfg(member.guild).get("raid_join_threshold", 10)):
            await self.lockdown(member.guild, f"{len(q)} joins خلال 30 ثانية")

    async def anti_nuke(self, guild, action, reason):
        if not self.enabled(guild, "antinuke", True):
            return
        actor = await self.actor_from_audit(guild, action)
        triggered = await self.record_action(guild, actor, reason)
        if triggered:
            await self.lockdown(guild, f"Anti-Nuke: {reason}")

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        await self.anti_nuke(channel.guild, discord.AuditLogAction.channel_delete, "حذف عدة رومات")

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        await self.anti_nuke(channel.guild, discord.AuditLogAction.channel_create, "إنشاء عدة رومات")

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        await self.anti_nuke(role.guild, discord.AuditLogAction.role_delete, "حذف عدة رتب")

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        await self.anti_nuke(role.guild, discord.AuditLogAction.role_create, "إنشاء عدة رتب")

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        if before.permissions != after.permissions:
            await self.anti_nuke(after.guild, discord.AuditLogAction.role_update, "تغيير صلاحيات رتبة")

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        if before.overwrites != after.overwrites or before.name != after.name:
            await self.anti_nuke(after.guild, discord.AuditLogAction.channel_update, "تغيير إعدادات روم")

    @commands.command(name="lockdown")
    @commands.has_permissions(manage_guild=True)
    async def lockdown_command(self, ctx):
        await self.lockdown(ctx.guild, "تفعيل يدوي من الإدارة")
        await ctx.send("🔒 تم تفعيل Lockdown.")

    @commands.command(name="unlockdown")
    @commands.has_permissions(manage_guild=True)
    async def unlockdown_command(self, ctx):
        for channel in ctx.guild.text_channels:
            try:
                overwrite = channel.overwrites_for(ctx.guild.default_role)
                overwrite.send_messages = None
                overwrite.add_reactions = None
                await channel.set_permissions(
                    ctx.guild.default_role,
                    overwrite=overwrite,
                    reason="Hhf Raid Lockdown解除",
                )
            except (discord.Forbidden, discord.HTTPException):
                continue
        self.locked.discard(ctx.guild.id)
        self.cfg(ctx.guild)["lockdown"] = False
        self.bot.save_json(self.bot.CONFIG_FILE, self.bot.configs)
        await ctx.send("🔓 تم إلغاء Lockdown.")
        await self.log(ctx.guild, "🔓 Lockdown Disabled", f"{ctx.author.mention} ألغى القفل.")

    @commands.command(name="protection")
    async def protection_status(self, ctx):
        c = self.cfg(ctx.guild)
        text = (
            f"Anti-Nuke: {'ON' if c.get('antinuke', True) else 'OFF'}\n"
            f"Role/Channel Guard: {'ON' if c.get('antinuke', True) else 'OFF'}\n"
            f"Raid Protection: {'ON' if c.get('raid_protection', True) else 'OFF'}\n"
            f"Lockdown: {'ON' if ctx.guild.id in self.locked else 'OFF'}"
        )
        await ctx.send(embed=self.bot.embed("🛡️ حالة الحماية", text, discord.Color.green()))


async def setup_protection(bot):
    await bot.add_cog(ProtectionCog(bot))
