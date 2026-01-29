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
    "miku_ping": "<:miku_ping:1466456670522835046>>" # Replace with your Miku emoji ID
}

DEV_ID = 1081496970805399562
INVITE_URL = "https://discord.com/oauth2/authorize?client_id=1279757277309435914&permissions=8&integration_type=0&scope=bot"

# --- MULTI-PREFIX LOGIC (+, miku, @Miku) ---
async def get_prefix(bot, message):
    prefixes = ['+', 'miku ', 'Miku ']
    return commands.when_mentioned_or(*prefixes)(bot, message)

bot = commands.Bot(command_prefix=get_prefix, intents=discord.Intents.all(), help_command=None)

# --- OPTIMIZED WEB SERVER FOR CRONJOB ---
app = Flask('')

@app.route('/')
def home():
    return "Miku is Awake! <:yes:1466456663325282446>", 200

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web)
    t.daemon = True
    t.start()

# --- HELP UI (NORMAL TEXT + BUTTONS) ---
class HelpView(discord.ui.View):
    @discord.ui.button(label="Moderation", emoji=EMOJIS['bankkick'], style=discord.ButtonStyle.danger)
    async def mod(self, interaction: discord.Interaction, button: discord.ui.Button):
        text = "🛠 **Moderation:** `+ban`, `+kick`, `+mute`, `+unmute`, `+role`, `+dm`"
        await interaction.response.send_message(text, ephemeral=True)

    @discord.ui.button(label="Anime Fun", emoji="✨", style=discord.ButtonStyle.success)
    async def fun(self, interaction: discord.Interaction, button: discord.ui.Button):
        text = "🎬 **Fun:** `+slap`, `+kill`, `+tickle`, `+hug`, `+cuddle`, `+nod`, `+fuck`, `+beat`, `+sex`, `+kiss`"
        await interaction.response.send_message(text, ephemeral=True)

    @discord.ui.button(label="Utility", emoji=EMOJIS['info'], style=discord.ButtonStyle.secondary)
    async def util(self, interaction: discord.Interaction, button: discord.ui.Button):
        text = "⚙️ **Utility:** `+userinfo`, `+serverinfo`, `+ping`, `+info`"
        await interaction.response.send_message(text, ephemeral=True)

# --- EVENTS ---
@bot.event
async def on_message(message):
    if message.author.bot: return
    if bot.user.mentioned_in(message) and len(message.content.strip().split()) == 1:
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Add Me", url=INVITE_URL))
        return await message.reply(f"Hello! I'm Miku, a multifunctional bot! {EMOJIS['yes']}\nMy prefixes are `+` and `miku `. How can I help you today?", view=view)
    await bot.process_commands(message)

# --- UTILITY COMMANDS (NEW) ---
@bot.command()
async def userinfo(ctx, member: discord.Member = None):
    member = member or ctx.author
    roles = [role.mention for role in member.roles[1:]] # Exclude @everyone
    
    text = (
        f"👤 **User Info for {member.name}**\n"
        f"**ID:** {member.id}\n"
        f"**Joined Discord:** {member.created_at.strftime('%Y-%m-%d')}\n"
        f"**Joined Server:** {member.joined_at.strftime('%Y-%m-%d') if member.joined_at else 'N/A'}\n"
        f"**Roles:** {', '.join(roles) if roles else 'None'}\n"
        f"**Top Role:** {member.top_role.mention}"
    )
    await ctx.send(text)

@bot.command()
async def serverinfo(ctx):
    guild = ctx.guild
    text = (
        f"🏰 **Server Info: {guild.name}**\n"
        f"**Owner:** {guild.owner}\n"
        f"**ID:** {guild.id}\n"
        f"**Created At:** {guild.created_at.strftime('%Y-%m-%d')}\n"
        f"**Total Members:** {guild.member_count}\n"
        f"**Channels:** {len(guild.channels)} ({len(guild.text_channels)} text / {len(guild.voice_channels)} voice)\n"
        f"**Roles:** {len(guild.roles)}"
    )
    await ctx.send(text)

@bot.command()
async def ping(ctx):
    latency = random.randint(983, 1234)
    await ctx.send(f"{EMOJIS['miku_ping']} Pong! Latency: **{latency}ms**")

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
        unit = time[-1].lower()
        amount = int(time[:-1])
        seconds = amount * {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}.get(unit, 60)
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
async def dm(ctx, member: discord.Member, *, message):
    if not ctx.author.guild_permissions.manage_messages: return
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

# --- INFO & HELP ---
@bot.command()
async def info(ctx):
    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="Report/Feedback", url="https://discord.gg/zCfBYyR5U6"))
    view.add_item(discord.ui.Button(label="Add Me", url=INVITE_URL))
    text = (
        f"🌸 **Bot Name:** Miku\n"
        f"📜 **Language:** Python\n"
        f"⌨️ **Prefix:** `+` , `miku ` , @Miku\n"
        f"👑 **Dev:** NebulaVex\n"
        f"🆔 **Dev User:** 4v3h"
    )
    await ctx.send(text, view=view)

@bot.command()
async def help(ctx):
    await ctx.send(f"{EMOJIS['help']} **Miku Help Menu**\nSelect a category below:", view=HelpView())

# --- DEV ONLY ---
@bot.command()
async def stats(ctx):
    if ctx.author.id != DEV_ID: return
    await ctx.send(f"Servers: {len(bot.guilds)} | Users: {sum(g.member_count for g in bot.guilds)}")

if __name__ == "__main__":
    keep_alive()
    token = os.getenv('TOKEN')
    if token:
        bot.run(token)
    else:
        print("Missing TOKEN!")
