import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import io

TICKET_DATA_FILE = "tickets.json"

def load_tickets():
    if not os.path.exists(TICKET_DATA_FILE):
        with open(TICKET_DATA_FILE, "w") as f:
            json.dump({"last_ticket": 0, "tickets": {}}, f)
    with open(TICKET_DATA_FILE, "r") as f:
        return json.load(f)

def save_tickets(data):
    with open(TICKET_DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

class TicketView(discord.ui.View):
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Create Ticket", style=discord.ButtonStyle.green, custom_id="create_ticket")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = load_tickets()
        data["last_ticket"] += 1
        ticket_id = data["last_ticket"]

        guild = interaction.guild
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        category = interaction.channel.category
        channel = await guild.create_text_channel(
            name=f"ticket-{ticket_id}",
            overwrites=overwrites,
            category=category
        )

        data["tickets"][str(channel.id)] = {
            "user_id": interaction.user.id,
            "open": True
        }
        save_tickets(data)

        await interaction.response.send_message(f"🎫 Ticket created: {channel.mention}", ephemeral=True)
        await channel.send(f"{interaction.user.mention}, thank you for opening a ticket. A staff member will be with you shortly.")

class TicketCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="setup", description="Setup ticket system in this channel")
    async def setup(self, interaction: discord.Interaction):
        view = TicketView(self.bot)
        await interaction.channel.send("🎟️ Click the button below to create a ticket:", view=view)
        await interaction.response.send_message("✅ Ticket system setup complete.", ephemeral=True)

    @app_commands.command(name="add", description="Add a user to the ticket")
    async def add(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.channel.set_permissions(member, read_messages=True, send_messages=True)
        await interaction.response.send_message(f"✅ {member.mention} has been added to the ticket.")

    @app_commands.command(name="remove", description="Remove a user from the ticket")
    async def remove(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.channel.set_permissions(member, overwrite=None)
        await interaction.response.send_message(f"✅ {member.mention} has been removed from the ticket.")

    @app_commands.command(name="close", description="Close the ticket")
    async def close(self, interaction: discord.Interaction):
        data = load_tickets()
        ticket = data["tickets"].get(str(interaction.channel.id))
        if ticket:
            ticket["open"] = False
            save_tickets(data)
            await interaction.channel.set_permissions(interaction.guild.default_role, read_messages=False)
            await interaction.response.send_message("🔒 Ticket closed.")
        else:
            await interaction.response.send_message("❌ This is not a valid ticket channel.", ephemeral=True)

    @app_commands.command(name="open", description="Reopen the ticket")
    async def open(self, interaction: discord.Interaction):
        data = load_tickets()
        ticket = data["tickets"].get(str(interaction.channel.id))
        if ticket:
            ticket["open"] = True
            save_tickets(data)
            user = interaction.guild.get_member(ticket["user_id"])
            if user:
                await interaction.channel.set_permissions(user, read_messages=True, send_messages=True)
            await interaction.response.send_message("🔓 Ticket reopened.")
        else:
            await interaction.response.send_message("❌ This is not a valid ticket channel.", ephemeral=True)

    @app_commands.command(name="transcript", description="Generate a transcript of the ticket")
    async def transcript(self, interaction: discord.Interaction):
        messages = []
        async for msg in interaction.channel.history(limit=None, oldest_first=True):
            messages.append(f"{msg.created_at} - {msg.author}: {msg.content}")
        transcript_text = "\n".join(messages)
        transcript_file = discord.File(io.StringIO(transcript_text), filename="transcript.txt")
        await interaction.response.send_message("📄 Transcript generated:", file=transcript_file)

async def setup(bot: commands.Bot):
    await bot.add_cog(TicketCog(bot))