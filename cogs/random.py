from calendar import c
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
        chance = [0.5, 0.5]
        if "love" in message:
            chance = [0.25, 0.75]
        elif "job" in message:
            chance = [0.6, 0.4]
        elif len(message) > 5:
            chance = [0.5, 0.5]
        elif len(message) > 20:
            chance = [0.4, 0.6]
        elif len(message) > 50:
            chance = [0.7, 0.3]
        agree = random.choice(agree_responses)
        disagree = random.choice(disagree_responses)
        final_response = random.choices([agree, disagree], weights=chance, k=1)[0]
        await ctx.send(final_response)


async def setup(bot: commands.Bot):
    """Function to load the RandomCog."""
    await bot.add_cog(RandomCog(bot))
    print("RandomCog has been loaded.")
