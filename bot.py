import os, json, time, asyncio, logging
from pathlib import Path
from collections import defaultdict, deque
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

load_dotenv()
TOKEN=os.getenv("DISCORD_TOKEN")
PREFIX=os.getenv("PREFIX","!")
START=time.time()
DATA=Path("data"); DATA.mkdir(exist_ok=True)
CONFIG=DATA/"config.json"; WARNS=DATA/"warnings.json"; TICKETS=DATA/"tickets.json"
logging.basicConfig(level=logging.INFO,format="%(asctime)s | %(levelname)s | %(message)s")

intents=discord.Intents.default()
intents.message_content=True
intents.members=True
intents.guilds=True
bot=commands.Bot(command_prefix=PREFIX,intents=intents,help_command=None,case_insensitive=True)

def load(path, default):
    if not path.exists(): return default
    try: return json.loads(path.read_text(encoding="utf-8"))
    except Exception: return default

def save(path,data): path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
configs=load(CONFIG,{}); warns=load(WARNS,{}); tickets=load(TICKETS,{})
spam=defaultdict(lambda:deque(maxlen=8))

def settings(guild):
    k=str(guild.id)
    if k not in configs:
        configs[k]={"logs":0,"welcome":0,"suggestions":0,"welcome_text":"أهلًا بك {member} في {server}! 🎉","automod":True,"antilink":False,"antispam":True}
        save(CONFIG,configs)
    return configs[k]

def mod(member):
    p=member.guild_permissions
    return p.administrator or p.manage_guild or p.manage_messages

async def log(guild,title,text,color=discord.Color.blurple()):
    cid=int(settings(guild).get("logs",0) or 0); ch=guild.get_channel(cid) if cid else None
    if not ch: return
    try: await ch.send(embed=discord.Embed(title=title,description=text[:4000],color=color,timestamp=discord.utils.utcnow()))
    except discord.HTTPException: pass

@bot.event
async def on_ready():
    logging.info("Logged in as %s",bot.user)
    await bot.change_presence(activity=discord.Game(name=f"{PREFIX}help | Hhf"))
    if not status.is_running(): status.start()

@tasks.loop(minutes=5)
async def status():
    await bot.change_presence(activity=discord.Game(name=f"{PREFIX}help | {len(bot.guilds)} servers"))

@bot.event
async def on_member_join(member):
    s=settings(member.guild); cid=int(s.get("welcome",0) or 0); ch=member.guild.get_channel(cid) if cid else None
    if ch:
        text=s.get("welcome_text","أهلًا بك {member} في {server}! 🎉").replace("{member}",member.mention).replace("{server}",member.guild.name)
        e=discord.Embed(title="👋 عضو جديد",description=text,color=discord.Color.green()); e.set_thumbnail(url=member.display_avatar.url); await ch.send(embed=e)
    await log(member.guild,"👋 دخول عضو",f"{member.mention} دخل السيرفر.",discord.Color.green())

@bot.event
async def on_member_remove(member): await log(member.guild,"🚪 خروج عضو",f"{member} غادر السيرفر.",discord.Color.orange())

@bot.event
async def on_message_delete(message):
    if message.guild and not message.author.bot: await log(message.guild,"🗑️ حذف رسالة",f"{message.author.mention} في {message.channel.mention}\n{message.content[:1000]}",discord.Color.orange())

@bot.event
async def on_message_edit(before,after):
    if before.guild and not before.author.bot and before.content!=after.content: await log(before.guild,"✏️ تعديل رسالة",f"قبل: {before.content[:500]}\nبعد: {after.content[:500]}",discord.Color.gold())

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild: return
    s=settings(message.guild)
    if s.get("automod") and not mod(message.author):
        text=message.content.lower()
        if s.get("antilink") and any(x in text for x in ("http://","https://","discord.gg/","www.")):
            try: await message.delete(); await message.channel.send(f"{message.author.mention} ❌ الروابط غير مسموحة.",delete_after=5)
            except discord.HTTPException: pass
            return
        if s.get("antispam"):
            now=time.monotonic(); q=spam[message.author.id]; q.append(now)
            while q and now-q[0]>6: q.popleft()
            if len(q)>=7:
                q.clear()
                try: await message.author.timeout(discord.utils.utcnow()+discord.timedelta(seconds=10),reason="Hhf Anti-Spam")
                except (discord.Forbidden,discord.HTTPException): pass
                return
    await bot.process_commands(message)

