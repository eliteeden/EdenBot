import discord
from discord.ext import commands

class AFKCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.afk_users = {}  # {user_id: reason}

    @commands.command()
    async def afk(self, ctx, *, reason="AFK"):
        """Set your AFK status with an optional reason."""
        self.afk_users[ctx.author.id] = reason
        await ctx.send(f"{ctx.author.mention} is now AFK: {reason}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        ctx = await self.bot.get_context(message)

        # Don't remove AFK if the user is invoking the afk command
        if message.author.id in self.afk_users and ctx.command != self.afk:
            del self.afk_users[message.author.id]
            await message.channel.send(f"Welcome back {message.author.mention}, you're no longer AFK.")

        # Notify if mentioned user is AFK
        for user in message.mentions:
            if user.id in self.afk_users:
                reason = self.afk_users[user.id]
                await message.channel.send(f"{user.mention} is AFK: {reason}")


async def setup(bot):
    await bot.add_cog(AFKCog(bot))
    print("AFKCog has been loaded successfully")