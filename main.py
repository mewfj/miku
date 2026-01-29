import os
import discord
from discord.ext import commands
import datetime
import asyncio
import yt_dlp
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Miku is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# Call this before bot.run(token)
keep_alive()

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

# Basic Queue
queues = {}

# --- HELP COMMAND ---
@bot.command()
async def help(ctx):
    embed = discord.Embed(title=f"{EMOJIS['help']} Miku Command List", color=0x00ffcc)
    embed.add_field(name="Music", value=f"{EMOJIS['music']} `play/p`, `stop/s`, `skip`, `queue` (Anime themed!)", inline=False)
    embed.add_field(name="Moderation", value=f"{EMOJIS['bankkick']} `ban`, `kick`, `mute`, `unmute`, `role`, `dm`", inline=False)
    embed.add_field(name="Info", value=f"{EMOJIS['info']} `info`, `stats`, `admin`", inline=False)
    await ctx.send(embed=embed)

# --- MUSIC COMMANDS ---
@bot.command(aliases=['p'])
async def play(ctx, *, search):
    if not ctx.author.voice:
        return await ctx.send("Join a voice channel first!")
    
    # Check if music is already playing to show your custom message
    if ctx.voice_client and ctx.voice_client.is_playing():
        await ctx.send(f"{EMOJIS['musicplay']} Music has been added to the queue! {EMOJIS['dancing']}")
        # (Add logic to append to 'queues' here)
        return

    # Simplified join and play (requires FFmpeg on Render)
    vc = await ctx.author.voice.channel.connect()
    await ctx.send(f"{EMOJIS['musicplay']} Now playing: **{search}** {EMOJIS['yes']}")

@bot.command(aliases=['s'])
async def stop(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send(f"{EMOJIS['success']} Music stopped. Bye bye!")

@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send(f"{EMOJIS['musicplay']} Skipped the track!")

@bot.command()
async def queue(ctx):
    await ctx.send(f"{EMOJIS['music']} The current queue is empty (or logic not implemented yet!)")

# --- MODERATION COMMANDS ---
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="No reason provided"):
    await member.ban(reason=reason)
    await ctx.send(f"{EMOJIS['bankkick']} Banned {member.name} | Reason: {reason}")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="No reason provided"):
    await member.kick(reason=reason)
    await ctx.send(f"{EMOJIS['bankkick']} Kicked {member.name} | Reason: {reason}")

@bot.command()
@commands.has_permissions(moderate_members=True)
async def mute(ctx, member: discord.Member, time: str, *, reason="No reason provided"):
    seconds = 0
    t = time.lower()
    if 's' in t: seconds = int(t.replace('s',''))
    elif 'm' in t: seconds = int(t.replace('m','')) * 60
    elif 'hrs' in t: seconds = int(t.replace('hrs','')) * 3600
    elif 'd' in t: seconds = int(t.replace('d','')) * 86400
    
    await member.timeout(datetime.timedelta(seconds=seconds), reason=reason)
    await ctx.send(f"{EMOJIS['success']} {member.mention} has been muted for {time}.")

@bot.command()
@commands.has_permissions(moderate_members=True)
async def unmute(ctx, member: discord.Member):
    await member.timeout(None)
    await ctx.send(f"{EMOJIS['yes']} Unmuted {member.mention}.")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def role(ctx, member: discord.Member, role: discord.Role):
    if role in member.roles:
        await member.remove_roles(role)
        await ctx.send(f"{EMOJIS['settings']} Removed {role.name} from {member.name}")
    else:
        await member.add_roles(role)
        await ctx.send(f"{EMOJIS['success']} Added {role.name} to {member.name}")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def dm(ctx, member: discord.Member, *, message):
    try:
        await member.send(f"Message from {ctx.guild.name} staff: {message}")
        await ctx.send(f"{EMOJIS['success']} DM sent to {member.name}")
    except:
        await ctx.send("Could not DM this user.")

# --- INFO & OWNER COMMANDS ---
@bot.command()
async def info(ctx):
    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="Report/Rate", url="https://discord.gg/zCfBYyR5U6"))
    
    embed = discord.Embed(title=f"{EMOJIS['info']} Miku Bot Info", color=0x00ffcc)
    embed.add_field(name="Developer", value="NebulaVex", inline=True)
    embed.add_field(name="Username", value="4v3h", inline=True)
    embed.add_field(name="Server", value="[Join Here](https://discord.gg/zCfBYyR5U6)", inline=False)
    await ctx.send(embed=embed, view=view)

@bot.command()
async def stats(ctx):
    if ctx.author.id != DEV_ID: return
    await ctx.send(f"Serving {len(bot.guilds)} servers and {sum(g.member_count for g in bot.guilds)} users.")

@bot.command()
async def admin(ctx):
    if ctx.author.id != DEV_ID: return
    # Generates a select menu with servers
    options = [discord.SelectOption(label=g.name, value=str(g.id)) for g in bot.guilds[:25]]
    select = discord.ui.Select(placeholder="Select a server to leave", options=options)
    
    async def callback(interaction):
        if interaction.user.id != DEV_ID: return
        guild = bot.get_guild(int(select.values[0]))
        await guild.leave()
        await interaction.response.send_message(f"Left {guild.name}")

    select.callback = callback
    view = discord.ui.View()
    view.add_item(select)
    await ctx.send("Admin Panel:", view=view)

if __name__ == "__main__":
    token = os.getenv('TOKEN')
    if token:
        bot.run(token)
    else:
        print("ERROR: No TOKEN found in environment variables!")
