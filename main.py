import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import json
import os

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents)

DATA_FILE = "data.json"

bot_enabled = True

# --------------------
# DATA KEZELÉS
# --------------------
def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

data = load_data()

# --------------------
# PR.TAG CHECK
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
        save_data(data)

@tasks.loop(hours=1)
async def check_members():
    if not bot_enabled:
        return

    now = datetime.utcnow()

    for guild in bot.guilds:
        for member in guild.members:

            if str(member.id) not in data:
                continue

            if not is_prtag(member):
                continue

            join_time = datetime.fromisoformat(data[str(member.id)])

            if now - join_time > timedelta(days=7):
                try:
                    await member.kick(reason="pr.tag lejárt")
                except:
                    pass

                del data[str(member.id)]
                save_data(data)

# --------------------
# /ELLENORZES
# --------------------
@bot.tree.command(name="ellenorzes")
async def ellenorzes(interaction: discord.Interaction):
    await interaction.response.send_message("🟢 Bot működik")

# --------------------
# /KI (bot leállítás logika)
# --------------------
@bot.tree.command(name="ki")
async def ki(interaction: discord.Interaction):
    global bot_enabled
    bot_enabled = False
    await interaction.response.send_message("🔴 Bot kikapcsolva")

# --------------------
# /BE
# --------------------
@bot.tree.command(name="be")
async def be(interaction: discord.Interaction):
    global bot_enabled
    bot_enabled = True
    await interaction.response.send_message("🟢 Bot bekapcsolva")


@bot.tree.command(name="refresh")
async def refresh(interaction: discord.Interaction):

    if not interaction.user.guild_permissions.staff:
        return await interaction.response.send_message("❌ Nincs jogod!", ephemeral=True)

    try:
        synced = await bot.tree.sync()
        await interaction.response.send_message(f"🔄 Frissítve! ({len(synced)} parancs)")
    except Exception as e:
        await interaction.response.send_message(f"Hiba: {e}")# --------------------
# /HOZZAAD (manuális user)
# --------------------
@bot.tree.command(name="hozzaad")
async def hozzaad(interaction: discord.Interaction, member: discord.Member):
    data[str(member.id)] = datetime.utcnow().isoformat()
    save_data(data)
    await interaction.response.send_message(f"➕ Hozzáadva: {member.name}")

# --------------------
# /KIVESZ
# --------------------
@bot.tree.command(name="kivesz")
async def kivesz(interaction: discord.Interaction, member: discord.Member):
    if str(member.id) in data:
        del data[str(member.id)]
        save_data(data)
    await interaction.response.send_message(f"🗑 Kivéve: {member.name}")

# --------------------
# /STATS
# --------------------
@bot.tree.command(name="stats")
async def stats(interaction: discord.Interaction):

    now = datetime.utcnow()
    msg = "📊 PR.TAG STATISZTIKA:\n\n"

    for guild in bot.guilds:
        for member in guild.members:

            if not is_prtag(member):
                continue

            if str(member.id) not in data:
                continue

            join_time = datetime.fromisoformat(data[str(member.id)])
            remaining = timedelta(days=7) - (now - join_time)

            sec = int(remaining.total_seconds())

            if sec > 0:
                h = sec // 3600
                m = (sec % 3600) // 60
                msg += f"{member.name} → {h}h {m}m maradt\n"
            else:
                msg += f"{member.name} → KÖZEL A KICKHEZ\n"

    await interaction.response.send_message(msg[:2000])

# --------------------
# READY
# --------------------
# --------------------
# READY
# --------------------
@bot.event
async def on_ready():
    print("Bot online")

    check_members.start()

    guild = discord.Object(id=1459639907004711127)

    try:
        synced = await bot.tree.sync(guild=guild)
        print(f"Guild sync: {len(synced)}")
    except Exception as e:
        print(e)
        
bot.run(TOKEN)
