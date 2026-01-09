import discord
from discord.ext import commands
from discord.ui import Button, View
import json
import os

CONFIG_FILE = "verify_config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

class VerificationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = load_config()

    async def cog_load(self):
        """Automatically reload verification setup when cog is loaded"""
        for guild in self.bot.guilds:
            guild_id = str(guild.id)
            if guild_id not in self.config:
                continue

            channel = guild.get_channel(self.config[guild_id]["channel_id"])
            role = guild.get_role(self.config[guild_id]["role_id"])

            if not channel or not role:
                continue

            # Re-send the verification button
            button = discord.ui.Button(label="Click here to verify!", style=discord.ButtonStyle.green)

            async def button_callback(interaction: discord.Interaction):
                await interaction.response.defer(ephemeral=True)
                try:
                    await interaction.user.add_roles(role)
                    await interaction.followup.send("You are now verified ✅", ephemeral=True)
                except discord.Forbidden:
                    await interaction.followup.send("❌ I don't have permission to give you that role.", ephemeral=True)

            button.callback = button_callback
            view = View()
            view.add_item(button)

            try:
                await channel.send("Click here to verify!", view=view)
                print(f"Verification button reloaded in {guild.name}")
            except Exception as e:
                print(f"Failed to reload verification in {guild.name}: {e}")

    @commands.command(name="verifysetup", aliases=["verifyy"])
    @commands.has_permissions(manage_channels=True)
    async def verifysetup(self, ctx, channel: discord.TextChannel, role: discord.Role):
        """
        Setup verification system.
        Usage: !verifysetup #channel @role
        """

        # Save config for persistence
        self.config[str(ctx.guild.id)] = {
            "channel_id": channel.id,
            "role_id": role.id
        }
        save_config(self.config)

        # Step 1: Lock all channels to only verified role
        for ch in ctx.guild.channels:
            if ch == channel:
                continue

            # Hide from @everyone
            overwrite = ch.overwrites_for(ctx.guild.default_role)
            overwrite.view_channel = False
            await ch.set_permissions(ctx.guild.default_role, overwrite=overwrite)

            # Allow verified role
            overwrite_verified = ch.overwrites_for(role)
            overwrite_verified.view_channel = True
            await ch.set_permissions(role, overwrite=overwrite_verified)

        # Step 2: Create button for verification
        button = discord.ui.Button(label="Click here to verify!", style=discord.ButtonStyle.green)

        async def button_callback(interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            try:
                await interaction.user.add_roles(role)
                await interaction.followup.send("You are now verified ✅", ephemeral=True)
            except discord.Forbidden:
                await interaction.followup.send("❌ I don't have permission to give you that role.", ephemeral=True)

        button.callback = button_callback
        view = View()
        view.add_item(button)

        await channel.send("Click here to verify!", view=view)
        await ctx.send("✅ Verification system setup complete!")

    
    @commands.command(name="oneoff")
    @commands.has_permissions(manage_roles=True)
    async def oneoff(self, ctx, role: discord.Role):
        """
        Assigns the specified role to every member in the server.
        Usage: ;assignrole @RoleName
        """
        # Confirm action
        await ctx.send(f"Starting to assign {role.name} to all members...")

        # Iterate through all members
        success_count = 0
        fail_count = 0
        for member in ctx.guild.members:
            try:
                # Skip bots if you want
                if member.bot:
                    continue
                await member.add_roles(role)
                success_count += 1
            except Exception as e:
                fail_count += 1
                print(f"Failed to assign role to {member}: {e}")

        await ctx.send(
            f"✅ Finished assigning {role.name}.\n"
            f"Success: {success_count}, Failed: {fail_count}"
        )


# --- Cog Setup Function ---
async def setup(bot):
    await bot.add_cog(VerificationCog(bot))
    print("VerificationCog has been loaded successfully")