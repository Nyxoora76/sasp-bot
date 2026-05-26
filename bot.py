import os
import re
from datetime import datetime, timedelta

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# ===== CONFIG =====
TICKET_CATEGORY_NAME = "tickets"

ROLE_RECRUITER = "Recruteur"
ROLE_CHIEF = "Chief"
ROLE_UNDER_CHIEF = "Under Chief"

DISTRICT_NAME = "Vespucci"
MANUAL_URL = "https://docs.google.com/presentation/d/102XSbfok9SQtR7faQkzvRZBhyzThu90muxOMMo6j6pY/edit?usp=drivesdk"

# ===== IMAGES / LOGO =====
LOGO_URL = "https://cdn.discordapp.com/attachments/1483550389436678348/1508801901397934270/72fa040f-3627-4669-b5dc-2eeb2eb999dc_1.png?ex=6a16dcc5&is=6a158b45&hm=0f1d95f912f7fc3511247cb2f3f239e9e3c4bd904b8874f21c9a442207814bf1&"

CANDIDATURE_ACCEPT_IMAGE_URL = "https://cdn.discordapp.com/attachments/1483550389436678348/1508806054866321508/061e866e-6185-442e-80d5-7d5d5a885eae.png?ex=6a16e0a3&is=6a158f23&hm=92f6a5a679445272d648e5c6ca413fbd1a969f215530fd5ba88c299ebea54a5d&"
CANDIDATURE_REFUSE_IMAGE_URL = "https://cdn.discordapp.com/attachments/1483550389436678348/1508801900349362286/6ef1d9e9-9eef-4aa8-9e0c-16b06723595c_1.png?ex=6a16dcc5&is=6a158b45&hm=7c8054704873e8ecf374bba316793078682a033be7c55013503be5cd9c5d1ef7&"
ENTRETIEN_ACCEPT_IMAGE_URL = "https://cdn.discordapp.com/attachments/1483550389436678348/1508801900848615524/d60118fe-4483-4cbc-aedb-343b5e4a35be.png?ex=6a16dcc5&is=6a158b45&hm=a3f03a0a7aedc062879eeb618322c4fb3851680f8b0f6f8cc70f924e9ac98b87&"
ENTRETIEN_REFUSE_IMAGE_URL = "https://cdn.discordapp.com/attachments/1483550389436678348/1508801899074420917/9c05aae3-060d-4630-8738-a2dbb930c8a1.png?ex=6a16dcc4&is=6a158b44&hm=6187230b0b54761d7f2ae4e39594722ef2e3734462943a305bfb3a9fa319925d&"

DELAI_REFUS_JOURS = 2

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

pending_forms = {}


def get_role_by_name(guild: discord.Guild, role_name: str):
    return discord.utils.get(guild.roles, name=role_name)


def get_category_by_name(guild: discord.Guild, category_name: str):
    return discord.utils.get(guild.categories, name=category_name)


def parse_birthdate(date_str: str):
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y"):
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            pass
    return None


def calculate_age(birth_date: datetime) -> int:
    today = datetime.today()
    return today.year - birth_date.year - (
        (today.month, today.day) < (birth_date.month, birth_date.day)
    )


def sanitize_channel_name(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\-]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "candidat"


def format_date_fr(date_obj: datetime) -> str:
    mois_fr = {
        1: "janvier", 2: "février", 3: "mars", 4: "avril",
        5: "mai", 6: "juin", 7: "juillet", 8: "août",
        9: "septembre", 10: "octobre", 11: "novembre", 12: "décembre",
    }
    return f"{date_obj.day} {mois_fr[date_obj.month]} {date_obj.year} à {date_obj.strftime('%H:%M')}"


def build_candidature_accept_embed(recruiter_name: str, membre: discord.Member) -> discord.Embed:
    embed = discord.Embed(
        title="Candidature Acceptée — Vespucci",
        description=f"Le dossier de {membre.mention} a été retenu.",
        color=discord.Color.green()
    )
    embed.add_field(name="Instructions :", value="Veuillez lire attentivement les salons pour passer votre entretien.", inline=False)
    embed.add_field(name="Candidat", value=membre.mention, inline=False)
    embed.add_field(name="District", value=DISTRICT_NAME, inline=False)
    embed.set_thumbnail(url=LOGO_URL)
    embed.set_image(url=CANDIDATURE_ACCEPT_IMAGE_URL)
    embed.set_footer(text=f"LSPD Vespucci | Recruteur : {recruiter_name}")
    return embed


