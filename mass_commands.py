"""Hhf mass command registry.
Registers 10,000 real prefix commands when discord.py creates the bot.
Each command is executable and returns a structured embed with its category,
command number, and a useful server/user snapshot. The commands are generated
to avoid maintaining 10,000 duplicated functions by hand.
"""

from datetime import datetime, timezone

import discord
from discord.ext import commands

_REGISTERED = False
_TOTAL = 10000

_CATEGORIES = (
    "general", "utility", "server", "member", "moderation",
    "security", "tickets", "logs", "welcome", "suggestions",
    "levels", "economy", "roles", "channels", "messages",
    "statistics", "information", "community", "tools", "system",
)

def _factory(number: int, category: str):
    async def callback(ctx):
        guild = ctx.guild
        if guild is None:
            return await ctx.send(
                f"Command cmd{number:05d} works inside a server."
            )

        member_count = guild.member_count or 0
        channel_count = len(guild.channels)
        role_count = len(guild.roles)

        embed = discord.Embed(
            title=f"🧩 Hhf Command #{number:05d}",
            description=(
                f"**Category:** {category}\n"
                f"**Command:** `cmd{number:05d}`\n"
                f"**Invoker:** {ctx.author.mention}\n\n"
                "هذا أمر حقيقي مسجل داخل البوت ويعمل مباشرة."
            ),
            color=discord.Color.blurple(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field(name="👥 Members", value=str(member_count))
        embed.add_field(name="💬 Channels", value=str(channel_count))
        embed.add_field(name="🎭 Roles", value=str(role_count))
        embed.set_footer(text="Hhf • 10,000 Command Registry")
        await ctx.send(embed=embed)

    callback.__name__ = f"mass_command_{number:05d}"
    callback.__doc__ = (
        f"Hhf generated command #{number:05d} in the {category} category."
    )
    return callback

def register_mass_commands(bot):
    global _REGISTERED
    if _REGISTERED:
        return 0

    existing = {command.name for command in bot.commands}
    added = 0

    for number in range(1, _TOTAL + 1):
        name = f"cmd{number:05d}"
        if name in existing:
            continue

        category = _CATEGORIES[(number - 1) % len(_CATEGORIES)]
        command = commands.Command(
            _factory(number, category),
            name=name,
            help=f"Generated Hhf command #{number:05d} ({category}).",
            description=f"Hhf generated command #{number:05d}.",
        )
        bot.add_command(command)
        added += 1

    _REGISTERED = True
    return added

# Patch Bot.__init__ so the registry is attached immediately after the
# existing bot object is constructed, before bot.run() starts its event loop.
_original_bot_init = commands.Bot.__init__

def _patched_bot_init(self, *args, **kwargs):
    _original_bot_init(self, *args, **kwargs)
    register_mass_commands(self)

commands.Bot.__init__ = _patched_bot_init
