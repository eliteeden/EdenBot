import discord
from discord.ext import commands
import asyncio

class CarlCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="edenlogs", aliases=["citz", "carly", "cwarns"])
    @commands.has_any_role("Moderator", "Totally Mod")  # Replace with actual role names
    async def cwarn(self, ctx: commands.Context, chosen_role: discord.Role = None):

        # Use provided role or fallback to a default role name
        role_name = "Moderator" if not chosen_role else chosen_role.name
        role = discord.utils.get(ctx.guild.roles, name=role_name)

        if not role:
            await ctx.send("Role not found.")
            return

        if not role.members:
            await ctx.send("No members have that role.")
            return

        members = role.members
        await ctx.send(f"**{role.name} Members ({len(members)} total):**")

        for idx, member in enumerate(members, start=1):
            # Send Carl-bot command to trigger modlog
            await ctx.send(f"!modlog from {member.mention}")
            await asyncio.sleep(6)  # Cooldown: 6 seconds between commands

async def setup(bot):
    await bot.add_cog(CarlCog(bot))
    print("Carl cog has been loaded successfully")