@bot.command(name="help")
async def help_cmd(ctx):
    e=discord.Embed(title="🤖 Hhf Bot",description="بوت إدارة وحماية وتذاكر وأدوات.",color=discord.Color.blurple())
    e.add_field(name="📌 عام",value=f"{PREFIX}ping | {PREFIX}uptime | {PREFIX}server | {PREFIX}userinfo | {PREFIX}avatar | {PREFIX}botinfo",inline=False)
    e.add_field(name="🛡️ إدارة",value=f"{PREFIX}clear | {PREFIX}kick | {PREFIX}ban | {PREFIX}unban | {PREFIX}timeout | {PREFIX}untimeout | {PREFIX}warn | {PREFIX}warnings | {PREFIX}unwarn",inline=False)
    e.add_field(name="🔒 حماية",value=f"{PREFIX}automod on/off | {PREFIX}antilink on/off | {PREFIX}antispam on/off",inline=False)
    e.add_field(name="🎫 تذاكر",value=f"{PREFIX}ticket | {PREFIX}close",inline=False)
    e.add_field(name="⚙️ إعدادات",value=f"{PREFIX}setlog | {PREFIX}setwelcome | {PREFIX}welcome_msg | {PREFIX}setsuggest | {PREFIX}config",inline=False)
    e.add_field(name="🔧 أدوات",value=f"{PREFIX}lock | {PREFIX}unlock | {PREFIX}slowmode | {PREFIX}say | {PREFIX}announce | {PREFIX}poll | {PREFIX}suggest | {PREFIX}createchannel | {PREFIX}deletechannel",inline=False)
    await ctx.send(embed=e)

@bot.command()
async def ping(ctx): await ctx.send(f"🏓 Pong! {round(bot.latency*1000)}ms")

@bot.command()
async def uptime(ctx):
    x=int(time.time()-START); d,x=divmod(x,86400); h,x=divmod(x,3600); m,x=divmod(x,60); await ctx.send(f"⏱️ {d}d {h}h {m}m {x}s")

@bot.command()
async def botinfo(ctx):
    e=discord.Embed(title="🤖 Hhf",color=discord.Color.blurple()); e.add_field(name="Servers",value=len(bot.guilds)); e.add_field(name="Users",value=len(bot.users)); e.add_field(name="Library",value=discord.__version__); await ctx.send(embed=e)

@bot.command()
async def server(ctx):
    g=ctx.guild; e=discord.Embed(title=f"📊 {g.name}",color=discord.Color.blurple()); e.add_field(name="👥 الأعضاء",value=g.member_count); e.add_field(name="💬 الرومات",value=len(g.channels)); e.add_field(name="🎭 الرتب",value=len(g.roles)); e.add_field(name="🆔 ID",value=g.id); await ctx.send(embed=e)

@bot.command()
async def userinfo(ctx,member:discord.Member=None):
    member=member or ctx.author; e=discord.Embed(title=f"👤 {member}",color=member.color); e.set_thumbnail(url=member.display_avatar.url); e.add_field(name="ID",value=member.id); e.add_field(name="الحساب",value=discord.utils.format_dt(member.created_at,"F")); e.add_field(name="الرتبة",value=member.top_role.mention); await ctx.send(embed=e)

