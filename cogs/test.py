import random
import discord
from discord.ext import commands

from constants import ROLES

class TestCog(commands.Cog):
    """A simple test cog to check if the bot is working."""

    def __init__(self, bot):
        self.bot = bot
        self.randomNumber = random.randint(1, 100)

    @commands.command(name='test')
    async def test_command(self, ctx):
        """A simple command to test if the bot is working."""
        await ctx.send(f"Test command executed successfully! Random number is {self.randomNumber}. (This number should change every reload)")
    @commands.command(name='getrolepos')
    @commands.has_any_role(ROLES.TOTALLY_MOD)
    async def get_role_position(self, ctx: commands.Context, role: int): # type: ignore
        """Get the position of a role."""
        role: discord.Role | None = ctx.guild.get_role(role) # type: ignore
        if role is None:
            await ctx.send("Role not found.")
            return
        await ctx.send(f"The position of the role {role.name} is {role.position}.")
    @commands.command(name='setrolepos')
    @commands.has_any_role(ROLES.TOTALLY_MOD)
    async def set_role_position(self, ctx: commands.Context, role: int, position: int): # type: ignore
        """Set the position of a role."""
        role: discord.Role | None = ctx.guild.get_role(role) # type: ignore
        if role is None:
            await ctx.send("Role not found.")
            return
        if position < 0 or position >= len(ctx.guild.roles): # type: ignore
            await ctx.send("Invalid position.")
            return
        try:
            await role.edit(position=position)
            await ctx.send(f"The position of the role {role.name} has been set to {position}.")
        except Exception as e:
            await ctx.send(f"Failed to set role position: {e}")
async def setup(bot: commands.Bot):
    """Function to load the cog."""
    await bot.add_cog(TestCog(bot)) # type: ignore
    print("TestCog has been (re-)loaded.")