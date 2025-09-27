from calendar import c
import discord
from discord.ext import commands
import random

class RandomCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Response pools
        self.responses = {
            "love": {
                "agree": [
                    "Love is in the air—yes!", 
                    "Absolutely, romance awaits.", 
                    "Your heart says yes."
                ],
                "disagree": [
                    "Not this time, unfortunately.", 
                    "Love might be on hold.", 
                    "I wouldn’t count on it."
                ],
                "neutral": [
                    "Hard to say about the heart.", 
                    "Could go either way."
                ],
                "weights": (0.25, 0.60, 0.15)
            },
            "job": {
                "agree": [
                    "Your career path is clear—go!", 
                    "Opportunities ahead.", 
                    "Yes, take that risk."
                ],
                "disagree": [
                    "Maybe hold off for now.", 
                    "Not looking great professionally.", 
                    "Consider playing it safe."
                ],
                "neutral": [
                    "I can’t see clearly on that job move.", 
                    "Could go either way."
                ],
                "weights": (0.60, 0.30, 0.10)
            },
            "money": {
                "agree": [
                    "Your wallet will smile—yes!", 
                    "Profits are likely.", 
                    "Investment looks good."
                ],
                "disagree": [
                    "Hold your purse strings tight.", 
                    "Not a good time for spending.", 
                    "I wouldn’t bet on gains."
                ],
                "neutral": [
                    "Financial forecast is cloudy."
                ],
                "weights": (0.40, 0.40, 0.20)
            },
            "health": {
                "agree": [
                    "Your body says yes—take care!", 
                    "A healthy choice.", 
                    "Go for it, safely."
                ],
                "disagree": [
                    "Maybe rest instead.", 
                    "Not ideal for your health right now."
                ],
                "neutral": [
                    "Listen to your body closely."
                ],
                "weights": (0.50, 0.35, 0.15)
            },
            "exam": {
                "agree": [
                    "Study hard—you’ll ace it!", 
                    "Yes, you’re ready."
                ],
                "disagree": [
                    "Not quite—hit the books more."
                ],
                "neutral": [
                    "Half of success is preparation."
                ],
                "weights": (0.55, 0.30, 0.15)
            },
            "generic": {
                "agree": [
                    "Yes", 
                    "Absolutely", 
                    "Go for it", 
                    "That’s a solid idea"
                ],
                "disagree": [
                    "No", 
                    "Not at all", 
                    "I wouldn’t do that"
                ],
                "neutral": [
                    "Maybe later", 
                    "I can’t decide"
                ],
                "weights": (0.45, 0.45, 0.10)
            }
        }

    @commands.command(name="8ball", aliases=["magicball", "pool", "conch"])
    async def ball(self, ctx, *, message: str):
        msg_lower = message.lower()

        # Pick category based on keywords
        for category in ("love", "job", "money", "health", "exam"):
            if category in msg_lower:
                pool = self.responses[category]
                break
        else:
            # length-based slight tweak for generic
            length = len(msg_lower)
            pool = self.responses["generic"]
            if length > 50:
                pool["weights"] = (0.30, 0.50, 0.20)
            elif length > 20:
                pool["weights"] = (0.50, 0.40, 0.10)

        agree, disagree, neutral = pool["agree"], pool["disagree"], pool["neutral"]
        w_agree, w_disagree, w_neutral = pool["weights"]

        # Choose response
        response = random.choices(
            population=[random.choice(agree),
                        random.choice(disagree),
                        random.choice(neutral)],
            weights=[w_agree, w_disagree, w_neutral],
            k=1
        )[0]

        await ctx.send(response)

async def setup(bot: commands.Bot):
    """Load the RandomCog cog."""
    await bot.add_cog(RandomCog(bot))
    print("RandomCog has been loaded successfully.")
