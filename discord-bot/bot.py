import discord
from discord.ext import commands, tasks
from discord.ui import View, Button, Modal, TextInput
import sqlite3
import datetime

TOKEN = "MTQ3MTE4MzIxMDQzOTUxMjI1OQ.GULJKA.g2jqxyd894sBzTUl1uQpY2hL8xlcfWHodQPhbM"

# ====== ID-URI ======
CHANNEL_LOG = 1470325891161915513
CHANNEL_MEMBRI = 1471195719833489451
CHANNEL_ARHIVA = 1471195404212375552
CHANNEL_TASK = 1470325890801074203,1470325890528575571

ROL_CONDUCERE = 1470325888871563364

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ====== DATABASE ======
conn = sqlite3.connect("database.db")
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS membri(
    discord_id TEXT PRIMARY KEY,
    nume TEXT,
    cnp TEXT,
    grad TEXT,
    telefon TEXT,
    data_intrare TEXT,
    concediu INTEGER DEFAULT 14,
    invoiri INTEGER DEFAULT 0,
    puncte INTEGER DEFAULT 0,
    sanctiuni INTEGER DEFAULT 0,
    buletin TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS pontaj(
    discord_id TEXT,
    start TEXT,
    activ INTEGER
)
""")

conn.commit()

# ====== UTIL ======
def is_conducere(user):
    return ROL_CONDUCERE in [r.id for r in user.roles]

# ================== PONTAJ ==================

@bot.slash_command(name="pontaj")
async def pontaj(ctx):
    embed = discord.Embed(
        title="📋 Pontaj",
        description=(
            "Reguli:\n"
            "• Activitate Discord ON\n"
            "• Verificare periodică 20 min\n"
            "• Ieșire → oprire automată\n"
        ),
        color=0x2f3136
    )

    view = View()

    view.add_item(Button(label="🟢 Începe tura", style=discord.ButtonStyle.success, custom_id="start"))
    view.add_item(Button(label="🔴 Încheie tura", style=discord.ButtonStyle.danger, custom_id="stop"))
    view.add_item(Button(label="⏱ Vezi timpul", style=discord.ButtonStyle.secondary, custom_id="time"))

    await ctx.respond(embed=embed, view=view)

@bot.event
async def on_interaction(interaction):
    if not interaction.type == discord.InteractionType.component:
        return

    cid = interaction.data["custom_id"]
    uid = str(interaction.user.id)
    now = datetime.datetime.now().isoformat()

    # START
    if cid == "start":
        c.execute("INSERT INTO pontaj VALUES (?,?,?)", (uid, now, 1))
        conn.commit()
        await interaction.user.send("🟢 Pontaj început.")
        await interaction.response.send_message("Pontaj pornit.", ephemeral=True)

    # STOP
    if cid == "stop":
        c.execute("DELETE FROM pontaj WHERE discord_id=?", (uid,))
        conn.commit()
        await interaction.user.send("🔴 Pontaj încheiat.")
        await interaction.response.send_message("Pontaj oprit.", ephemeral=True)

# ================== ANGAJARE ==================

class AngajareModal(Modal):
    def __init__(self):
        super().__init__(title="Cerere de angajare")
        self.nume = TextInput(label="Nume Prenume")
        self.cnp = TextInput(label="CNP")
        self.exp = TextInput(label="Experiență")
        self.tel = TextInput(label="Număr telefon")
        self.buletin = TextInput(label="Link poză buletin")
        for i in [self.nume,self.cnp,self.exp,self.tel,self.buletin]:
            self.add_item(i)

    async def on_submit(self, interaction):
        data = datetime.date.today().isoformat()
        c.execute("INSERT OR REPLACE INTO membri VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (str(interaction.user.id), self.nume.value, self.cnp.value,
         "Recruit", self.tel.value, data, 14, 0, 0, 0, self.buletin.value))
        conn.commit()

        canal = bot.get_channel(CHANNEL_MEMBRI)
        await canal.send(f"📄 Fișă creată pentru {interaction.user.mention}")

        await interaction.user.send("✅ Cerere acceptată.\nFișa ta a fost creată.")
        await interaction.response.send_message("Cerere trimisă.", ephemeral=True)

@bot.slash_command(name="angajare")
async def angajare(ctx):
    await ctx.send_modal(AngajareModal())

# ================== PUNCTE ==================

@bot.slash_command(name="puncte")
async def puncte(ctx, membru: discord.Member, valoare: int):
    if not is_conducere(ctx.author):
        await ctx.respond("Nu ai permisiune.", ephemeral=True)
        return

    c.execute("SELECT puncte FROM membri WHERE discord_id=?", (str(membru.id),))
    r = c.fetchone()
    total = (r[0] if r else 0) + valoare

    c.execute("UPDATE membri SET puncte=? WHERE discord_id=?", (total, str(membru.id)))
    conn.commit()

    await membru.send(f"📊 Puncte modificate: {valoare}\n💠 Total: {total}")

    log = bot.get_channel(CHANNEL_LOG)
    await log.send(f"📊 {membru.mention} | {valoare} puncte | Total: {total}")

    await ctx.respond("Actualizat.", ephemeral=True)

# ================== SANCȚIUNI ==================

class SanctiuneModal(Modal):
    def __init__(self):
        super().__init__(title="Aplicare sancțiune")
        self.nume = TextInput(label="Nume Prenume")
        self.cnp = TextInput(label="CNP")
        self.tip = TextInput(label="Tip sancțiune (FW1/FW2/FW3/Avertisment)")
        self.motiv = TextInput(label="Motiv")
        for i in [self.nume,self.cnp,self.tip,self.motiv]:
            self.add_item(i)

    async def on_submit(self, interaction):
        await interaction.user.send("⚠️ Sancțiunea a fost înregistrată.")
        log = bot.get_channel(CHANNEL_LOG)
        await log.send(f"⚠️ Sancțiune aplicată:\n{self.nume.value} | {self.tip.value}\nMotiv: {self.motiv.value}")
        await interaction.response.send_message("Sancțiune aplicată.", ephemeral=True)

@bot.slash_command(name="sanctiune")
async def sanctiune(ctx):
    if not is_conducere(ctx.author):
        return await ctx.respond("Nu ai permisiune.", ephemeral=True)
    await ctx.send_modal(SanctiuneModal())

# ================== TASK ==================

@bot.slash_command(name="task")
async def task(ctx, grad: str, text: str):
    azi = datetime.date.today()
    final = azi + datetime.timedelta(days=6)

    msg = (
        f"📌 TASK\n\n"
        f"Task: {text}\n"
        f"Săptămâna: {azi} - {final}\n"
        f"Grad: {grad}\n\n"
        f"✅ Membri cu task:\n"
        f"❌ Membri fără task:\n"
        f"🏖 Membri în concediu:\n"
    )

    canal = bot.get_channel(CHANNEL_TASK)
    await canal.send(msg)
    await ctx.respond("Task creat.", ephemeral=True)

# ================== RESET LUNAR ==================

@tasks.loop(hours=24)
async def reset_lunar():
    azi = datetime.date.today()
    if azi.day == 1:
        c.execute("UPDATE membri SET concediu=14, invoiri=0")
        conn.commit()
        log = bot.get_channel(CHANNEL_LOG)
        await log.send("♻️ Reset lunar concedii + învoiri.")

reset_lunar.start()

# ================== READY ==================

@bot.event
async def on_ready():
    print("Bot online.")

bot.run(TOKEN)
