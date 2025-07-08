import random
from discord.ext import commands

class TestCog(commands.Cog):
    """A simple test cog to check if the bot is working."""

    def __init__(self, bot):
        self.bot = bot
        self.randomNumber = random.randint(1, 100)

    @commands.command(name='test')
    async def test_command(self, ctx):
        """A simple command to test if the bot is working."""
        await ctx.send(f"Test command executed successfully! Random number is {self.randomNumber}. (This number should change every reload)")

async def setup(bot: commands.Bot):
    """Function to load the cog."""
    await bot.add_cog(TestCog(bot)) # type: ignore
    print("TestCog has been (re-)loaded.")