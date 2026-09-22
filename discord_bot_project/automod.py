
import json
import os
import re
from dataclasses import dataclass, asdict
from datetime import timedelta
from typing import Optional

import discord
from discord.ext import commands

DATA_FILE = "automod_rules.json"

class MatchType:
    SUBSTRING = "substring"
    WORD = "word"
    REGEX = "regex"

class ActionType:
    DELETE = "delete"
    NOTE = "note"
    MUTE = "mute"
    KICK = "kick"
    BAN = "ban"

@dataclass
class Rule:
    id: int
    keywords: list[str]
    type: str
    action: Optional[str] = None
    duration: Optional[int] = None

class AutoMod:
    """Adapted AutoMod rule engine based on discord-math/bot."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.rules: dict[int, Rule] = {}
        self.exempt_roles: set[int] = set()
        self.regex = re.compile(r"(?!)")
        self.load()

    def load(self):
        if not os.path.exists(DATA_FILE):
            self.save()
            return
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.rules = {int(k): Rule(**v) for k, v in data.get("rules", {}).items()}
            self.exempt_roles = {int(x) for x in data.get("exempt_roles", [])}
            self.rehash()
        except Exception as e:
            print(f"AutoMod load error: {e}")

    def save(self):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "rules": {str(k): asdict(v) for k, v in self.rules.items()},
                    "exempt_roles": list(self.exempt_roles),
                }, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"AutoMod save error: {e}")

    @staticmethod
    def rule_to_regex(rule: Rule) -> str:
        if rule.type == MatchType.SUBSTRING:
            return r"|".join(re.escape(k) for k in rule.keywords)
        if rule.type == MatchType.WORD:
            return r"|".join(r"\b" + re.escape(k) + r"\b" for k in rule.keywords)
        return r"|".join(r"(?:" + k + r")" for k in rule.keywords)

    def rehash(self):
        parts = []
        for rule in sorted(self.rules.values(), key=lambda x: x.id):
            if rule.action:
                parts.append(f"(?P<_{rule.id}>" + self.rule_to_regex(rule) + ")")
        self.regex = re.compile("|".join(parts), re.I) if parts else re.compile(r"(?!)")

    def add_rule(self, kind: str, patterns: list[str]) -> Rule:
        if kind not in (MatchType.SUBSTRING, MatchType.WORD, MatchType.REGEX):
            raise ValueError("النوع يجب أن يكون substring أو word أو regex")
        if not patterns:
            raise ValueError("يجب إدخال نمط واحد على الأقل")
        if kind == MatchType.REGEX:
            for pattern in patterns:
                compiled = re.compile(pattern, re.I)
                if compiled.search("") is not None:
                    raise ValueError("Regex يطابق رسالة فارغة")
        elif any(not p for p in patterns):
            raise ValueError("النمط فارغ")
        for rule in self.rules.values():
            if rule.keywords == patterns and rule.type == kind and rule.action is None:
                return rule
        rule_id = max(self.rules.keys(), default=-1) + 1
        rule = Rule(id=rule_id, keywords=patterns, type=kind)
        self.rules[rule_id] = rule
        self.save()
        self.rehash()
        return rule

    async def scan(self, message: discord.Message) -> bool:
        if message.guild is None or message.author.bot:
            return False
        if message.author.guild_permissions.administrator:
            return False
        if isinstance(message.author, discord.Member):
            if any(role.id in self.exempt_roles for role in message.author.roles):
                return False

        match = self.regex.search(message.content)
        if not match:
            return False

        rule_id = None
        value = None
        for key, matched in match.groupdict().items():
            if matched is not None:
                rule_id = int(key[1:])
                value = matched
                break
        if rule_id is None:
            return False

        rule = self.rules.get(rule_id)
        if rule is None or not rule.action:
            return False

        reason = f"AutoMod pattern {rule.id}: {value!r}"
        try:
            await message.delete()
        except (discord.NotFound, discord.Forbidden):
            pass
        except Exception as e:
            print(f"AutoMod delete error: {e}")

        try:
            if rule.action == ActionType.NOTE:
                print(f"[AutoMod NOTE] {message.author} | {reason}")
            elif rule.action == ActionType.MUTE and isinstance(message.author, discord.Member):
                duration = rule.duration or 28 * 24 * 60 * 60
                await message.author.timeout(timedelta(seconds=duration), reason=reason)
            elif rule.action == ActionType.KICK:
                await message.guild.kick(message.author, reason=reason)
            elif rule.action == ActionType.BAN:
                await message.guild.ban(message.author, reason=reason, delete_message_seconds=0)
        except discord.Forbidden:
            print(f"AutoMod permission error: {reason}")
        except Exception as e:
            print(f"AutoMod action error: {e}")

        return True

def register(bot: commands.Bot) -> AutoMod:
    automod = AutoMod(bot)

    @bot.group(name="automod", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def automod_command(ctx: commands.Context):
        await ctx.send("AutoMod: -automod add / action / list / remove / exempt")

    @automod_command.command(name="add")
    @commands.has_permissions(administrator=True)
    async def automod_add(ctx: commands.Context, kind: str, *, patterns: str):
        values = [p.strip() for p in patterns.split("|") if p.strip()]
        try:
            rule = automod.add_rule(kind.lower(), values)
        except ValueError as e:
            await ctx.send(f"خطأ: {e}")
            return
        await ctx.send(f"تمت إضافة نمط AutoMod رقم {rule.id} بدون إجراء. استخدم -automod action {rule.id} delete لتفعيله.")

    @automod_command.command(name="action")
    @commands.has_permissions(administrator=True)
    async def automod_action(ctx: commands.Context, number: int, action: str, duration: Optional[int] = None):
        rule = automod.rules.get(number)
        if not rule:
            await ctx.send("لم يتم العثور على هذا النمط.")
            return
        if action not in (ActionType.DELETE, ActionType.NOTE, ActionType.MUTE, ActionType.KICK, ActionType.BAN):
            await ctx.send("الإجراء: delete / note / mute / kick / ban")
            return
        rule.action = action
        rule.duration = duration
        automod.save()
        automod.rehash()
        await ctx.send(f"تم تفعيل {action} للنمط {number}.")

    @automod_command.command(name="list")
    @commands.has_permissions(administrator=True)
    async def automod_list(ctx: commands.Context):
        active = [r for r in automod.rules.values() if r.action]
        if not active:
            await ctx.send("لا توجد أنماط AutoMod مفعلة.")
            return
        lines = [f"{r.id} • {r.type} • {', '.join(r.keywords)} -> {r.action}" for r in active]
        await ctx.send("\n".join(lines))

    @automod_command.command(name="remove")
    @commands.has_permissions(administrator=True)
    async def automod_remove(ctx: commands.Context, number: int):
        rule = automod.rules.get(number)
        if not rule:
            await ctx.send("لم يتم العثور على هذا النمط.")
            return
        rule.action = None
        rule.duration = None
        automod.save()
        automod.rehash()
        await ctx.send(f"تم تعطيل نمط AutoMod {number}.")

    @automod_command.group(name="exempt", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def automod_exempt(ctx: commands.Context):
        roles = []
        for role_id in automod.exempt_roles:
            role = ctx.guild.get_role(role_id) if ctx.guild else None
            roles.append(role.mention if role else str(role_id))
        await ctx.send("الرتب المستثناة: " + (", ".join(roles) if roles else "لا يوجد"))

    @automod_exempt.command(name="add")
    @commands.has_permissions(administrator=True)
    async def automod_exempt_add(ctx: commands.Context, role: discord.Role):
        automod.exempt_roles.add(role.id)
        automod.save()
        await ctx.send(f"تم استثناء رتبة {role.mention} من AutoMod.")

    @automod_exempt.command(name="remove")
    @commands.has_permissions(administrator=True)
    async def automod_exempt_remove(ctx: commands.Context, role: discord.Role):
        automod.exempt_roles.discard(role.id)
        automod.save()
        await ctx.send(f"تم إلغاء استثناء رتبة {role.mention}.")

    return automod
