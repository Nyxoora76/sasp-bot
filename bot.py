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

DEPARTMENT_NAME = "LSPD"
DISTRICT_NAME = "Vespucci"
FOOTER_TEXT = "LSPD Vespucci | Recruteur"

MANUAL_URL = "https://docs.google.com/presentation/d/102XSbfok9SQtR7faQkzvRZBhyzThu90muxOMMo6j6pY/edit?usp=drivesdk"

LOGO_URL = "https://cdn.discordapp.com/attachments/1483550389436678348/1495335411726155876/Capture_decran_2026-04-19_100807.png"

CANDIDATURE_ACCEPT_IMAGE_URL = "https://cdn.discordapp.com/attachments/1483550389436678348/1499676174589235260/ChatGPT_Image_1_mai_2026_09_37_35.png"
CANDIDATURE_REFUSE_IMAGE_URL = "https://cdn.discordapp.com/attachments/1483550389436678348/1499676432979460176/ChatGPT_Image_1_mai_2026_09_38_22.png"
ENTRETIEN_ACCEPT_IMAGE_URL = "https://cdn.discordapp.com/attachments/1483550389436678348/1499676096378048584/ChatGPT_Image_1_mai_2026_09_37_13.png"
ENTRETIEN_REFUSE_IMAGE_URL = "https://cdn.discordapp.com/attachments/1483550389436678348/1499676075691868170/ChatGPT_Image_1_mai_2026_09_37_08.png"

DELAI_REFUS_JOURS = 2

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

pending_forms = {}


def get_role_by_name(guild, role_name):
    return discord.utils.get(guild.roles, name=role_name)


def get_category_by_name(guild, category_name):
    return discord.utils.get(guild.categories, name=category_name)


def parse_birthdate(date_str):
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y"):
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            pass
    return None


def calculate_age(birth_date):
    today = datetime.today()
    return today.year - birth_date.year - (
        (today.month, today.day) < (birth_date.month, birth_date.day)
    )


def sanitize_channel_name(text):
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\-]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "candidat"


def format_date_fr(date_obj):
    mois_fr = {
        1: "janvier", 2: "février", 3: "mars", 4: "avril",
        5: "mai", 6: "juin", 7: "juillet", 8: "août",
        9: "septembre", 10: "octobre", 11: "novembre", 12: "décembre",
    }
    return f"{date_obj.day} {mois_fr[date_obj.month]} {date_obj.year} à {date_obj.strftime('%H:%M')}"


# ===== EMBEDS CANDIDATURE =====
def build_candidature_accept_embed(recruiter_name, membre):
    embed = discord.Embed(
        title="Candidature Acceptée — Vespucci",
        description=f"Le dossier de {membre.mention} a été retenu.",
        color=discord.Color.green()
    )

    embed.add_field(
        name="Instructions :",
        value="Veuillez lire attentivement les salons pour passer votre entretien.",
        inline=False
    )
    embed.add_field(name="Candidat", value=membre.mention, inline=False)
    embed.add_field(name="District", value=DISTRICT_NAME, inline=False)

    embed.set_thumbnail(url=LOGO_URL)
    embed.set_image(url=CANDIDATURE_ACCEPT_IMAGE_URL)
    embed.set_footer(text=f"{FOOTER_TEXT} : {recruiter_name}")
    return embed


def build_candidature_refuse_embed(recruiter_name, membre, motif):
    date_repost = datetime.now() + timedelta(days=DELAI_REFUS_JOURS)

    embed = discord.Embed(
        title="Candidature Refusée — Vespucci",
        description=f"Le dossier de {membre.mention} n'a pas été retenu.",
        color=discord.Color.red()
    )

    embed.add_field(
        name="Information",
        value=(
            "Vous êtes invité à réessayer dans deux jours.\n"
            f"Votre compte pourra à nouveau postuler le **{format_date_fr(date_repost)}**."
        ),
        inline=False
    )
    embed.add_field(name="Motif :", value=motif, inline=False)
    embed.add_field(name="Candidat", value=membre.mention, inline=False)
    embed.add_field(name="District", value=DISTRICT_NAME, inline=False)

    embed.set_thumbnail(url=LOGO_URL)
    embed.set_image(url=CANDIDATURE_REFUSE_IMAGE_URL)
    embed.set_footer(text=f"{FOOTER_TEXT} : {recruiter_name}")
    return embed


