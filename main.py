import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import json
import os

TOKEN = os.getenv("TOKEN")

# ÚJ SZERVER ID
GUILD_ID = 1501208722083545088

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "data.json"
bot_enabled = True

# --------------------
# MEMORY STORE
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
# PR TAG CHECK
# --------------------
def is_prtag(member):
    return any(r.name == "pr.tag" for r in member.roles)

# --------------------
# JOIN
# --------------------
@bot.event
async def on_member_join(member):
    if str(member.id) not in data:
        data[str(member.id)] = datetime.utcnow().isoformat()
        save_data()

# --------------------
# KICK CHECK LOOP
# --------------------
@tasks.loop(minutes=10)
async def check_members():
    if not bot_enabled:
        return

    now = datetime.utcnow()

    for guild in bot.guilds:
        for member in guild.members:

            if not is_prtag(member):
                continue

            if str(member.id) not in data:
                data[str(member.id)] = now.isoformat()
                save_data()
                continue

            join_time = datetime.fromisoformat(data[str(member.id)])

            if now - join_time > timedelta(days=7):
                try:
                    await member.kick(reason="pr.tag lejárt")
                except:
                    pass

                del data[str(member.id)]
                save_data()

# --------------------
# COMMAND GUILD
# --------------------
guild = discord.Object(id=GUILD_ID)

@bot.tree.command(name="ellenorzes", guild=guild)
async def ellenorzes(interaction: discord.Interaction):
    await interaction.response.send_message("🟢 Bot működik")

@bot.tree.command(name="ki", guild=guild)
async def ki(interaction: discord.Interaction):
    global bot_enabled
    bot_enabled = False
    await interaction.response.send_message("🔴 Kikapcsolva")

@bot.tree.command(name="be", guild=guild)
async def be(interaction: discord.Interaction):
    global bot_enabled
    bot_enabled = True
    await interaction.response.send_message("🟢 Bekapcsolva")

@bot.tree.command(name="hozzaad", guild=guild)
async def hozzaad(interaction: discord.Interaction, member: discord.Member):
    data[str(member.id)] = datetime.utcnow().isoformat()
    save_data()
    await interaction.response.send_message(f"➕ Hozzáadva: {member.name}")

@bot.tree.command(name="kivesz", guild=guild)
async def kivesz(interaction: discord.Interaction, member: discord.Member):
    if str(member.id) in data:
        del data[str(member.id)]
        save_data()
    await interaction.response.send_message(f"🗑 Kivéve: {member.name}")

@bot.tree.command(name="stats", guild=guild)
async def stats(interaction: discord.Interaction):

    now = datetime.utcnow()
    msg = "📊 PR TAG STATS:\n\n"

    for member_id, time_str in data.items():

        try:
            member = interaction.guild.get_member(int(member_id))
            if not member:
                continue

            if not is_prtag(member):
                continue

            join_time = datetime.fromisoformat(time_str)
            remaining = timedelta(days=7) - (now - join_time)

            sec = int(remaining.total_seconds())

            if sec > 0:
                h = sec // 3600
                m = (sec % 3600) // 60
                s = sec % 60
                msg += f"{member.name} → {h}h {m}m {s}s\n"
            else:
                msg += f"{member.name} → KICK SOON\n"

        except:
            continue

    await interaction.response.send_message(msg[:2000])

@bot.tree.command(name="refresh", guild=guild)
async def refresh(interaction: discord.Interaction):
    try:
        synced = await bot.tree.sync(guild=guild)
        await interaction.response.send_message(f"🔄 Sync kész ({len(synced)})")
    except Exception as e:
        await interaction.response.send_message(str(e))

# --------------------
# READY
# --------------------
@bot.event
async def on_ready():
    print("Bot online")

    load_data()
    check_members.start()

    try:
        synced = await bot.tree.sync(guild=guild)
        print(f"Synced: {len(synced)}")
    except Exception as e:
        print(e)

bot.run(TOKEN)
