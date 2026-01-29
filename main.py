import discord
from discord.ext import commands
import datetime
import asyncio
import os
import yt_dlp
from flask import Flask
from threading import Thread

# --- EMOJIS ---
EMOJIS = {
    "musicplay": "<:musicplay:1466456872163737620>",
    "bankkick": "<:bankkick:1466456864194560315>",
    "settings": "<:settings:1466456847681847439>",
    "help": "<:help:1466456820578128054>",
    "music": "<:music:1466456797320843327>",
    "info": "<:info:1466456677166612490>",
    "dancing": "<:dancing:1466456670522835046>",
    "success": "<:success:1466456666890305688>",
    "yes": "<:yes:1466456663325282446>"
}

DEV_ID = 1081496970805399562
bot = commands.Bot(command_prefix='+', intents=discord.Intents.all(), help_command=None)

# --- WEB SERVER ---
app = Flask('')
@app.route('/')
def home(): return "Miku V2 is Online!"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

# --- MUSIC SETUP ---
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
YDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist': True, 'quiet': True}
queues = {}

# --- UI COMPONENTS (HELP CMD) ---
class HelpRow(discord.ui.View):
    def __init__(self):
        super().__init__()
    
    @discord.ui.button(label="Music", emoji=EMOJIS['music'], style=discord.ButtonStyle.blurple)
    async def music_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🎵 **Music:** `+p`, `+s`, `+skip`, `+queue`", ephemeral=True)

    @discord.ui.button(label="Mod", emoji=EMOJIS['bankkick'], style=discord.ButtonStyle.danger)
    async def mod_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🛠 **Mod:** `+ban`, `+kick`, `+mute`, `+unmute`, `+role`, `+dm`", ephemeral=True)

# --- COMMANDS ---

@bot.command()
async def help(ctx):
    # Help in a row-type message with emojis
    msg = f"{EMOJIS['help']} **Miku Help Menu**\nClick the buttons below for commands!"
    await ctx.send(msg, view=HelpRow())

@bot.command(aliases=['p'])
async def play(ctx, *, search):
    if not ctx.author.voice: return await ctx.send(f"{EMOJIS['settings']} Join VC!")
    
    # Ensure audio library is loaded
    if not discord.opus.is_loaded():
        try: discord.opus.load_opus('libopus.so.0')
        except: pass

    if ctx.voice_client and ctx.voice_client.is_playing():
        await ctx.send(f"{EMOJIS['musicplay']} Added to queue! {EMOJIS['dancing']}")
        return queues.setdefault(ctx.guild.id, []).append(search)

    vc = ctx.voice_client or await ctx.author.voice.channel.connect()
    
    async with ctx.typing():
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(f"ytsearch:{search}", download=False)['entries'][0]
            url = info['url']
        
        # Audio playback with FFmpeg
        vc.play(discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS))
        await ctx.send(f"{EMOJIS['music']} **Playing:** {info['title']} {EMOJIS['yes']}")

@bot.command(aliases=['s'])
async def stop(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send(f"{EMOJIS['success']} Disconnected.")

@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send(f"{EMOJIS['musicplay']} Track skipped.")

@bot.command()
async def queue(ctx):
    q = queues.get(ctx.guild.id, [])
    await ctx.send(f"{EMOJIS['music']} Queue: " + (", ".join(q) if q else "Empty"))

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.send(f"{EMOJIS['bankkick']} Banned {member.name}")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    await ctx.send(f"{EMOJIS['bankkick']} Kicked {member.name}")

@bot.command()
@commands.has_permissions(moderate_members=True)
async def mute(ctx, member: discord.Member, time: str, *, reason=None):
    s = int(time[:-1]) * {'s':1, 'm':60, 'h':3600, 'd':86400}[time[-1]]
    await member.timeout(datetime.timedelta(seconds=s), reason=reason)
    await ctx.send(f"{EMOJIS['success']} Muted {member.name} for {time}")

@bot.command()
async def unmute(ctx, member: discord.Member):
    await member.timeout(None)
    await ctx.send(f"{EMOJIS['yes']} Unmuted {member.name}")

@bot.command()
async def role(ctx, member: discord.Member, role: discord.Role):
    if role in member.roles: await member.remove_roles(role)
    else: await member.add_roles(role)
    await ctx.send(f"{EMOJIS['settings']} Toggled role: {role.name}")

@bot.command()
async def dm(ctx, member: discord.Member, *, text):
    if ctx.author.guild_permissions.manage_messages:
        await member.send(f"Admin: {text}")
        await ctx.send(f"{EMOJIS['success']} DM Sent.")

@bot.command()
async def info(ctx):
    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="Report/Rate", url="https://discord.gg/zCfBYyR5U6", style=discord.ButtonStyle.link))
    await ctx.send(f"{EMOJIS['info']} **Dev:** NebulaVex (4v3h)\n**Server:** https://discord.gg/zCfBYyR5U6", view=view)

@bot.command()
async def stats(ctx):
    if ctx.author.id == DEV_ID:
        await ctx.send(f"Servers: {len(bot.guilds)} | Users: {sum(g.member_count for g in bot.guilds)}")

@bot.command()
async def admin(ctx):
    if ctx.author.id != DEV_ID: return
    options = [discord.SelectOption(label=g.name, value=str(g.id)) for g in bot.guilds[:25]]
    select = discord.ui.Select(placeholder="Select server to leave", options=options)
    async def cb(i):
        if i.user.id == DEV_ID:
            await bot.get_guild(int(select.values[0])).leave()
            await i.response.send_message("Left.")
    select.callback = cb
    view = discord.ui.View(); view.add_item(select)
    await ctx.send("Admin Panel:", view=view)

if __name__ == "__main__":
    keep_alive()
    bot.run(os.getenv('TOKEN'))