# ===== EMBEDS ENTRETIEN =====
def build_entretien_accept_embed(recruiter_name, membre):
    embed = discord.Embed(
        title="Entretien Validé — Vespucci",
        description=(
            "Entretien validé : ✅ Félicitations, votre entretien est validé.\n"
            "Vous avez **30 jours** pour poursuivre votre parcours."
        ),
        color=discord.Color.green()
    )

    embed.add_field(name="Candidat", value=membre.mention, inline=False)
    embed.add_field(name="District", value=DISTRICT_NAME, inline=False)

    embed.set_thumbnail(url=LOGO_URL)
    embed.set_image(url=ENTRETIEN_ACCEPT_IMAGE_URL)
    embed.set_footer(text=f"{FOOTER_TEXT} : {recruiter_name}")
    return embed


def build_entretien_refuse_embed(recruiter_name, membre, motif):
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
    embed.set_footer(text=f"{FOOTER_TEXT} : {recruiter_name}")
    return embed


# ===== VIEWS =====
class ContinueRPView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.button(label="➡️ Continuer vers la partie RP", style=discord.ButtonStyle.primary)
    async def continue_rp(self, interaction, button):
        await interaction.response.send_modal(RecruitmentRPModal())


class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🔒 Fermer le ticket",
        style=discord.ButtonStyle.danger,
        custom_id="close_ticket_button_v1"
    )
    async def close_ticket(self, interaction, button):
        await interaction.response.send_message("Fermeture du ticket dans 3 secondes...", ephemeral=True)
        await interaction.channel.delete(delay=3)


class RecruitmentPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🚔 Recrutement LSPD",
        style=discord.ButtonStyle.primary,
        custom_id="recruitment_panel_button_v1"
    )
    async def recrutement(self, interaction, button):
        await interaction.response.send_modal(RecruitmentHRPModal())


class RDVPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📅 Prise de rendez-vous", style=discord.ButtonStyle.primary, custom_id="rdv_button_v1")
    async def rdv(self, interaction, button):
        channel = await create_simple_ticket(interaction.guild, interaction.user, "rdv")
        if not channel:
            await interaction.response.send_message("Impossible de créer le ticket.", ephemeral=True)
            return
        await interaction.response.send_message(f"✅ Ton ticket a été créé : {channel.mention}", ephemeral=True)

    @discord.ui.button(label="💼 Proposition de contrat", style=discord.ButtonStyle.secondary, custom_id="contrat_button_v1")
    async def contrat(self, interaction, button):
        channel = await create_simple_ticket(interaction.guild, interaction.user, "contrat")
        if not channel:
            await interaction.response.send_message("Impossible de créer le ticket.", ephemeral=True)
            return
        await interaction.response.send_message(f"✅ Ton ticket a été créé : {channel.mention}", ephemeral=True)

    @discord.ui.button(label="👮 Police Academy", style=discord.ButtonStyle.success, custom_id="academy_button_v1")
    async def academy(self, interaction, button):
        channel = await create_simple_ticket(interaction.guild, interaction.user, "academy")
        if not channel:
            await interaction.response.send_message("Impossible de créer le ticket.", ephemeral=True)
            return
        await interaction.response.send_message(f"✅ Ton ticket a été créé : {channel.mention}", ephemeral=True)


class LSPDBot(commands.Bot):
    async def setup_hook(self):
        self.add_view(RecruitmentPanelView())
        self.add_view(RDVPanelView())
        self.add_view(CloseTicketView())
        print("Views persistantes enregistrées.")


bot = LSPDBot(command_prefix="!", intents=intents, case_insensitive=True)


