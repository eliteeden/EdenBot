from discord.ext import commands
import discord
import random

class DiceCog(commands.Cog):
    """A cog for rolling dice."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='roll', aliases=['dice', 'd'])
    async def roll_dice(self, ctx: commands.Context, sides: int = 6):
        """Roll a dice with the specified number of sides (default is 6)."""
        if sides < 2:
            await ctx.send("The number of sides must be at least 2.")
            return
        
        result = random.randint(1, sides)
        await ctx.send(f"You rolled a {result} on a {sides}-sided die.")
    @commands.command(name='d20')
    async def roll_d20(self, ctx: commands.Context):
        """Roll a 20-sided die."""
        result = random.randint(1, 20)
        if result == 20:
            await ctx.send("Critical hit! You rolled a 20!")
        elif result == 1:
            await ctx.send("Critical fail! You rolled a 1!")
        else:
            await ctx.send(f"You rolled a {result}.")
    @commands.command(name='d6')
    async def roll_d6(self, ctx: commands.Context):
        return await self.roll_dice(ctx, 6)
    @commands.command(name='d100')
    async def roll_d100(self, ctx: commands.Context):
        return await self.roll_dice(ctx, 100)

async def setup(bot: commands.Bot):
    """Function to load the DiceCog."""
    await bot.add_cog(DiceCog(bot))
    print("DiceCog has been loaded.")