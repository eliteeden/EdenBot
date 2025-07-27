import discord
from discord.ext import commands

class Counting(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.channel_id = None      # Set this manually or through a command
        self.current_count = 0
        self.last_user_id = None    # To avoid double counting
        self.breaker = None

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.channel.id != self.channel_id:
            return

        try:
            number = int(message.content.strip())
        except ValueError:
            if ";setcount" in message.content:
                return # ignore 
            else:
                await message.channel.send(
                    f"{message.author.mention} broke the chain by sending an invalid message!"
                )
                self.current_count = 0
                return


        # Same user posting twice
        if message.author.id == self.last_user_id:
            self.breaker = message.author
            await message.channel.send(
                f"{message.author.mention} broke the chain by counting twice!"
            )
            self.current_count = 0
            return

        # Wrong number
        if number != self.current_count + 1:
            self.breaker = message.author
            await message.channel.send(
                f"{message.author.mention} broke the chain at {self.current_count}. Expected {self.current_count + 1}."
            )
            self.current_count = 0
            return

        # Valid count
        self.current_count = number
        self.last_user_id = message.author.id
    @commands.command(name="setcount")
    async def setcount(self, ctx, start: int):
        """Set the starting number and restrict to this channel."""
        self.current_count = start
        self.last_user_id = None
        self.breaker = None
        self.channel_id = ctx.channel.id
        await ctx.send(f"Counting is now restricted to **{ctx.channel.mention}**. Starting from **{start}**!")

    @commands.command(name="broken")
    async def broken(self, ctx):
        """Reveal who last broke the chain."""
        if self.breaker:
            await ctx.send(f"The last breaker was {self.breaker.mention}.")
        else:
            await ctx.send("No one has broken the chain yet!")

async def setup(bot: commands.Bot):
    await bot.add_cog(Counting(bot))
    print("CountingCog has been loaded")