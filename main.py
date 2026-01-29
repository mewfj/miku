import discord
from discord.ext import commands
import datetime
import asyncio
import os
import yt_dlp
from flask import Flask
from threading import Thread

# --- EMOJI DICTIONARY ---
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
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='+', intents=intents, help_command=None)

# --- WEB SERVER FOR RENDER ---
app = Flask('')
@app.route('/')
def home(): return "Miku is online!"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

# --- MUSIC CONFIG ---
YDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist': 'True', 'quiet': True}
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}
queues = {}

# --- HELP COMMAND ---
@bot.command()
async def help(ctx):
    embed = discord.Embed(title=f"{EMOJIS['help']} Miku Bot Help", color=0x00ffff)
    embed.add_field(name="🎵 Music", value="`+play / +p`, `+stop / +s`, `+skip`, `+queue` (Anime style!)", inline=False)
    embed.add_field(name="🛠 Moderation", value="`+ban`, `+kick`, `+mute`, `+unmute`, `+role`, `+dm` (Mod only)", inline=False)
    embed.add_field(name="ℹ️ Info", value="`+info`, `+stats` (Dev), `+admin` (Dev)", inline=False)
    await ctx.send(embed=embed)

# --- MUSIC COMMANDS ---
@bot.command(aliases=['p'])
async def play(ctx, *, search):
    if not ctx.author.voice:
        return await ctx.send(f"{EMOJIS['settings']} Join a Voice Channel first!")

    if ctx.guild.id not in queues: queues[ctx.guild.id] = []

    if ctx.voice_client and ctx.voice_client.is_playing():
        queues[ctx.guild.id].append(search)
        return await ctx.send(f"{EMOJIS['musicplay']} Music added to queue! {EMOJIS['dancing']}")

    vc = ctx.voice_client or await ctx.author.voice.channel.connect()
    
    with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
        info = ydl.extract_info(f"ytsearch:{search}", download=False)['entries'][0]
        url = info['url']
        title = info['title']
    
    vc.play(discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS))
    await ctx.send(f"{EMOJIS['music']} Playing: **{title}** {EMOJIS['yes']}")

@bot.command(aliases=['s'])
async def stop(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send(f"{EMOJIS['success']} Stopped and left VC.")

@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send(f"{EMOJIS['musicplay']} Skipped!")

@bot.command()
async def queue(ctx):
    q_list = queues.get(ctx.guild.id, [])
    if not q_list: return await ctx.send(f"{EMOJIS['music']} Queue is empty.")
    await ctx.send(f"{EMOJIS['help']} **Next in Queue:**\n" + "\n".join(q_list))

# --- MODERATION COMMANDS ---
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="None"):
    await member.ban(reason=reason)
    await ctx.send(f"{EMOJIS['bankkick']} Banned {member.mention}")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="None"):
    await member.kick(reason=reason)
    await ctx.send(f"{EMOJIS['bankkick']} Kicked {member.mention}")

@bot.command()
@commands.has_permissions(moderate_members=True)
async def mute(ctx, member: discord.Member, time: str, *, reason="None"):
    seconds = 0
    t = time.lower()
    if 's' in t: seconds = int(t.replace('s',''))
    elif 'm' in t: seconds = int(t.replace('m','')) * 60
    elif 'hrs' in t: seconds = int(t.replace('hrs','')) * 3600
    elif 'd' in t: seconds = int(t.replace('d','')) * 86400
    await member.timeout(datetime.timedelta(seconds=seconds), reason=reason)
    await ctx.send(f"{EMOJIS['success']} Muted {member.mention} for {time}.")

@bot.command()
@commands.has_permissions(moderate_members=True)
async def unmute(ctx, member: discord.Member):
    await member.timeout(None)
    await ctx.send(f"{EMOJIS['yes']} Unmuted {member.mention}.")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def role(ctx, member: discord.Member, role: discord.Role):
    if role in member.roles: await member.remove_roles(role)
    else: await member.add_roles(role)
    await ctx.send(f"{EMOJIS['settings']} Toggled role {role.name} for {member.name}")

@bot.command()
async def dm(ctx, member: discord.Member, *, text):
    if not ctx.author.guild_permissions.manage_messages: return
    await member.send(f"Admin Message: {text}")
    await ctx.send(f"{EMOJIS['success']} DM sent.")

# --- INFO & ADMIN ---
@bot.command()
async def info(ctx):
    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="Report/Rate", url="https://discord.gg/zCfBYyR5U6"))
    embed = discord.Embed(title=f"{EMOJIS['info']} Miku Info", color=0x00ffff)
    embed.add_field(name="Dev", value="NebulaVex (4v3h)")
    await ctx.send(embed=embed, view=view)

@bot.command()
async def stats(ctx):
    if ctx.author.id != DEV_ID: return
    await ctx.send(f"Servers: {len(bot.guilds)} | Users: {sum(g.member_count for g in bot.guilds)}")

@bot.command()
async def admin(ctx):
    if ctx.author.id != DEV_ID: return
    options = [discord.SelectOption(label=g.name, value=str(g.id)) for g in bot.guilds[:25]]
    select = discord.ui.Select(placeholder="Leave a server", options=options)
    async def cb(interaction):
        if interaction.user.id != DEV_ID: return
        g = bot.get_guild(int(select.values[0]))
        await g.leave()
        await interaction.response.send_message(f"Left {g.name}")
    select.callback = cb
    view = discord.ui.View(); view.add_item(select)
    await ctx.send("Admin Panel:", view=view)

# --- RUN ---
if __name__ == "__main__":
    token = os.getenv('TOKEN')
    if token:
        keep_alive()
        bot.run(token)
    else:
        print("Set the TOKEN variable in Render dashboard!")
