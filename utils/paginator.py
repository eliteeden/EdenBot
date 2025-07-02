import asyncio
import discord
from discord.ext import commands

class Paginator:
    def __init__(self, bot):
        self.bot = bot
        self.pages = []

    def add_page(self, embed):
        self.pages.append(embed)

    async def send(self, ctx):
        current_page = 0
        message = await ctx.send(embed=self.pages[current_page])

        await message.add_reaction("◀️")
        await message.add_reaction("▶️")

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["◀️", "▶️"]

        while True:
            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)

                if str(reaction.emoji) == "▶️" and current_page < len(self.pages) - 1:
                    current_page += 1
                    await message.edit(embed=self.pages[current_page])
                    await message.remove_reaction(reaction, user)

                elif str(reaction.emoji) == "◀️" and current_page > 0:
                    current_page -= 1
                    await message.edit(embed=self.pages[current_page])
                    await message.remove_reaction(reaction, user)

            except asyncio.TimeoutError:
                break
