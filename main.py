import discord
from discord.ext import commands, tasks
import datetime
import asyncio
import os
import json
import random
import aiohttp
from flask import Flask
from threading import Thread

# --- EMOJIS ---
EMOJIS = {
    "bankkick": "<:bankkick:1466456864194560315>",
    "settings": "<:settings:1466456847681847439>",
    "help": "<:help:1466456820578128054>",
    "success": "<:success:1466456666890305688>",
    "yes": "<:yes:1466456663325282446>",
    "dancing": "<:dancing:1466456670522835046>"
}

DEV_ID = 1081496970805399562
INVITE_URL = "https://discord.com/oauth2/authorize?client_id=1279757277309435914&permissions=8&integration_type=0&scope=bot"

async def get_prefix(bot, message):
    prefixes = ['+', 'miku ', 'Miku ']
    return commands.when_mentioned_or(*prefixes)(bot, message)

bot = commands.Bot(command_prefix=get_prefix, intents=discord.Intents.all(), help_command=None)

# --- ECONOMY DATA HANDLER ---
def load_data():
    if not os.path.exists('data.json'): return {"users": {}, "guilds": {}}
    with open('data.json', 'r') as f: return json.load(f)

def save_data(data):
    with open('data.json', 'w') as f: json.dump(data, f, indent=4)

# --- PAGINATED LEADERBOARD ---
class LeaderboardView(discord.ui.View):
    def __init__(self, lb_data, page=0):
        super().__init__(timeout=60)
        self.lb_data, self.page = lb_data, page

    async def update_lb(self, interaction):
        start, end = self.page * 5, (self.page * 5) + 5
        msg = f"🏆 **Miku Leaderboard (Page {self.page + 1})**\n"
        for i, (uid, bal) in enumerate(self.lb_data[start:end], start + 1):
            rank = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"#{i}"
            msg += f"{rank} <@{uid}>: **{bal} points**\n"
        await interaction.response.edit_message(content=msg, view=self)

    @discord.ui.button(label="Prev", style=discord.ButtonStyle.gray)
    async def prev(self, i, b):
        if self.page > 0: self.page -= 1; await self.update_lb(i)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.gray)
    async def next(self, i, b):
        if (self.page + 1) * 5 < len(self.lb_data): self.page += 1; await self.update_lb(i)

# --- 8 AM TASK ---
@tasks.loop(time=datetime.time(hour=8, minute=0))
async def daily_reminder():
    for guild in bot.guilds:
        channel = guild.system_channel or next((c for c in guild.text_channels if c.permissions_for(guild.me).send_messages), None)
        if channel: await channel.send("🌸 **Good morning!** Time to play the Miku game! Try `miku daily`!")

# --- MODERATION ---
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="No reason provided"):
    await member.ban(reason=reason)
    await ctx.send(f"{EMOJIS['bankkick']} Banned **{member.name}** | Reason: {reason}")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="No reason provided"):
    await member.kick(reason=reason)
    await ctx.send(f"{EMOJIS['bankkick']} Kicked **{member.name}** | Reason: {reason}")

@bot.command()
@commands.has_permissions(moderate_members=True)
async def mute(ctx, member: discord.Member, time: str, *, reason="No reason provided"):
    try:
        seconds = int(time[:-1]) * {'s':1,'m':60,'h':3600,'d':86400}[time[-1].lower()]
        await member.timeout(datetime.timedelta(seconds=seconds), reason=reason)
        await ctx.send(f"{EMOJIS['success']} Muted {member.name} for {time}.")
    except: await ctx.send("Format: `10m`, `1h`, `1d`!")

@bot.command()
async def unmute(ctx, member: discord.Member):
    await member.timeout(None); await ctx.send(f"{EMOJIS['yes']} Unmuted {member.name}.")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def role(ctx, member: discord.Member, role: discord.Role):
    if role in member.roles: await member.remove_roles(role); await ctx.send(f"Removed {role.name}")
    else: await member.add_roles(role); await ctx.send(f"Added {role.name}")

@bot.command()
async def dm(ctx, member: discord.Member, *, message):
    if ctx.author.guild_permissions.manage_messages:
        await member.send(f"**Staff Msg:** {message}"); await ctx.send(f"DM Sent.")

# --- UTILITY ---
@bot.command()
async def userinfo(ctx, m: discord.Member = None):
    m = m or ctx.author
    await ctx.send(f"👤 **{m.name}**\n**ID:** {m.id}\n**Joined:** {m.created_at.strftime('%Y-%m-%d')}")

@bot.command()
async def serverinfo(ctx):
    g = ctx.guild
    await ctx.send(f"🏰 **{g.name}**\n**Owner:** {g.owner}\n**Members:** {g.member_count}")

@bot.command()
async def ping(ctx):
    await ctx.send(f"{EMOJIS['dancing']} Pong! Latency: **{random.randint(983, 1234)}ms**")

# --- GAME ---
@bot.command()
async def start_egame(ctx):
    data = load_data()
    if str(ctx.guild.id) in data["guilds"]: return await ctx.send("Already active!")
    data["guilds"][str(ctx.guild.id)] = True
    for m in ctx.guild.members:
        if not m.bot: data["users"][str(m.id)] = data["users"].get(str(m.id), 0) + 500
    save_data(data); await ctx.send(f"{EMOJIS['success']} Game On! +500 points to all!")

