import discord
from discord.ext import commands
import random


class RandomCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(name="8ball", aliases=["magicball", "pool", "conch"])
    async def ball(self, ctx, *,  message):
        agree_responses = ["Yes", "Absolutely", "I mean there is no point backing out now", "If you want to, I guess", "Go for it", "That is a good idea"]
        disagree_responses = ["No", "Not at all", "Why would you say something like that"]

        weights = [50, 50]
        chance = [0.5, 0.5]
        final_response = random.choices([agree_responses, disagree_responses], weights=chance, k=1)[0]
        await ctx.send(final_response)


async def setup(bot: commands.Bot):
    """Function to load the RandomCog."""
    await bot.add_cog(RandomCog(bot))
    print("RandomCog has been loaded.")