# ===== TICKETS =====
async def create_recruitment_ticket(guild, user, form_data):
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
        guild.me: discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            manage_channels=True,
            manage_messages=True,
            read_message_history=True
        ),
    }

    for role in [role_recruiter, role_chief, role_under_chief]:
        if role:
            overwrites[role] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True
            )

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


async def create_simple_ticket(guild, user, ticket_type):
    category = get_category_by_name(guild, TICKET_CATEGORY_NAME)
    if not category:
        return None

    role_recruiter = get_role_by_name(guild, ROLE_RECRUITER)
    role_chief = get_role_by_name(guild, ROLE_CHIEF)
    role_under_chief = get_role_by_name(guild, ROLE_UNDER_CHIEF)

    base_name = sanitize_channel_name(user.display_name)
    channel_name = f"{ticket_type}-{base_name}"

    for ch in guild.text_channels:
        if ch.category_id == category.id and ch.name == channel_name:
            return ch

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
        guild.me: discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            manage_channels=True,
            manage_messages=True,
            read_message_history=True
        ),
    }

    for role in [role_recruiter, role_chief, role_under_chief]:
        if role:
            overwrites[role] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True
            )

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


# ===== MODALS =====
class RecruitmentHRPModal(discord.ui.Modal, title="Partie HRP - LSPD Vespucci"):
    unique_id = discord.ui.TextInput(label="ID Unique", required=True, max_length=100)
    irl_birthdate = discord.ui.TextInput(
        label="Date de naissance HRP (> 15 ans)",
        placeholder="JJ/MM/AAAA",
        required=True,
        max_length=10
    )
    fivem_hours = discord.ui.TextInput(label="Nombre d'heures sur le serveur", required=True, max_length=20)

    async def on_submit(self, interaction):
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
            "✅ Partie HRP enregistrée. Clique sur le bouton pour passer à la partie RP.",
            view=ContinueRPView(),
            ephemeral=True
        )