@bot.command()
async def daily(ctx):
    data = load_data(); uid = str(ctx.author.id)
    data["users"][uid] = data["users"].get(uid, 0) + 1000
    save_data(data); await ctx.send(f"Claimed **1,000** daily points!")

@bot.command()
async def weekly(ctx):
    data = load_data(); uid = str(ctx.author.id)
    data["users"][uid] = data["users"].get(uid, 0) + 10000
    save_data(data); await ctx.send(f"Claimed **10,000** weekly points!")

@bot.command(aliases=['lb'])
async def leaderboard(ctx):
    data = load_data()
    server_ids = [m.id for m in ctx.guild.members if not m.bot]
    lb = sorted([(u, b) for u, b in data["users"].items() if int(u) in server_ids], key=lambda x: x[1], reverse=True)
    msg = f"🏆 **{ctx.guild.name} LB**\n"
    for i, (u, b) in enumerate(lb[:5], 1):
        rank = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"#{i}"
        msg += f"{rank} <@{u}>: **{b} points**\n"
    await ctx.send(msg, view=LeaderboardView(lb), silent=True)

@bot.command()
async def cf(ctx, amt: int):
    data = load_data(); uid = str(ctx.author.id)
    if amt > data["users"].get(uid, 0): return await ctx.send("Too poor!")
    if random.choice([True, False]): data["users"][uid] += amt; r = f"won {amt}!"
    else: data["users"][uid] -= amt; r = f"lost {amt}."
    save_data(data); await ctx.send(f"🪙 Coinflip: You {r}")

@bot.command()
async def pray(ctx):
    data = load_data(); uid = str(ctx.author.id)
    amt = random.randint(10, 100)
    data["users"][uid] = data["users"].get(uid, 0) + amt
    save_data(data); await ctx.send(f"🙏 Prayed and got **{amt}**!")

@bot.command()
async def rob(ctx, m: discord.Member):
    data = load_data(); uid, tid = str(ctx.author.id), str(m.id)
    if data["users"].get(tid, 0) < 100: return await ctx.send("Too poor to rob!")
    if random.randint(1, 10) > 7:
        amt = random.randint(1, 100)
        data["users"][uid] += amt; data["users"][tid] -= amt
        save_data(data); await ctx.send(f"💰 Stole **{amt}** from {m.name}!")
    else: await ctx.send("Failed!")

# --- ANIME FUN ---
# Removed 'kick' and 'punch' from this list to avoid duplicates
FUN_LIST = ['slap', 'kill', 'tickle', 'hug', 'cuddle', 'nod', 'fuck', 'beat', 'sex', 'kiss', 'wave', 'hi', 'bye', 'welcome', 'thank', 'thanks', 'pat', 'poke', 'boop', 'highfive', 'handshake', 'holdhands', 'snuggle', 'nuzzle', 'comfort', 'bonk', 'yeet', 'throw', 'bite', 'lick', 'spank', 'roast', 'explode', 'prank', 'confuse', 'tease', 'bully', 'scare', 'trap', 'shoot', 'smack', 'blush', 'cry', 'laugh', 'dance', 'sing', 'sleep', 'wake', 'facepalm', 'think', 'stare', 'smile', 'happy', 'sad', 'angry', 'excited', 'clap']

async def anime_gif(ctx, action, member: discord.Member = None):
    async with aiohttp.ClientSession() as s:
        async with s.get(f"https://api.otakugifs.xyz/gif?reaction={action}") as r:
            url = (await r.json())['url']
    msg = f"{ctx.author.mention} {action}s {member.mention}!" if member else f"{ctx.author.mention} is {action}ing!"
    await ctx.send(f"{msg}\n{url}")

for f in FUN_LIST:
    if not bot.get_command(f):
        @bot.command(name=f)
        async def _f(ctx, m: discord.Member = None, name=f): await anime_gif(ctx, name, m)

# --- DEV ONLY ---
@bot.command(name="add_money", hidden=True)
async def add_money(ctx, m: discord.Member, amt: int):
    if ctx.author.id != DEV_ID: return
    data = load_data(); data["users"][str(m.id)] = data["users"].get(str(m.id), 0) + amt
    save_data(data); await ctx.send(f"Added {amt} to {m.name}.")

# --- HELP ---
class HelpView(discord.ui.View):
    @discord.ui.button(label="Mod", style=discord.ButtonStyle.danger)
    async def m(self, i, b): await i.response.send_message("🛠 `ban`, `kick`, `mute`, `unmute`, `role`, `dm`", ephemeral=True)
    @discord.ui.button(label="Game", style=discord.ButtonStyle.success)
    async def g(self, i, b): await i.response.send_message("🎮 `daily`, `weekly`, `lb`, `cf`, `rob`, `pray`, `start_egame`", ephemeral=True)
    @discord.ui.button(label="Fun", style=discord.ButtonStyle.primary)
    async def f(self, i, b): await i.response.send_message(f"✨ {', '.join(FUN_LIST[:10])}...", ephemeral=True)

@bot.command()
async def help(ctx): await ctx.send(f"{EMOJIS['help']} **Miku Help Menu**", view=HelpView())

# --- WEB ---
app = Flask('')
@app.route('/')
def home_route(): return "Miku V6 Online!", 200

if __name__ == "__main__":
    Thread(target=lambda: app.run(host='0.0.0.0', port=os.getenv("PORT", 8080)), daemon=True).start()
    daily_reminder.start(); bot.run(os.getenv('TOKEN'))