def build_candidature_refuse_embed(recruiter_name: str, membre: discord.Member, motif: str) -> discord.Embed:
    date_repost = datetime.now() + timedelta(days=DELAI_REFUS_JOURS)
    embed = discord.Embed(
        title="Candidature Refusée — Vespucci",
        description=f"Le dossier de {membre.mention} n'a pas été retenu.",
        color=discord.Color.red()
    )
    embed.add_field(
        name="Information",
        value=f"Vous êtes invité à réessayer dans deux jours.\nVotre compte pourra à nouveau postuler le **{format_date_fr(date_repost)}**.",
        inline=False
    )
    embed.add_field(name="Motif :", value=motif, inline=False)
    embed.add_field(name="Candidat", value=membre.mention, inline=False)
    embed.add_field(name="District", value=DISTRICT_NAME, inline=False)
    embed.set_thumbnail(url=LOGO_URL)
    embed.set_image(url=CANDIDATURE_REFUSE_IMAGE_URL)
    embed.set_footer(text=f"LSPD Vespucci | Recruteur : {recruiter_name}")
    return embed


def build_entretien_accept_embed(recruiter_name: str, membre: discord.Member) -> discord.Embed:
    embed = discord.Embed(
        title="Entretien Validé — Vespucci",
        description="Entretien validé : ✅ Félicitations, votre entretien est validé.\nVous avez **30 jours** pour poursuivre votre parcours.",
        color=discord.Color.green()
    )
    embed.add_field(name="Candidat", value=membre.mention, inline=False)
    embed.add_field(name="District", value=DISTRICT_NAME, inline=False)
    embed.set_thumbnail(url=LOGO_URL)
    embed.set_image(url=ENTRETIEN_ACCEPT_IMAGE_URL)
    embed.set_footer(text=f"LSPD Vespucci | Recruteur : {recruiter_name}")
    return embed


def build_entretien_refuse_embed(recruiter_name: str, membre: discord.Member, motif: str) -> discord.Embed:
    embed = discord.Embed(
        title="Entretien Refusé — Vespucci",
        description="Entretien refusé : ❌ Vous avez été refusé lors de votre passage entretien.",
        color=discord.Color.red()
    )
    embed.add_field(name="Motif :", value=motif, inline=False)
    embed.add_field(name="Candidat", value=membre.mention, inline=False)
    embed.add_field(name="District", value=DISTRICT_NAME, inline=False)
    embed.set_thumbnail(url=LOGO_URL)
    embed.set_image(url=ENTRETIEN_REFUSE_IMAGE_URL)
    embed.set_footer(text=f"LSPD Vespucci | Recruteur : {recruiter_name}")
    return embed


class ContinueRPView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.button(label="➡️ Continuer vers la partie RP", style=discord.ButtonStyle.primary)
    async def continue_rp(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RecruitmentRPModal())


class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Fermer le ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket_button_v1")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Fermeture du ticket dans 3 secondes...", ephemeral=True)
        await interaction.channel.delete(delay=3)


class RecruitmentPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🚔 Recrutement LSPD", style=discord.ButtonStyle.primary, custom_id="recruitment_panel_button_v1")
    async def recrutement(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RecruitmentHRPModal())


class RDVPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📅 Prise de rendez-vous", style=discord.ButtonStyle.primary, custom_id="rdv_button_v1")
    async def rdv(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = await create_simple_ticket(interaction.guild, interaction.user, "rdv")
        if not channel:
            await interaction.response.send_message("Impossible de créer le ticket. Vérifie la catégorie `tickets`.", ephemeral=True)
            return
        await interaction.response.send_message(f"✅ Ton ticket a été créé : {channel.mention}", ephemeral=True)

    @discord.ui.button(label="💼 Proposition de contrat", style=discord.ButtonStyle.secondary, custom_id="contrat_button_v1")
    async def contrat(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = await create_simple_ticket(interaction.guild, interaction.user, "contrat")
        if not channel:
            await interaction.response.send_message("Impossible de créer le ticket. Vérifie la catégorie `tickets`.", ephemeral=True)
            return
        await interaction.response.send_message(f"✅ Ton ticket a été créé : {channel.mention}", ephemeral=True)

    @discord.ui.button(label="👮 Police Academy", style=discord.ButtonStyle.success, custom_id="academy_button_v1")
    async def academy(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = await create_simple_ticket(interaction.guild, interaction.user, "academy")
        if not channel:
            await interaction.response.send_message("Impossible de créer le ticket. Vérifie la catégorie `tickets`.", ephemeral=True)
            return
        await interaction.response.send_message(f"✅ Ton ticket a été créé : {channel.mention}", ephemeral=True)


class LSPDBot(commands.Bot):
    async def setup_hook(self):
        self.add_view(RecruitmentPanelView())
        self.add_view(RDVPanelView())
        self.add_view(CloseTicketView())
        print("Views persistantes enregistrées.")


bot = LSPDBot(command_prefix="!", intents=intents, case_insensitive=True)


async def create_recruitment_ticket(guild: discord.Guild, user: discord.Member, form_data: dict):
    category = get_category_by_name(guild, TICKET_CATEGORY_NAME)
    if not category:
        return None

    role_recruiter = get_role_by_name(guild, ROLE_RECRUITER)
    role_chief = get_role_by_name(guild, ROLE_CHIEF)
    role_under_chief = get_role_by_name(guild, ROLE_UNDER_CHIEF)

    channel_name = f"recrutement-{sanitize_channel_name(user.display_name)}"

    for ch in guild.text_channels:
        if ch.category_id == category.id and ch.name == channel_name:
            return ch

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
        guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True, manage_messages=True, read_message_history=True),
    }

    for role in [role_recruiter, role_chief, role_under_chief]:
        if role:
            overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

    channel = await guild.create_text_channel(
        name=channel_name[:95],
        category=category,
        overwrites=overwrites,
        topic=f"Candidature recrutement | {user} | District: {DISTRICT_NAME}"
    )

    embed = discord.Embed(
        title="📁 Nouvelle candidature LSPD",
        description=f"Bienvenue {user.mention}, votre candidature a bien été envoyée.",
        color=discord.Color.blurple()
    )
    embed.add_field(name="District", value=DISTRICT_NAME, inline=False)
    embed.add_field(name="HRP - ID Unique", value=form_data["unique_id"], inline=True)
    embed.add_field(name="HRP - Date de naissance", value=form_data["irl_birthdate"], inline=True)
    embed.add_field(name="HRP - Heures serveur", value=form_data["fivem_hours"], inline=True)
    embed.add_field(name="RP - Nom et Prénom", value=form_data["rp_name"], inline=False)
    embed.add_field(name="RP - Diplôme obtenu", value=form_data["rp_diploma"], inline=True)
    embed.add_field(name="RP - Nationalité", value=form_data["rp_nationality"], inline=True)
    embed.add_field(name="RP - Numéro de téléphone", value=form_data["rp_phone"], inline=True)
    embed.add_field(name="RP - Lettre de motivation", value=form_data["rp_motivation"], inline=False)
    embed.set_footer(text="LSPD Vespucci")

    await channel.send(content=user.mention, embed=embed, view=CloseTicketView())
    return channel


async def create_simple_ticket(guild: discord.Guild, user: discord.Member, ticket_type: str):
    category = get_category_by_name(guild, TICKET_CATEGORY_NAME)
    if not category:
        return None

    role_recruiter = get_role_by_name(guild, ROLE_RECRUITER)
    role_chief = get_role_by_name(guild, ROLE_CHIEF)
    role_under_chief = get_role_by_name(guild, ROLE_UNDER_CHIEF)

    base_name = sanitize_channel_name(user.display_name)
    prefixes = {"rdv": "rdv", "contrat": "contrat", "academy": "academy"}
    channel_name = f"{prefixes.get(ticket_type, 'ticket')}-{base_name}"

    for ch in guild.text_channels:
        if ch.category_id == category.id and ch.name == channel_name:
            return ch

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
        guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True, manage_messages=True, read_message_history=True),
    }

    for role in [role_recruiter, role_chief, role_under_chief]:
        if role:
            overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

    channel = await guild.create_text_channel(
        name=channel_name[:95],
        category=category,
        overwrites=overwrites,
        topic=f"Ticket {ticket_type} | {user}"
    )

    titles = {
        "rdv": "📅 Ticket prise de rendez-vous",
        "contrat": "💼 Ticket proposition de contrat",
        "academy": "👮 Ticket Police Academy"
    }

    descs = {
        "rdv": "Explique clairement ta demande de rendez-vous.",
        "contrat": "Explique clairement ta proposition de contrat.",
        "academy": "Explique clairement ta demande concernant la Police Academy."
    }

    embed = discord.Embed(
        title=titles.get(ticket_type, "🎫 Ticket"),
        description=f"Bonjour {user.mention}.\n\n{descs.get(ticket_type, 'Explique ta demande.')}",
        color=discord.Color.green()
    )

    await channel.send(content=user.mention, embed=embed, view=CloseTicketView())
    return channel


