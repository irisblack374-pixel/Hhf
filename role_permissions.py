import discord
from discord.ext import commands

ADMIN_COMMANDS = {
    "setlog", "setwelcome", "welcome_msg", "setsuggest", "setcategory",
    "automod", "antilink", "antispam", "announce", "serverstats", "config",
    "setadminrole", "setmodrole", "clearadminrole", "clearmodrole",
}

MODERATOR_COMMANDS = {
    "clear", "kick", "ban", "unban", "timeout", "untimeout",
    "warn", "warnings", "unwarn", "lock", "unlock", "slowmode",
    "say", "poll", "createchannel", "deletechannel",
}

def _has_role(member, role_id):
    if not role_id:
        return False
    return any(role.id == int(role_id) for role in member.roles)

def _configured_role_check(member, level):
    if member.id == member.guild.owner_id:
        return True

    settings = member.guild._hhf_cfg if hasattr(member.guild, "_hhf_cfg") else {}
    admin_id = int(settings.get("admin_role", 0) or 0)
    mod_id = int(settings.get("moderator_role", 0) or 0)

    if level == "admin":
        return _has_role(member, admin_id) if admin_id else True

    if level == "moderator":
        if admin_id and _has_role(member, admin_id):
            return True
        return _has_role(member, mod_id) if mod_id else True

    return True

class RolePermissionError(commands.CheckFailure):
    def __init__(self, level):
        self.level = level
        super().__init__(f"Missing configured {level} role.")

async def role_permission_check(ctx):
    if not ctx.guild or not isinstance(ctx.author, discord.Member):
        return True

    command = ctx.command
    if command is None:
        return True

    name = command.qualified_name.lower()
    if name in ADMIN_COMMANDS:
        level = "admin"
    elif name in MODERATOR_COMMANDS:
        level = "moderator"
    else:
        return True

    # Read the current per-guild settings from the bot's config.
    cfg = getattr(ctx.bot, "cfg", None)
    if cfg is None:
        return True

    settings = cfg(ctx.guild)
    ctx.guild._hhf_cfg = settings

    if _configured_role_check(ctx.author, level):
        return True

    raise RolePermissionError(level)

async def setup_role_permissions(bot):
    bot.cfg = getattr(bot, "cfg", None)
    if bot.cfg is None:
        return
    bot.add_check(role_permission_check)
    bot.RolePermissionError = RolePermissionError
