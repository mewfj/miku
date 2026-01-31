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

# --- EMOJIS & CONFIG ---
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

# --- DATABASE & DATA ---
def load_data():
    if not os.path.exists('data.json'): return {"users": {}, "guilds": {}, "status": "default"}
    try:
        with open('data.json', 'r') as f: return json.load(f)
    except: return {"users": {}, "guilds": {}, "status": "default"}

def save_data(data):
    with open('data.json', 'w') as f: json.dump(data, f, indent=4)

# --- STATUS ENGINE ---
@tasks.loop(seconds=60)
async def status_updater():
    data = load_data()
    if data.get("status") == "default":
        total_members = sum(g.member_count for g in bot.guilds)
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"{total_members} members"))

# --- 8 AM ANNOUNCEMENT ---
@tasks.loop(time=datetime.time(hour=8, minute=0))
async def daily_reminder():
    data = load_data()
    for guild_id, channel_id in data["guilds"].items():
        channel = bot.get_channel(channel_id)
        if channel:
            await channel.send("🌸 **Ohayo Gozaimasu!** It's time to check your `daily` and play the Miku game! ✨")

# --- GAME LOGIC ---
@bot.command()
@commands.has_permissions(administrator=True)
async def start_egame(ctx):
    data = load_data()
    data["guilds"][str(ctx.guild.id)] = ctx.channel.id # Save channel for morning msgs
    for m in ctx.guild.members:
        if not m.bot:
            uid = str(m.id)
            data["users"][uid] = data["users"].get(uid, 0) + 500
    save_data(data)
    await ctx.send(f"🌸 **Ohayo!** The game has started in **{ctx.guild.name}**! Arigato for enabling Miku! Everyone received **500 points**! ✨")

@bot.command()
async def daily(ctx):
    data = load_data(); uid = str(ctx.author.id)
    data["users"][uid] = data["users"].get(uid, 0) + 1000
    save_data(data); await ctx.send(f"🎁 **Arigato!** You claimed your daily **1,000 points**! Sugoi!")

@bot.command()
async def weekly(ctx):
    data = load_data(); uid = str(ctx.author.id)
    data["users"][uid] = data["users"].get(uid, 0) + 10000
    save_data(data); await ctx.send(f"🔥 **Omedetou!** You received **10,000 weekly points**! ✨")

@bot.command()
async def give(ctx, member: discord.Member, amt: int):
    data = load_data(); uid, tid = str(ctx.author.id), str(member.id)
    if data["users"].get(uid, 0) < amt or amt <= 0: return await ctx.send("Gomen, you don't have enough points!")
    data["users"][uid] -= amt; data["users"][tid] = data["users"].get(tid, 0) + amt
    save_data(data); await ctx.send(f"🤝 **Arigato!** {ctx.author.name} gave **{amt} points** to {member.name}!")

@bot.command()
async def cf(ctx, amt: int):
    data = load_data(); uid = str(ctx.author.id)
    if amt > data["users"].get(uid, 0): return await ctx.send("Gomen, not enough points!")
    if random.choice([True, False]):
        data["users"][uid] += amt
        await ctx.send(f"🪙 **Yatta!** You won **{amt}** points! Arigato luck!")
    else:
        data["users"][uid] -= amt
        await ctx.send(f"🪙 **Gomen...** You lost **{amt}** points. Don't be sad!")
    save_data(data)

@bot.command(aliases=['lb'])
async def leaderboard(ctx):
    data = load_data()
    server_ids = [m.id for m in ctx.guild.members if not m.bot]
    lb = sorted([(u, b) for u, b in data["users"].items() if int(u) in server_ids], key=lambda x: x[1], reverse=True)
    
    # Using Embed for Silent Mentions (Zero ping)
    embed = discord.Embed(title=f"🏆 {ctx.guild.name} Leaderboard", color=0x00ffff)
    for i, (u, b) in enumerate(lb[:5], 1):
        rank = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"#{i}"
        embed.description = embed.description or ""
        embed.description += f"{rank} <@{u}>: **{b}**\n"
    await ctx.send(embed=embed) # Embed mentions are silent/no-ping by default

