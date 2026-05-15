import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import json
import os

TOKEN = os.getenv("TOKEN")

GUILD_ID = 1501208722083545088

intents = discord.Intents.all()

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

DATA_FILE = "data.json"

bot_enabled = True

data = {}

# --------------------
# LOAD DATA
# --------------------
def load_data():
    global data

    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
    except:
        data = {}

# --------------------
# SAVE DATA
# --------------------
def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# --------------------
# PR.TAG CHECK
# --------------------
def is_prtag(member):
    return any(role.name.lower() == "pr.tag" for role in member.roles)

# --------------------
# MEMBER JOIN
# --------------------
@bot.event
async def on_member_join(member):

    if str(member.id) not in data:

        data[str(member.id)] = datetime.utcnow().isoformat()

        save_data()

# --------------------
# CHECK MEMBERS
# --------------------
@tasks.loop(minutes=10)
async def check_members():

    global bot_enabled

    if not bot_enabled:
        return

    now = datetime.utcnow()

    for guild in bot.guilds:

        for member in guild.members:

            # csak pr.tag
            if not is_prtag(member):
                continue

            # nincs adat
            if str(member.id) not in data:

                data[str(member.id)] = now.isoformat()

                save_data()

                continue

            try:
                join_time = datetime.fromisoformat(
                    data[str(member.id)]
                )

            except:

                data[str(member.id)] = now.isoformat()

                save_data()

                continue

            remaining = timedelta(days=7) - (now - join_time)

            # kick
            if remaining.total_seconds() <= 0:

                try:
                    await member.kick(
                        reason="Silent Fury pr.tag lejárt"
                    )

                except:
                    pass

                if str(member.id) in data:

                    del data[str(member.id)]

                    save_data()

# --------------------
# /ELLENORZES
# --------------------
@bot.tree.command(name="ellenorzes")
async def ellenorzes(interaction: discord.Interaction):

    await interaction.response.send_message(
        "🟢 Silent Fury bot működik"
    )

# --------------------
# /KI
# --------------------
@bot.tree.command(name="ki")
async def ki(interaction: discord.Interaction):

    global bot_enabled

    bot_enabled = False

    await interaction.response.send_message(
        "🔴 Rendszer kikapcsolva"
    )

# --------------------
# /BE
# --------------------
@bot.tree.command(name="be")
async def be(interaction: discord.Interaction):

    global bot_enabled

    bot_enabled = True

    await interaction.response.send_message(
        "🟢 Rendszer bekapcsolva"
    )

# --------------------
# /HOZZAAD
# --------------------
@bot.tree.command(name="hozzaad")
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
@bot.tree.command(name="kivesz")
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
@bot.tree.command(name="stats")
async def stats(interaction: discord.Interaction):

    now = datetime.utcnow()

    msg = "📊 Silent Fury PR.TAG STATS\n\n"

    found = False

    for member_id, time_str in data.items():

        try:

            member = interaction.guild.get_member(
                int(member_id)
            )

            if not member:
                continue

            if not is_prtag(member):
                continue

            join_time = datetime.fromisoformat(time_str)

            remaining = timedelta(days=7) - (
                now - join_time
            )

            seconds = int(
                remaining.total_seconds()
            )

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
                f"{days}d "
                f"{hours}h "
                f"{minutes}m "
                f"{secs}s\n"
            )

            found = True

        except:
            continue

    if not found:

        msg += "Nincs aktív pr.tag tag."

    await interaction.response.send_message(
        msg[:2000]
    )

# --------------------
# /REFRESH
# --------------------
@bot.tree.command(name="refresh")
async def refresh(interaction: discord.Interaction):

    try:

        guild = discord.Object(
            id=GUILD_ID
        )

        synced = await bot.tree.sync(
            guild=guild
        )

        await interaction.response.send_message(
            f"🔄 Frissítve ({len(synced)})"
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

    if not check_members.is_running():

        check_members.start()

    try:

        guild = discord.Object(
            id=GUILD_ID
        )

        synced = await bot.tree.sync(
            guild=guild
        )

        print(
            f"Synced: {len(synced)}"
        )

    except Exception as e:

        print(e)

# --------------------
# START
# --------------------
bot.run(TOKEN)
