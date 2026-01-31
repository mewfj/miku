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
    "success": "<:success:1466456666666890305688>", # Use your specific IDs
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
            await channel.send("🌸 **Good morning!** Use Miku bot today or play the Miku game! Try `miku daily`!")

# --- GAME COMMANDS ---
@bot.command()
@commands.has_permissions(administrator=True)
async def start_egame(ctx):
    data = load_data()
    if str(ctx.guild.id) in data["guilds"]: return await ctx.send("Game already active!")
    data["guilds"][str(ctx.guild.id)] = True
    for m in ctx.guild.members:
        if not m.bot: data["users"][str(m.id)] = data["users"].get(str(m.id), 0) + 500
    save_data(data)
    await ctx.send(f"{EMOJIS['success']} **Miku Game Started!** Everyone got **500 points**!")

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

@bot.command(aliases=['lb', 'top'])
async def leaderboard(ctx):
    data = load_data()
    # Server LB logic
    server_ids = [m.id for m in ctx.guild.members if not m.bot]
    lb = sorted([(u, b) for u, b in data["users"].items() if int(u) in server_ids], key=lambda x: x[1], reverse=True)
    
    msg = f"🏆 **{ctx.guild.name} Leaderboard**\n"
    for i, (u, b) in enumerate(lb[:5], 1):
        rank = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"#{i}"
        msg += f"{rank} <@{u}>: **{b} points**\n"
    await ctx.send(msg, silent=True)

# Coinflip, Pray, Rob
@bot.command()
async def cf(ctx, amt: int):
    data = load_data(); uid = str(ctx.author.id)
    bal = data["users"].get(uid, 0)
    if amt > bal: return await ctx.send("Not enough points!")
    if random.choice([True, False]):
        data["users"][uid] += amt; res = f"won {amt}!"
    else:
        data["users"][uid] -= amt; res = f"lost {amt}."
    save_data(data); await ctx.send(f"🪙 Coinflip: You {res}")

@bot.command()
async def pray(ctx):
    data = load_data(); uid = str(ctx.author.id)
    amt = random.randint(10, 100)
    data["users"][uid] = data["users"].get(uid, 0) + amt
    save_data(data); await ctx.send(f"🙏 You prayed and got **{amt}** points!")

@bot.command()
async def rob(ctx, member: discord.Member):
    data = load_data(); uid, tid = str(ctx.author.id), str(member.id)
    if data["users"].get(tid, 0) < 100: return await ctx.send("They are too poor!")
    if random.randint(1, 10) > 7:
        amt = random.randint(1, 100)
        data["users"][uid] += amt; data["users"][tid] -= amt
        save_data(data); await ctx.send(f"💰 Stole **{amt}** from {member.name}!")
    else: await ctx.send("Police caught you! Rob failed.")

# --- MODERATION ---
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, m: discord.Member, *, r="None"):
    await m.ban(reason=r); await ctx.send(f"{EMOJIS['bankkick']} Banned {m.name}")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, m: discord.Member, *, r="None"):
    await m.kick(reason=r); await ctx.send(f"{EMOJIS['bankkick']} Kicked {m.name}")

# --- MASSIVE ANIME FUN ---
FUN_LIST = ['slap', 'kill', 'tickle', 'hug', 'cuddle', 'nod', 'fuck', 'beat', 'sex', 'kiss', 'wave', 'hi', 'bye', 'pat', 'poke', 'boop', 'yeet', 'punch', 'dance', 'cry', 'smile', 'happy', 'sad', 'angry', 'excited', 'clap', 'facepalm', 'think', 'stare', 'wake', 'sleep', 'sing', 'laugh', 'blush', 'smack', 'shoot', 'kick', 'trap', 'scare', 'bully', 'tease', 'confuse', 'prank', 'explode', 'roast', 'spank', 'lick', 'bite', 'throw', 'bonk', 'comfort', 'nuzzle', 'snuggle', 'holdhands', 'handshake', 'highfive', 'thanks', 'thank', 'welcome']

async def anime_gif(ctx, action, member: discord.Member = None):
    async with aiohttp.ClientSession() as s:
        async with s.get(f"https://api.otakugifs.xyz/gif?reaction={action}") as r:
            url = (await r.json())['url']
    mention_txt = f"{ctx.author.mention} {action}s {member.mention}!" if member else f"{ctx.author.mention} is {action}ing!"
    await ctx.send(f"{mention_txt}\n{url}")

for f in FUN_LIST:
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
    @discord.ui.button(label="Game", style=discord.ButtonStyle.success)
    async def g(self, i, b): await i.response.send_message("🎮 `daily`, `weekly`, `lb`, `cf`, `rob`, `pray`, `start_egame`", ephemeral=True)
    @discord.ui.button(label="Mod", style=discord.ButtonStyle.danger)
    async def m(self, i, b): await i.response.send_message("🛠 `ban`, `kick`, `mute`, `unmute`, `role`, `dm`", ephemeral=True)
    @discord.ui.button(label="Fun", style=discord.ButtonStyle.primary)
    async def f(self, i, b): await i.response.send_message(f"✨ {', '.join(FUN_LIST[:10])}...", ephemeral=True)

@bot.command()
async def help(ctx): await ctx.send(f"{EMOJIS['help']} **Miku Help**", view=HelpView())

# --- WEB SERVER (FIXED SYNTAX) ---
app = Flask('')
@app.route('/')
def home_route(): 
    return "Miku Alive!", 200

if __name__ == "__main__":
    Thread(target=lambda: app.run(host='0.0.0.0', port=os.getenv("PORT", 8080)), daemon=True).start()
    daily_reminder.start(); bot.run(os.getenv('TOKEN'))