class RecruitmentRPModal(discord.ui.Modal, title="Partie RP - LSPD Vespucci"):
    rp_name = discord.ui.TextInput(label="Nom et Prénom", required=True, max_length=100)
    rp_diploma = discord.ui.TextInput(label="Diplôme obtenu", required=True, max_length=100)
    rp_nationality = discord.ui.TextInput(label="Nationalité", required=True, max_length=100)
    rp_phone = discord.ui.TextInput(label="Numéro de téléphone", required=True, max_length=50)
    rp_motivation = discord.ui.TextInput(
        label="Lettre de motivation",
        required=True,
        style=discord.TextStyle.paragraph,
        max_length=1000
    )

    async def on_submit(self, interaction):
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
            await interaction.response.send_message(
                "Impossible de créer le ticket. Vérifie la catégorie `tickets` et les permissions du bot.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(f"✅ Candidature envoyée dans {channel.mention}", ephemeral=True)


# ===== COMMANDES =====
@bot.command()
async def test(ctx):
    await ctx.send("✅ Bot LSPD Vespucci OK")


@bot.command()
async def panel(ctx):
    embed = discord.Embed(
        title="🚨 Recrutement LSPD Vespucci",
        description=(
            "⚠️ Ce formulaire sera transmis au staff LSPD Vespucci.\n"
            "Ne donne pas de mot de passe ni d'information sensible.\n\n"
            "Clique sur le bouton pour commencer ta candidature."
        ),
        color=discord.Color.blue()
    )
    embed.add_field(name="District ouvert", value=DISTRICT_NAME, inline=False)
    await ctx.send(embed=embed, view=RecruitmentPanelView())


@bot.command()
async def panel_rdv(ctx):
    embed = discord.Embed(
        title="📅 Prise de rendez-vous",
        description=(
            "Choisis le bouton correspondant à ta demande.\n\n"
            "• Prise de rendez-vous\n"
            "• Proposition de contrat\n"
            "• Police Academy"
        ),
        color=discord.Color.gold()
    )
    await ctx.send(embed=embed, view=RDVPanelView())


@bot.command()
async def manuel(ctx):
    embed = discord.Embed(
        title="Postuler au sein du LSPD Vespucci",
        description="Voici les informations pour postuler au LSPD Vespucci.",
        color=discord.Color.blue()
    )

    embed.add_field(
        name="📝 CONDITIONS HRP :",
        value=(
            "🔹 Avoir au moins 15 ans\n"
            "🔹 L'expérience RP Police n'est pas obligatoire\n"
            "🔹 Être sérieux et original\n"
            "🔹 Ne pas être Blacklist"
        ),
        inline=False
    )

    embed.add_field(
        name="👮 CONDITIONS RP :",
        value=(
            "🔹 Être âgé de 21 ans ou plus\n"
            "🔹 Être un citoyen américain\n"
            "🔹 Être diplômé d'un lycée américain et/ou GED\n"
            "🔹 Disposer d'un casier judiciaire vierge\n"
            "🔹 Disposer d'un permis de conduire valide\n"
            "🔹 Être en bonne condition physique et mentale"
        ),
        inline=False
    )

    view = discord.ui.View()
    view.add_item(
        discord.ui.Button(
            label="📖 Accéder au manuel",
            style=discord.ButtonStyle.link,
            url=MANUAL_URL
        )
    )

    await ctx.send(embed=embed, view=view)


# ===== ACTIONS CANDIDATURE / ENTRETIEN =====
async def candidature_acceptee(ctx, membre):
    role = get_role_by_name(ctx.guild, DISTRICT_NAME)

    if role is None:
        await ctx.send(f"❌ Le rôle **{DISTRICT_NAME}** est introuvable.")
        return

    try:
        await membre.add_roles(role, reason=f"Candidature acceptée par {ctx.author}")
    except discord.Forbidden:
        await ctx.send("❌ Je ne peux pas ajouter le rôle. Mets le rôle du bot au-dessus du rôle Vespucci.")
        return

    embed = build_candidature_accept_embed(str(ctx.author), membre)
    await ctx.send(content=membre.mention, embed=embed)


async def candidature_refusee(ctx, membre, motif):
    embed = build_candidature_refuse_embed(str(ctx.author), membre, motif)
    await ctx.send(content=membre.mention, embed=embed)


async def entretien_valide(ctx, membre):
    role = get_role_by_name(ctx.guild, DISTRICT_NAME)

    if role is None:
        await ctx.send(f"❌ Le rôle **{DISTRICT_NAME}** est introuvable.")
        return

    try:
        await membre.add_roles(role, reason=f"Entretien validé par {ctx.author}")
    except discord.Forbidden:
        await ctx.send("❌ Je ne peux pas ajouter le rôle. Mets le rôle du bot au-dessus du rôle Vespucci.")
        return

    embed = build_entretien_accept_embed(str(ctx.author), membre)
    await ctx.send(content=membre.mention, embed=embed)


async def entretien_refuse_action(ctx, membre, motif):
    embed = build_entretien_refuse_embed(str(ctx.author), membre, motif)
    await ctx.send(content=membre.mention, embed=embed)


# ===== COMMANDES CANDIDATURE =====
@bot.command(name="accepte")
@commands.has_any_role(ROLE_RECRUITER, ROLE_CHIEF, ROLE_UNDER_CHIEF)
async def accepte(ctx, membre: discord.Member):
    await candidature_acceptee(ctx, membre)


@bot.command(name="refuse")
@commands.has_any_role(ROLE_RECRUITER, ROLE_CHIEF, ROLE_UNDER_CHIEF)
async def refuse(ctx, membre: discord.Member, *, motif: str = "Aucun motif précisé"):
    await candidature_refusee(ctx, membre, motif)


# ===== COMMANDES ENTRETIEN =====
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
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(
            "❌ Commande incorrecte.\n\n"
            "`!accepte @pseudo`\n"
            "`!refuse @pseudo motif`\n"
            "`!Entretien_ok @pseudo`\n"
            "`!Entretien_refuser @pseudo motif`"
        )
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