# --- ANIME FUN ---
FUN_LIST = ['slap', 'kill', 'tickle', 'hug', 'cuddle', 'nod', 'fuck', 'beat', 'sex', 'kiss', 'wave', 'hi', 'bye', 'welcome', 'thank', 'thanks', 'pat', 'poke', 'boop', 'highfive', 'handshake', 'holdhands', 'snuggle', 'nuzzle', 'comfort', 'bonk', 'yeet', 'throw', 'bite', 'lick', 'spank', 'roast', 'explode', 'prank', 'confuse', 'tease', 'bully', 'scare', 'trap', 'shoot', 'smack', 'blush', 'cry', 'laugh', 'dance', 'sing', 'sleep', 'wake', 'facepalm', 'think', 'stare', 'smile', 'happy', 'sad', 'angry', 'excited', 'clap']

async def anime_gif(ctx, action, member: discord.Member = None):
    async with aiohttp.ClientSession() as s:
        async with s.get(f"https://api.otakugifs.xyz/gif?reaction={action}") as r:
            url = (await r.json())['url']
    txt = f"**{ctx.author.mention}** {action}ing **{member.mention}**!" if member else f"**{ctx.author.mention}** is {action}ing!"
    await ctx.send(f"{txt}\n{url}")

for f in FUN_LIST:
    if not bot.get_command(f):
        @bot.command(name=f)
        async def _f(ctx, m: discord.Member = None, name=f): await anime_gif(ctx, name, m)

# --- MODERATION (Unchanged) ---
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, m: discord.Member, *, r="None"):
    await m.ban(reason=r); await ctx.send(f"{EMOJIS['bankkick']} Banned **{m.name}**")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, m: discord.Member, *, r="None"):
    await m.kick(reason=r); await ctx.send(f"{EMOJIS['bankkick']} Kicked **{m.name}**")

# --- DEV ONLY SECRET TOOLS ---
@bot.command(hidden=True)
async def adh(ctx):
    if ctx.author.id != DEV_ID: return
    await ctx.send("🤫 **Dev Secrets:** `+stats`, `+admin`, `+cstatus`, `+add_money`")

@bot.command()
async def cstatus(ctx, type: str, *, name: str):
    if ctx.author.id != DEV_ID: return
    data = load_data()
    if name.lower() == "default":
        data["status"] = "default"; await ctx.send("Status reset to Member Count.")
    else:
        data["status"] = "custom"
        t_map = {"playing": discord.ActivityType.playing, "watching": discord.ActivityType.watching, "streaming": discord.ActivityType.streaming}
        await bot.change_presence(activity=discord.Activity(type=t_map.get(type.lower(), discord.ActivityType.playing), name=name))
        await ctx.send(f"Status changed to {type}: {name}")
    save_data(data)

@bot.command()
async def stats(ctx):
    if ctx.author.id == DEV_ID: await ctx.send(f"Servers: {len(bot.guilds)} | Users: {sum(g.member_count for g in bot.guilds)}")

# --- UI & HELP ---
@bot.command()
async def help(ctx):
    v = discord.ui.View()
    v.add_item(discord.ui.Button(label="Add Me", url=INVITE_URL))
    
    text = (
        f"🌸 **Miku Help Menu**\n"
        f"🛠 **Mod:** `ban`, `kick`, `mute`, `unmute`, `role`, `dm`\n"
        f"🎮 **Game:** `start_egame`, `daily`, `weekly`, `give`, `lb`, `cf`, `rob`, `pray`\n"
        f"⚙️ **Util:** `info`, `userinfo`, `serverinfo`, `ping`\n"
        f"✨ **Fun:** `{', '.join(FUN_LIST[:8])}...`"
    )
    await ctx.send(text, view=v)

@bot.event
async def on_message(msg):
    if msg.author.bot: return
    if bot.user.mentioned_in(msg) and len(msg.content.strip().split()) == 1:
        v = discord.ui.View(); v.add_item(discord.ui.Button(label="Add Me", url=INVITE_URL))
        return await msg.reply(f"Ohayo! I'm Miku! Add me to your server to play games and moderate! {EMOJIS['yes']}", view=v)
    await bot.process_commands(msg)

@bot.event
async def on_ready():
    status_updater.start(); daily_reminder.start()
    print("Miku Ready!")

# --- FLASK ---
app = Flask(''); @app.route('/')
def home(): return "Miku Ultimate Online!", 200

if __name__ == "__main__":
    Thread(target=lambda: app.run(host='0.0.0.0', port=os.getenv("PORT", 8080)), daemon=True).start()
    bot.run(os.getenv('TOKEN'))
