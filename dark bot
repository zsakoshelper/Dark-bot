import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import json
import os

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents)

DATA_FILE = "users.json"
bot_enabled = True

# --------------------
# ADATOK
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
# BELÉPÉS
# --------------------
@bot.event
async def on_member_join(member):
    data[str(member.id)] = datetime.utcnow().isoformat()
    save_data(data)

# --------------------
# 7 NAP CHECK + KICK
# --------------------
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
# /ELLENŐRZÉS
# --------------------
@bot.tree.command(name="ellenorzes")
async def ellenorzes(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"🟢 Bot működik\n📡 Ping: {round(bot.latency*1000)}ms"
    )

# --------------------
# READY
# --------------------
@bot.event
async def on_ready():
    print("Bot online")
    check_members.start()
    await bot.tree.sync()

bot.run(TOKEN)