@bot.command()
async def avatar(ctx,member:discord.Member=None):
    member=member or ctx.author; e=discord.Embed(title=f"🖼️ {member}"); e.set_image(url=member.display_avatar.url); await ctx.send(embed=e)

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx,amount:int):
    if not 1<=amount<=100: return await ctx.reply("❌ العدد من 1 إلى 100.")
    deleted=await ctx.channel.purge(limit=amount+1); await ctx.send(f"🧹 تم حذف {max(len(deleted)-1,0)} رسالة.",delete_after=4); await log(ctx.guild,"🧹 Clear",f"{ctx.author.mention} حذف رسائل.")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx,member:discord.Member,*,reason="بدون سبب"):
    if member==ctx.author or member==ctx.guild.owner: return await ctx.reply("❌ لا يمكنك طرد هذا العضو.")
    await member.kick(reason=reason); await ctx.send(f"👢 تم طرد {member.mention}\nالسبب: {reason}"); await log(ctx.guild,"👢 Kick",f"{ctx.author.mention} طرد {member.mention}. السبب: {reason}",discord.Color.orange())

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx,member:discord.Member,*,reason="بدون سبب"):
    if member==ctx.author or member==ctx.guild.owner: return await ctx.reply("❌ لا يمكنك حظر هذا العضو.")
    await member.ban(reason=reason,delete_message_seconds=0); await ctx.send(f"🔨 تم حظر {member.mention}\nالسبب: {reason}"); await log(ctx.guild,"🔨 Ban",f"{ctx.author.mention} حظر {member.mention}. السبب: {reason}",discord.Color.red())

@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx,user_id:int):
    try: user=await bot.fetch_user(user_id); await ctx.guild.unban(user); await ctx.send(f"🔓 تم فك حظر {user}.")
    except discord.NotFound: await ctx.reply("❌ العضو غير موجود في قائمة المحظورين.")

@bot.command()
@commands.has_permissions(moderate_members=True)
async def timeout(ctx,member:discord.Member,minutes:int,*,reason="بدون سبب"):
    if not 1<=minutes<=40320: return await ctx.reply("❌ المدة من 1 إلى 40320 دقيقة.")
    await member.timeout(discord.utils.utcnow()+discord.timedelta(minutes=minutes),reason=reason); await ctx.send(f"⏳ تم تقييد {member.mention} لمدة {minutes} دقيقة.")

@bot.command()
@commands.has_permissions(moderate_members=True)
async def untimeout(ctx,member:discord.Member): await member.timeout(None); await ctx.send(f"✅ تم إزالة Timeout عن {member.mention}.")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def lock(ctx):
    o=ctx.channel.overwrites_for(ctx.guild.default_role); o.send_messages=False; await ctx.channel.set_permissions(ctx.guild.default_role,overwrite=o); await ctx.send("🔒 تم قفل الروم.")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def unlock(ctx):
    o=ctx.channel.overwrites_for(ctx.guild.default_role); o.send_messages=None; await ctx.channel.set_permissions(ctx.guild.default_role,overwrite=o); await ctx.send("🔓 تم فتح الروم.")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def slowmode(ctx,seconds:int):
    if not 0<=seconds<=21600: return await ctx.reply("❌ استخدم 0 إلى 21600.")
    await ctx.channel.edit(slowmode_delay=seconds); await ctx.send(f"🐢 Slowmode: {seconds} ثانية.")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def say(ctx,*,text): await ctx.message.delete(); await ctx.send(text)

@bot.command()
@commands.has_permissions(manage_guild=True)
async def announce(ctx,*,text): await ctx.send(embed=discord.Embed(title="📢 إعلان",description=text,color=discord.Color.gold()))

@bot.command()
@commands.has_permissions(manage_messages=True)
async def poll(ctx,*,question):
    m=await ctx.send(embed=discord.Embed(title="📊 تصويت",description=question,color=discord.Color.blurple())); await m.add_reaction("👍"); await m.add_reaction("👎")

@bot.command()
@commands.has_permissions(manage_guild=True)
async def setlog(ctx,channel:discord.TextChannel): settings(ctx.guild)["logs"]=channel.id; save(CONFIG,configs); await ctx.send(f"✅ Logs: {channel.mention}")

@bot.command()
@commands.has_permissions(manage_guild=True)
async def setwelcome(ctx,channel:discord.TextChannel): settings(ctx.guild)["welcome"]=channel.id; save(CONFIG,configs); await ctx.send(f"✅ Welcome: {channel.mention}")