class RecruitmentHRPModal(discord.ui.Modal, title="Partie HRP - Vespucci"):
    unique_id = discord.ui.TextInput(label="ID Unique", required=True, max_length=100)
    irl_birthdate = discord.ui.TextInput(label="Date de naissance HRP (> 15 ans)", placeholder="JJ/MM/AAAA", required=True, max_length=10)
    fivem_hours = discord.ui.TextInput(label="Nombre d'heures sur le serveur", required=True, max_length=20)

    async def on_submit(self, interaction: discord.Interaction):
        birth_date = parse_birthdate(str(self.irl_birthdate))
        if birth_date is None:
            await interaction.response.send_message("Format invalide. Utilise JJ/MM/AAAA.", ephemeral=True)
            return

        if calculate_age(birth_date) < 15:
            await interaction.response.send_message("Tu dois avoir au moins 15 ans IRL pour postuler.", ephemeral=True)
            return

        pending_forms[interaction.user.id] = {
            "unique_id": str(self.unique_id),
            "irl_birthdate": str(self.irl_birthdate),
            "fivem_hours": str(self.fivem_hours),
        }

        await interaction.response.send_message(
            "✅ Partie HRP enregistrée. Clique sur le bouton ci-dessous pour passer à la partie RP.",
            view=ContinueRPView(),
            ephemeral=True
        )


class RecruitmentRPModal(discord.ui.Modal, title="Partie RP - Vespucci"):
    rp_name = discord.ui.TextInput(label="Nom et Prénom", required=True, max_length=100)
    rp_diploma = discord.ui.TextInput(label="Diplôme obtenu", placeholder="Doit être un High School Diploma ou GED", required=True, max_length=100)
    rp_nationality = discord.ui.TextInput(label="Nationalité", required=True, max_length=100)
    rp_phone = discord.ui.TextInput(label="Numéro de téléphone", required=True, max_length=50)
    rp_motivation = discord.ui.TextInput(label="Lettre de motivation", required=True, style=discord.TextStyle.paragraph, max_length=1000)

    async def on_submit(self, interaction: discord.Interaction):
        saved = pending_forms.get(interaction.user.id)
        if not saved:
            await interaction.response.send_message("Session expirée. Recommence.", ephemeral=True)
            return

        form_data = {
            **saved,
            "rp_name": str(self.rp_name),
            "rp_diploma": str(self.rp_diploma),
            "rp_nationality": str(self.rp_nationality),
            "rp_phone": str(self.rp_phone),
            "rp_motivation": str(self.rp_motivation),
        }

        channel = await create_recruitment_ticket(interaction.guild, interaction.user, form_data)
        pending_forms.pop(interaction.user.id, None)

        if not channel:
            await interaction.response.send_message("Impossible de créer le ticket. Vérifie la catégorie `tickets` et les permissions du bot.", ephemeral=True)
            return

        await interaction.response.send_message(f"✅ Candidature envoyée dans {channel.mention}", ephemeral=True)


