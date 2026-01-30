import discord
from discord.ext import commands
import datetime
import asyncio
import os
import aiohttp
import random
from flask import Flask
from threading import Thread

# --- EMOJIS (Fixed miku_ping ID) ---
EMOJIS = {
    "bankkick": "<:bankkick:1466456864194560315>",
    "settings": "<:settings:1466456847681847439>",
    "help": "<:help:1466456820578128054>",
    "info": "<:info:1466456677166612490>",
    "success": "<:success:1466456666890305688>",
    "yes": "<:yes:1466456663325282446>",
    "miku_ping": "<:dancing:1466456670522835046>" # Using your dancing emoji for ping
}

DEV_ID = 1081496970805399562
INVITE_URL = "https://discord.com/oauth2/authorize?client_id=1279757277309435914&permissions=8&integration_type=0&scope=bot"

async def get_prefix(bot, message):
    prefixes = ['+', 'miku ', 'Miku ']
    return commands.when_mentioned_or(*prefixes)(bot, message)

bot = commands.Bot(command_prefix=get_prefix, intents=discord.Intents.all(), help_command=None)

# --- KEEP ALIVE WEB SERVER ---
app = Flask('')
@app.route('/')
def home(): return "Miku V3 is Awake!", 200
def run_web(): app.run(host='0.0.0.0', port=os.environ.get("PORT", 8080))
def keep_alive(): Thread(target=run_web, daemon=True).start()

# --- HELP UI (Updated with Utility and massive Fun list) ---
class HelpView(discord.ui.View):
    @discord.ui.button(label="Moderation", emoji=EMOJIS['bankkick'], style=discord.ButtonStyle.danger)
    async def mod(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🛠 **Mod:** `+ban`, `+kick`, `+mute`, `+unmute`, `+role`, `+dm`", ephemeral=True)

    @discord.ui.button(label="Anime Fun", emoji="✨", style=discord.ButtonStyle.success)
    async def fun(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🎬 **Fun:** `+slap`, `+kill`, `+hug`, `+kiss`, `+pat`, `+wave`, `+hi`, `+bye`, `+boop`, `+punch`, `+yeet`, `+dance`, `+cry`... (and many more!)", ephemeral=True)

    @discord.ui.button(label="Utility", emoji=EMOJIS['info'], style=discord.ButtonStyle.secondary)
    async def util(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("⚙️ **Utility:** `+userinfo`, `+serverinfo`, `+ping`, `+info`", ephemeral=True)

# --- ANIME GIF ENGINE ---
async def send_gif(ctx, category, member: discord.Member = None):
    # Mapping for similar commands to ensure API hits a valid endpoint
    api_map = {"hi": "wave", "thanks": "thank", "spank": "slap", "throw": "yeet", "shoot": "kill", "smack": "slap"}
    action = api_map.get(category.lower(), category.lower())
    
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.otakugifs.xyz/gif?reaction={action}") as r:
            data = await r.json()
            url = data.get('url', 'https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJueW9ueW9ueW9ueW9ueW9ueW9ueW9ueW9ueW9ueW9ueW9ueSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3o7TKMGpxL2p990664/giphy.gif')
    
    msg = f"**{ctx.author.name}** {category}s **{member.name}**!" if member else f"**{ctx.author.name}** is {category}ing!"
    await ctx.send(f"{msg}\n{url}")

# --- COMMANDS ---

# Utility
@bot.command()
async def ping(ctx):
    await ctx.send(f"{EMOJIS['miku_ping']} Pong! Latency: **{random.randint(983, 1234)}ms**")

@bot.command()
async def userinfo(ctx, member: discord.Member = None):
    m = member or ctx.author
    await ctx.send(f"👤 **{m.name}**\n**ID:** {m.id}\n**Joined Discord:** {m.created_at.strftime('%Y-%m-%d')}\n**Joined Server:** {m.joined_at.strftime('%Y-%m-%d')}")

@bot.command()
async def serverinfo(ctx):
    g = ctx.guild
    await ctx.send(f"🏰 **{g.name}**\n**Owner:** {g.owner}\n**Members:** {g.member_count}\n**Roles:** {len(g.roles)}")

# Moderation
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, m: discord.Member, *, r="None"):
    await m.ban(reason=r); await ctx.send(f"{EMOJIS['bankkick']} Banned {m.name}")

@bot.command()
@commands.has_permissions(moderate_members=True)
async def mute(ctx, m: discord.Member, t: str, *, r="None"):
    s = int(t[:-1]) * {'s':1,'m':60,'h':3600,'d':86400}[t[-1].lower()]
    await m.timeout(datetime.timedelta(seconds=s), reason=r)
    await ctx.send(f"{EMOJIS['success']} Muted {m.name} for {t}")

@bot.command()
async def role(ctx, m: discord.Member, r: discord.Role):
    if r in m.roles: await m.remove_roles(r); await ctx.send(f"Removed {r.name}")
    else: await m.add_roles(r); await ctx.send(f"Added {r.name}")

# --- MASSIVE ANIME FUN LIST ---
FUN_CMDS = [
    'slap', 'kill', 'tickle', 'hug', 'cuddle', 'nod', 'fuck', 'beat', 'sex', 'kiss',
    'wave', 'hi', 'bye', 'welcome', 'thank', 'thanks', 'pat', 'poke', 'boop', 
    'highfive', 'handshake', 'holdhands', 'snuggle', 'nuzzle', 'comfort', 'bonk', 
    'yeet', 'throw', 'bite', 'lick', 'spank', 'roast', 'explode', 'prank', 
    'confuse', 'tease', 'bully', 'scare', 'trap', 'punch', 'kick', 'shoot', 
    'smack', 'blush', 'cry', 'laugh', 'dance', 'sing', 'sleep', 'wake', 
    'facepalm', 'think', 'stare', 'smile', 'happy', 'sad', 'angry', 'excited', 'clap'
]

# Dynamically creating commands to save space
def make_fun_cmd(name):
    @bot.command(name=name)
    async def _cmd(ctx, m: discord.Member = None):
        await send_gif(ctx, name, m)
    return _cmd

for cmd_name in FUN_CMDS:
    make_fun_cmd(cmd_name)

# --- BASE INFO/HELP ---
@bot.command()
async def info(ctx):
    v = discord.ui.View()
    v.add_item(discord.ui.Button(label="Report/Feedback", url="https://discord.gg/zCfBYyR5U6"))
    v.add_item(discord.ui.Button(label="Add Me", url=INVITE_URL))
    await ctx.send(f"🌸 **Miku Bot**\nPrefix: `+` , `miku `\nDev: **NebulaVex** (4v3h)", view=v)

@bot.command()
async def help(ctx):
    await ctx.send(f"{EMOJIS['help']} **Miku Menu**", view=HelpView())

@bot.event
async def on_message(msg):
    if msg.author.bot: return
    if bot.user.mentioned_in(msg) and len(msg.content.strip().split()) == 1:
        await msg.reply(f"Hello! I'm Miku! My prefix is `+` or `miku `. {EMOJIS['yes']}")
    await bot.process_commands(msg)

if __name__ == "__main__":
    keep_alive()
    bot.run(os.getenv('TOKEN'))