@bot.command()
@commands.has_permissions(manage_guild=True)
async def welcome_msg(ctx,*,text): settings(ctx.guild)["welcome_text"]=text[:1000]; save(CONFIG,configs); await ctx.send("✅ تم حفظ رسالة الترحيب.")

@bot.command()
@commands.has_permissions(manage_guild=True)
async def setsuggest(ctx,channel:discord.TextChannel): settings(ctx.guild)["suggestions"]=channel.id; save(CONFIG,configs); await ctx.send(f"✅ Suggestions: {channel.mention}")

@bot.command()
@commands.has_permissions(manage_guild=True)
async def automod(ctx,mode:str):
    if mode.lower() not in ("on","off"): return await ctx.reply("❌ استخدم on أو off.")
    settings(ctx.guild)["automod"]=mode.lower()=="on"; save(CONFIG,configs); await ctx.send("🛡️ AutoMod: "+("مفعل" if settings(ctx.guild)["automod"] else "متوقف"))

@bot.command()
@commands.has_permissions(manage_guild=True)
async def antilink(ctx,mode:str):
    if mode.lower() not in ("on","off"): return await ctx.reply("❌ استخدم on أو off.")
    settings(ctx.guild)["antilink"]=mode.lower()=="on"; save(CONFIG,configs); await ctx.send("🔗 Anti-Link: "+("مفعل" if settings(ctx.guild)["antilink"] else "متوقف"))

@bot.command()
@commands.has_permissions(manage_guild=True)
async def antispam(ctx,mode:str):
    if mode.lower() not in ("on","off"): return await ctx.reply("❌ استخدم on أو off.")
    settings(ctx.guild)["antispam"]=mode.lower()=="on"; save(CONFIG,configs); await ctx.send("🚫 Anti-Spam: "+("مفعل" if settings(ctx.guild)["antispam"] else "متوقف"))

@bot.command()
@commands.has_permissions(manage_messages=True)
async def warn(ctx,member:discord.Member,*,reason="بدون سبب"):
    g=str(ctx.guild.id); u=str(member.id); warns.setdefault(g,{}).setdefault(u,[]).append({"reason":reason,"by":ctx.author.id,"time":int(time.time())}); save(WARNS,warns); await ctx.send(f"⚠️ تم تحذير {member.mention}. الإجمالي: {len(warns[g][u])}.")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def warnings(ctx,member:discord.Member=None):
    member=member or ctx.author; entries=warns.get(str(ctx.guild.id),{}).get(str(member.id),[])
    if not entries: return await ctx.send("✅ لا توجد تحذيرات.")
    await ctx.send("⚠️ تحذيرات "+member.mention+":\n"+"\n".join(f"{i}. {x[\"reason\"]}" for i,x in enumerate(entries[-10:],1)))

@bot.command()
@commands.has_permissions(manage_messages=True)
async def unwarn(ctx,member:discord.Member,number:int):
    entries=warns.get(str(ctx.guild.id),{}).get(str(member.id),[])
    if not 1<=number<=len(entries): return await ctx.reply("❌ رقم غير صحيح.")
    entries.pop(number-1); save(WARNS,warns); await ctx.send("✅ تم حذف التحذير.")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def ticket(ctx):
    g=str(ctx.guild.id); u=str(ctx.author.id); old=tickets.get(g,{}).get(u)
    if old and ctx.guild.get_channel(int(old)): return await ctx.reply(f"🛑 لديك تذكرة: <#{old}>")
    ow={ctx.guild.default_role:discord.PermissionOverwrite(view_channel=False),ctx.author:discord.PermissionOverwrite(view_channel=True,send_messages=True,read_message_history=True),ctx.guild.me:discord.PermissionOverwrite(view_channel=True,send_messages=True,manage_channels=True)}
    ch=await ctx.guild.create_text_channel(f"ticket-{ctx.author.name[:20]}",overwrites=ow); tickets.setdefault(g,{})[u]=ch.id; save(TICKETS,tickets); await ch.send(f"🎫 مرحبًا {ctx.author.mention}! اكتب طلبك هنا. {PREFIX}close للإغلاق."); await ctx.reply(f"✅ تم إنشاء {ch.mention}")