@bot.command()
async def test(ctx):
    await ctx.send("✅ Bot LSPD Vespucci OK")


@bot.command()
async def panel(ctx):
    embed = discord.Embed(
        title="🚨 Recrutement LSPD Vespucci",
        description="⚠️ Ce formulaire sera transmis au staff LSPD Vespucci.\nNe donne pas de mot de passe ni d'information sensible.\n\nClique sur le bouton pour commencer ta candidature.",
        color=discord.Color.blue()
    )
    embed.add_field(name="District ouvert", value=DISTRICT_NAME, inline=False)
    await ctx.send(embed=embed, view=RecruitmentPanelView())


async def candidature_acceptee(ctx, membre: discord.Member):
    role = get_role_by_name(ctx.guild, DISTRICT_NAME)
    if role is None:
        await ctx.send(f"❌ Le rôle **{DISTRICT_NAME}** est introuvable.")
        return

    try:
        await membre.add_roles(role, reason=f"Candidature acceptée par {ctx.author}")
    except discord.Forbidden:
        await ctx.send("❌ Je ne peux pas ajouter le rôle. Vérifie la hiérarchie des rôles du bot.")
        return

    embed = build_candidature_accept_embed(str(ctx.author), membre)
    await ctx.send(content=membre.mention, embed=embed)


async def candidature_refusee(ctx, membre: discord.Member, motif: str):
    embed = build_candidature_refuse_embed(str(ctx.author), membre, motif)
    await ctx.send(content=membre.mention, embed=embed)


async def entretien_valide(ctx, membre: discord.Member):
    role = get_role_by_name(ctx.guild, DISTRICT_NAME)
    if role is None:
        await ctx.send(f"❌ Le rôle **{DISTRICT_NAME}** est introuvable.")
        return

    try:
        await membre.add_roles(role, reason=f"Entretien validé par {ctx.author}")
    except discord.Forbidden:
        await ctx.send("❌ Je ne peux pas ajouter le rôle. Vérifie la hiérarchie des rôles du bot.")
        return

    embed = build_entretien_accept_embed(str(ctx.author), membre)
    await ctx.send(content=membre.mention, embed=embed)


async def entretien_refuse_action(ctx, membre: discord.Member, motif: str):
    embed = build_entretien_refuse_embed(str(ctx.author), membre, motif)
    await ctx.send(content=membre.mention, embed=embed)


@bot.command(name="accepte")
@commands.has_any_role(ROLE_RECRUITER, ROLE_CHIEF, ROLE_UNDER_CHIEF)
async def accepte(ctx, membre: discord.Member):
    await candidature_acceptee(ctx, membre)


@bot.command(name="refuse")
@commands.has_any_role(ROLE_RECRUITER, ROLE_CHIEF, ROLE_UNDER_CHIEF)
async def refuse(ctx, membre: discord.Member, *, motif: str = "Aucun motif précisé"):
    await candidature_refusee(ctx, membre, motif)


@bot.command(name="Entretien_ok")
@commands.has_any_role(ROLE_RECRUITER, ROLE_CHIEF, ROLE_UNDER_CHIEF)
async def entretien_ok(ctx, membre: discord.Member):
    await entretien_valide(ctx, membre)


@bot.command(name="Entretien_refuser")
@commands.has_any_role(ROLE_RECRUITER, ROLE_CHIEF, ROLE_UNDER_CHIEF)
async def entretien_refuser(ctx, membre: discord.Member, *, motif: str = "Aucun motif précisé"):
    await entretien_refuse_action(ctx, membre, motif)


@accepte.error
@refuse.error
@entretien_ok.error
@entretien_refuser.error
async def command_error(ctx, error):
    if isinstance(error, commands.MissingAnyRole):
        await ctx.send("❌ Tu n'as pas le rôle autorisé pour utiliser cette commande.")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ Membre introuvable. Mentionne bien la personne avec @.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ Membre introuvable. Utilise une vraie mention Discord.")
    else:
        await ctx.send(f"❌ Erreur : {error}")


@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user}")


if not TOKEN:
    print("❌ DISCORD_TOKEN introuvable dans Railway > Variables")
else:
    bot.run(TOKEN)
