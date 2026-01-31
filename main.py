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

# --- 8 AM TASK ---
@tasks.loop(time=datetime.time(hour=8, minute=0))
async def daily_reminder():
    for guild in bot.guilds:
        channel = guild.system_channel or next((c for c in guild.text_channels if c.permissions_for(guild.me).send_messages), None)
        if channel:
            try: await channel.send("🌸 **Good morning!** Time to play the Miku game! Try `miku daily`!")
            except: continue

# --- WEB SERVER ---
app = Flask('')
@app.route('/')
def home_route(): return "Miku V7 Online!", 200

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- ANIME FUN ENGINE ---
FUN_LIST = ['slap', 'kill', 'tickle', 'hug', 'cuddle', 'nod', 'fuck', 'beat', 'sex', 'kiss', 'wave', 'hi', 'bye', 'welcome', 'thank', 'thanks', 'pat', 'poke', 'boop', 'highfive', 'handshake', 'holdhands', 'snuggle', 'nuzzle', 'comfort', 'bonk', 'yeet', 'throw', 'bite', 'lick', 'spank', 'roast', 'explode', 'prank', 'confuse', 'tease', 'bully', 'scare', 'trap', 'shoot', 'smack', 'blush', 'cry', 'laugh', 'dance', 'sing', 'sleep', 'wake', 'facepalm', 'think', 'stare', 'smile', 'happy', 'sad', 'angry', 'excited', 'clap']

async def anime_gif(ctx, action, member: discord.Member = None):
    async with aiohttp.ClientSession() as s:
        async with s.get(f"https://api.otakugifs.xyz/gif?reaction={action}") as r:
            data = await r.json()
            url = data['url']
    msg = f"{ctx.author.mention} {action}s {member.mention}!" if member else f"{ctx.author.mention} is {action}ing!"
    await ctx.send(f"{msg}\n{url}")

for f in FUN_LIST:
    if not bot.get_command(f):
        @bot.command(name=f)
        async def _f(ctx, m: discord.Member = None, name=f): await anime_gif(ctx, name, m)

# --- MODERATION ---
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="No reason provided"):
    await member.ban(reason=reason); await ctx.send(f"{EMOJIS['bankkick']} Banned **{member.name}**")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="No reason provided"):
    await member.kick(reason=reason); await ctx.send(f"{EMOJIS['bankkick']} Kicked **{member.name}**")

@bot.command()
@commands.has_permissions(moderate_members=True)
async def mute(ctx, member: discord.Member, time: str, *, reason="No"):
    seconds = int(time[:-1]) * {'s':1,'m':60,'h':3600,'d':86400}[time[-1].lower()]
    await member.timeout(datetime.timedelta(seconds=seconds), reason=reason)
    await ctx.send(f"{EMOJIS['success']} Muted {member.name} for {time}")

# --- GAME ---
@bot.command()
async def daily(ctx):
    data = load_data(); uid = str(ctx.author.id)
    data["users"][uid] = data["users"].get(uid, 0) + 1000
    save_data(data); await ctx.send(f"Claimed **1,000** daily points!")

@bot.command(aliases=['lb'])
async def leaderboard(ctx):
    data = load_data()
    server_ids = [m.id for m in ctx.guild.members if not m.bot]
    lb = sorted([(u, b) for u, b in data["users"].items() if int(u) in server_ids], key=lambda x: x[1], reverse=True)
    msg = f"🏆 **{ctx.guild.name} LB**\n"
    for i, (u, b) in enumerate(lb[:5], 1):
        rank = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"#{i}"
        msg += f"{rank} <@{u}>: **{b} points**\n"
    await ctx.send(msg, silent=True)

# --- DEV TOOLS ---
@bot.command(name="add_money", hidden=True)
async def add_money(ctx, m: discord.Member, amt: int):
    if ctx.author.id == DEV_ID:
        data = load_data(); data["users"][str(m.id)] = data["users"].get(str(m.id), 0) + amt
        save_data(data); await ctx.send(f"Added {amt}!")

# --- STARTUP HOOK ---
@bot.event
async def on_ready():
    if not daily_reminder.is_running():
        daily_reminder.start()
    print(f"Miku is logged in as {bot.user}")

if __name__ == "__main__":
    Thread(target=run_web, daemon=True).start()
    bot.run(os.getenv('TOKEN'))