@bot.command()
async def close(ctx):
    g=str(ctx.guild.id); owner=next((u for u,c in tickets.get(g,{}).items() if int(c)==ctx.channel.id),None)
    if not owner: return await ctx.reply("❌ هذا ليس روم تذكرة.")
    if owner!=str(ctx.author.id) and not mod(ctx.author): return await ctx.reply("❌ لا يمكنك إغلاقها.")
    tickets[g].pop(owner,None); save(TICKETS,tickets); await ctx.send("🔒 سيتم الإغلاق خلال 3 ثوانٍ."); await asyncio.sleep(3); await ctx.channel.delete()

@bot.command()
async def suggest(ctx,*,text):
    ch=ctx.guild.get_channel(int(settings(ctx.guild).get("suggestions",0) or 0))
    if not ch: return await ctx.reply(f"❌ استخدم {PREFIX}setsuggest #الروم أولًا.")
    e=discord.Embed(title="💡 اقتراح جديد",description=text[:2000],color=discord.Color.blurple()); e.set_author(name=str(ctx.author),icon_url=ctx.author.display_avatar.url); m=await ch.send(embed=e); await m.add_reaction("👍"); await m.add_reaction("👎"); await ctx.reply("✅ تم إرسال الاقتراح.")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def createchannel(ctx,*,name): ch=await ctx.guild.create_text_channel(name[:100]); await ctx.send(f"✅ تم إنشاء {ch.mention}")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def deletechannel(ctx): name=ctx.channel.name; await ctx.channel.delete(reason=f"Deleted by {ctx.author}")

@bot.command()
async def rolelist(ctx):
    roles=[r.mention for r in reversed(ctx.guild.roles) if r!=ctx.guild.default_role]; await ctx.send("🎭 الرتب:\n"+(", ".join(roles)[:1900] or "لا توجد رتب"))

@bot.command()
async def channels(ctx): await ctx.send(f"💬 نصية: {len(ctx.guild.text_channels)} | 🔊 صوتية: {len(ctx.guild.voice_channels)} | 📁 تصنيفات: {len(ctx.guild.categories)}")

@bot.command()
async def icon(ctx):
    if not ctx.guild.icon: return await ctx.send("❌ لا توجد صورة.")
    e=discord.Embed(title=ctx.guild.name); e.set_image(url=ctx.guild.icon.url); await ctx.send(embed=e)

@bot.command()
@commands.has_permissions(manage_guild=True)
async def config(ctx):
    s=settings(ctx.guild); e=discord.Embed(title="⚙️ إعدادات Hhf",color=discord.Color.blurple())
    for key,label in (("logs","Logs"),("welcome","Welcome"),("suggestions","Suggestions")): e.add_field(name=label,value=f"<#{s[key]}>" if s.get(key) else "غير معين")
    e.add_field(name="AutoMod",value="ON" if s["automod"] else "OFF"); e.add_field(name="Anti-Link",value="ON" if s["antilink"] else "OFF"); e.add_field(name="Anti-Spam",value="ON" if s["antispam"] else "OFF"); await ctx.send(embed=e)

@bot.event
async def on_command_error(ctx,error):
    if isinstance(error,commands.CommandNotFound): return
    if isinstance(error,commands.MissingPermissions): return await ctx.reply("❌ هذا الأمر يحتاج صلاحيات مناسبة.")
    if isinstance(error,commands.BotMissingPermissions): return await ctx.reply("❌ البوت لا يملك الصلاحيات المطلوبة.")
    if isinstance(error,commands.MissingRequiredArgument): return await ctx.reply(f"❌ يوجد متغير ناقص. استخدم {PREFIX}help.")
    if isinstance(error,commands.BadArgument): return await ctx.reply("❌ البيانات غير صحيحة.")
    logging.exception("Command error",exc_info=error)
    try: await ctx.reply("❌ حدث خطأ أثناء التنفيذ.")
    except discord.HTTPException: pass

if not TOKEN: raise RuntimeError("DISCORD_TOKEN غير موجود في متغيرات البيئة.")
bot.run(TOKEN)