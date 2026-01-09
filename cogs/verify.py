import discord
from discord.ext import commands
from discord.ui import Button, View

class VerificationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="verifysetup", aliases=["verifyy"])
    @commands.has_permissions(manage_channels=True)
    async def verifysetup(self, ctx, channel: discord.TextChannel, role: discord.Role):
        """
        Setup verification system.
        Usage: ;verifysetup #channel @role
        """

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
        button = Button(label="Click here to verify!", style=discord.ButtonStyle.green)

        async def button_callback(interaction: discord.Interaction):
            await interaction.user.add_roles(role)
            await interaction.response.send_message("You are now verified ✅", ephemeral=True)

        button.callback = button_callback
        view = View()
        view.add_item(button)

        await channel.send("Click here to verify!", view=view)
        await ctx.send("✅ Verification system setup complete!")

# --- Cog Setup Function ---
async def setup(bot: commands.Bot):
    await bot.add_cog(VerificationCog(bot))
    print("VerficationCog has been loaded successfully")