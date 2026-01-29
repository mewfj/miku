import discord
from discord.ext import commands
import datetime
import asyncio
import os
import aiohttp
import random
from flask import Flask
from threading import Thread

# --- EMOJIS ---
EMOJIS = {
    "bankkick": "<:bankkick:1466456864194560315>",
    "settings": "<:settings:1466456847681847439>",
    "help": "<:help:1466456820578128054>",
    "info": "<:info:1466456677166612490>",
    "success": "<:success:1466456666890305688>",
    "yes": "<:yes:1466456663325282446>",
    "miku": "<:miku_ping:123456789012345678>" # Replace with your Miku emoji ID
}

DEV_ID = 1081496970805399562
INVITE_URL = "https://discord.com/oauth2/authorize?client_id=1279757277309435914&permissions=8&integration_type=0&scope=bot"

# --- UPDATED MULTI-PREFIX LOGIC ---
async def get_prefix(bot, message):
    # This allows: +cmd, @Miku cmd, and miku cmd
    prefixes = ['+', 'miku ', 'Miku '] # Added both lowercase and uppercase Miku
    return commands.when_mentioned_or(*prefixes)(bot, message)

bot = commands.Bot(command_prefix=get_prefix, intents=discord.Intents.all(), help_command=None)

# --- WEB SERVER ---
app = Flask('')
@app.route('/')
def home(): return "Miku V2 is Online!"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

# --- HELP UI (NO EMBEDS) ---
class HelpView(discord.ui.View):
    @discord.ui.button(label="Moderation", emoji=EMOJIS['bankkick'], style=discord.ButtonStyle.danger)
    async def mod(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            f"🛠 **Moderation:** `+ban`, `+kick`, `+mute`, `+unmute`, `+role`, `+dm`", ephemeral=True
        )

    @discord.ui.button(label="Anime Fun", emoji="✨", style=discord.ButtonStyle.success)
    async def fun(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            f"🎬 **Fun:** `+slap`, `+kill`, `+tickle`, `+hug`, `+cuddle`, `+nod`, `+fuck`, `+beat`, `+sex`, `+kiss`", ephemeral=True
        )

# --- EVENTS ---
@bot.event
async def on_message(message):
    if message.author.bot: return
    
    # Polite Response to Tag
    if bot.user.mentioned_in(message) and len(message.content.strip().split()) == 1:
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Add Me", url=INVITE_URL))
        return await message.reply(f"Hello! I'm Miku, a multifunctional bot! {EMOJIS['yes']}\nMy prefix is `+` or you can tag me. How can I help you today?", view=view)
    
    await bot.process_commands(message)

# --- MODERATION ---
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="No reason provided"):
    await member.ban(reason=reason)
    await ctx.send(f"{EMOJIS['bankkick']} **{member.name}** has been banned. | Reason: {reason}")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="No reason provided"):
    await member.kick(reason=reason)
    await ctx.send(f"{EMOJIS['bankkick']} **{member.name}** has been kicked. | Reason: {reason}")

@bot.command()
@commands.has_permissions(moderate_members=True)
async def mute(ctx, member: discord.Member, time: str, *, reason="No reason provided"):
    try:
        unit = time[-1]
        amount = int(time[:-1])
        seconds = amount * {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}.get(unit.lower(), 60)
        await member.timeout(datetime.timedelta(seconds=seconds), reason=reason)
        await ctx.send(f"{EMOJIS['success']} Muted **{member.name}** for {time}.")
    except:
        await ctx.send("Use format: `23s`, `5m`, `2h`, `1d`!")

@bot.command()
@commands.has_permissions(moderate_members=True)
async def unmute(ctx, member: discord.Member):
    await member.timeout(None)
    await ctx.send(f"{EMOJIS['yes']} Unmuted **{member.name}**.")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def role(ctx, member: discord.Member, role: discord.Role):
    if role in member.roles:
        await member.remove_roles(role)
        await ctx.send(f"{EMOJIS['settings']} Removed {role.name} from {member.name}.")
    else:
        await member.add_roles(role)
        await ctx.send(f"{EMOJIS['success']} Added {role.name} to {member.name}.")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def dm(ctx, member: discord.Member, *, message):
    await member.send(f"**Message from Staff:** {message}")
    await ctx.send(f"{EMOJIS['success']} DM sent to {member.name}.")

# --- ANIME FUN ---
async def send_gif(ctx, category, member: discord.Member = None):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.otakugifs.xyz/gif?reaction={category}") as r:
            data = await r.json()
            url = data['url']
    
    text = f"**{ctx.author.name}** {category}s **{member.name}**!" if member else f"**{ctx.author.name}** is {category}ing!"
    await ctx.send(f"{text}\n{url}")

@bot.command()
async def slap(ctx, m: discord.Member = None): await send_gif(ctx, "slap", m)
@bot.command()
async def kill(ctx, m: discord.Member = None): await send_gif(ctx, "kill", m)
@bot.command()
async def tickle(ctx, m: discord.Member = None): await send_gif(ctx, "tickle", m)
@bot.command()
async def hug(ctx, m: discord.Member = None): await send_gif(ctx, "hug", m)
@bot.command()
async def cuddle(ctx, m: discord.Member = None): await send_gif(ctx, "cuddle", m)
@bot.command()
async def nod(ctx, m: discord.Member = None): await send_gif(ctx, "nod", m)
@bot.command()
async def fuck(ctx, m: discord.Member = None): await send_gif(ctx, "fuck", m)
@bot.command()
async def beat(ctx, m: discord.Member = None): await send_gif(ctx, "beat", m)
@bot.command()
async def sex(ctx, m: discord.Member = None): await send_gif(ctx, "sex", m)
@bot.command()
async def kiss(ctx, m: discord.Member = None): await send_gif(ctx, "kiss", m)

# --- UTILITY ---
@bot.command()
async def ping(ctx):
    latency = random.randint(983, 1234)
    await ctx.send(f"{EMOJIS['miku']} Pong! Latency: **{latency}ms**")

@bot.command()
async def help(ctx):
    await ctx.send(f"{EMOJIS['help']} **Miku Help Menu**\nCommands are grouped below. Select a button!", view=HelpView())

@bot.command()
async def info(ctx):
    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="Report/Feedback", url="https://discord.gg/zCfBYyR5U6"))
    view.add_item(discord.ui.Button(label="Add Me", url=INVITE_URL))
    
    await ctx.send(
        f"🌸 **Bot Name:** Miku\n"
        f"📜 **Language:** Python\n"
        f"⌨️ **Prefix:** `+` / @Miku\n"
        f"👑 **Dev:** NebulaVex\n"
        f"🆔 **Dev User:** 4v3h", view=view
    )

if __name__ == "__main__":
    keep_alive()
    bot.run(os.getenv('TOKEN'))
