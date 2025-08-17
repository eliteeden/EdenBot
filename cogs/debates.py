import discord
from discord.ext import commands
import asyncio

from constants import ROLES


class DebatesCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot

    @commands.command()
    @commands.has_any_role("Event Host", ROLES.MODERATOR)
    @commands.has_permissions(manage_channels=True)
    async def hush(
        self,
        ctx: commands.Context,
        member: discord.Member,
        channel: discord.TextChannel = None,
    ) -> None:

        if channel is None:
            channel = self.bot.get_channel(1165716783207039117)
        """Temporarily mute a member in a specific channel for 1 hour."""
        overwrite: discord.PermissionOverwrite = channel.overwrites_for(member)
        overwrite.send_messages = False
        await channel.set_permissions(member, overwrite=overwrite)
        await ctx.send(
            f"{member.mention} has been muted in {channel.mention} for 1 hour."
        )

        await asyncio.sleep(3600)  # ⏱️ 1 hour in seconds

        overwrite.send_messages = None  # Reset to default permission
        await channel.set_permissions(member, overwrite=overwrite)
        await ctx.send(f"{member.mention} can now talk in {channel.mention} again.")

    @commands.command()
    @commands.has_any_role("Event Host", ROLES.MODERATOR)
    @commands.has_permissions(manage_channels=True)
    async def unhush(
        self,
        ctx: commands.Context,
        member: discord.Member,
        channel: discord.TextChannel = None,
    ) -> None:
        """Unmute a member in a specific channel before the timer ends."""
        if channel is None:
            channel = self.bot.get_channel(1165716783207039117)
        overwrite: discord.PermissionOverwrite = channel.overwrites_for(member)
        overwrite.send_messages = None  # Reset to default permission
        await channel.set_permissions(member, overwrite=overwrite)
        await ctx.send(f"{member.mention} can now talk in {channel.mention} again.")

    @commands.command()
    @commands.has_any_role("Event Host", ROLES.MODERATOR)
    @commands.has_permissions(manage_channels=True)
    async def topic(self, ctx: commands.Context, *, topic: str) -> None:
        """Announce a new debate topic."""
        await ctx.send(f"🗣️ **New Debate Topic:** {topic}")

    @commands.command()
    @commands.has_any_role("Event Host", ROLES.MODERATOR)
    @commands.has_permissions(manage_channels=True)
    async def enddebate(self, ctx: commands.Context) -> None:
        """Announce the end of a debate."""
        await ctx.send("🔔 The debate has ended! Thank you for participating.")


async def setup(bot: commands.Bot) -> None:
    """Function to load the DebatesCog."""
    await bot.add_cog(DebatesCog(bot))
    print("DebatesCog has been loaded.")
