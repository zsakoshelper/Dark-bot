import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import json
import os

TOKEN = os.getenv("TOKEN")

# SILENT FURY SZERVER ID
GUILD_ID = 1501208722083545088

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "data.json"
bot_enabled = True

# --------------------
# ADATOK
# --------------------
data = {}

def load_data():
    global data

    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
    except:
        data = {}

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# --------------------
# PR.TAG CHECK
# --------------------
def is_prtag(member):
    return any(role.name == "pr.tag" for role in member.roles)

# --------------------
# ÚJ TAG
# --------------------
@bot.event
async def on_member_join(member):

    if str(member.id) not in data:
        data[str(member.id)] = datetime.utcnow().isoformat()
        save_data()

# --------------------
# KICK LOOP
# --------------------
@tasks.loop(minutes=10)
async def check_members():

    global bot_enabled

    if not bot_enabled:
        return

    now = datetime.utcnow()

    for guild_obj in bot.guilds:

        for member in guild_obj.members:

            # csak pr.tag
            if not is_prtag(member):
                continue

            # ha nincs adat
            if str(member.id) not in data:
                data[str(member.id)] = now.isoformat()
                save_data()
                continue

            try:
                join_time = datetime.fromisoformat(data[str(member.id)])
            except:
                data[str(member.id)] = now.isoformat()
                save_data()
                continue

            remaining = timedelta(days=7) - (now - join_time)

            # kick
            if remaining.total_seconds() <= 0:

                try:
                    await member.kick(reason="Silent Fury pr.tag lejárt")
                except:
                    pass

                if str(member.id) in data:
                    del data[str(member.id)]
                    save_data()

# --------------------
# GUILD
# --------------------
guild = discord.Object(id=GUILD_ID)

# --------------------
# /ELLENORZES
# --------------------
@bot.tree.command(name="ellenorzes", guild=guild)
async def ellenorzes(interaction: discord.Interaction):

    await interaction.response.send_message(
        "🟢 Silent Fury bot működik"
    )

# --------------------
# /KI
# --------------------
@bot.tree.command(name="ki", guild=guild)
async def ki(interaction: discord.Interaction):

    global bot_enabled

    bot_enabled = False

    await interaction.response.send_message(
        "🔴 Silent Fury rendszer kikapcsolva"
    )

# --------------------
# /BE
# --------------------
@bot.tree.command(name="be", guild=guild)
async def be(interaction: discord.Interaction):

    global bot_enabled

    bot_enabled = True

    await interaction.response.send_message(
        "🟢 Silent Fury rendszer bekapcsolva"
    )

# --------------------
# /HOZZAAD
# --------------------
@bot.tree.command(name="hozzaad", guild=guild)
async def hozzaad(
    interaction: discord.Interaction,
    member: discord.Member
):

    data[str(member.id)] = datetime.utcnow().isoformat()

    save_data()

    await interaction.response.send_message(
        f"➕ {member.name} hozzáadva"
    )

# --------------------
# /KIVESZ
# --------------------
@bot.tree.command(name="kivesz", guild=guild)
async def kivesz(
    interaction: discord.Interaction,
    member: discord.Member
):

    if str(member.id) in data:

        del data[str(member.id)]

        save_data()

    await interaction.response.send_message(
        f"🗑 {member.name} kivéve"
    )

# --------------------
# /STATS
# --------------------
@bot.tree.command(name="stats", guild=guild)
async def stats(interaction: discord.Interaction):

    now = datetime.utcnow()

    msg = "📊 Silent Fury PR.TAG STATS\n\n"

    found = False

    for member_id, time_str in data.items():

        member = interaction.guild.get_member(int(member_id))

        if not member:
            continue

        if not is_prtag(member):
            continue

        try:
            join_time = datetime.fromisoformat(time_str)
        except:
            continue

        remaining = timedelta(days=7) - (now - join_time)

        seconds = int(remaining.total_seconds())

        if seconds <= 0:
            msg += f"{member.name} → KICK\n"
            found = True
            continue

        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        msg += (
            f"{member.name} → "
            f"{days}d {hours}h {minutes}m {secs}s\n"
        )

        found = True

    if not found:
        msg += "Nincs aktív pr.tag tag."

    await interaction.response.send_message(msg[:2000])

# --------------------
# /REFRESH
# --------------------
@bot.tree.command(name="refresh", guild=guild)
async def refresh(interaction: discord.Interaction):

    try:
        synced = await bot.tree.sync(guild=guild)

        await interaction.response.send_message(
            f"🔄 Frissítve ({len(synced)} parancs)"
        )

    except Exception as e:

        await interaction.response.send_message(
            f"Hiba: {e}"
        )

# --------------------
# READY
# --------------------
@bot.event
async def on_ready():

    print(f"Bot online: {bot.user}")

    load_data()

    # ne induljon el kétszer
    if not check_members.is_running():
        check_members.start()

    try:
        synced = await bot.tree.sync(guild=guild)
        print(f"Synced: {len(synced)}")

    except Exception as e:
        print(e)

# --------------------
# BOT START
# --------------------
bot.run(TOKEN)
