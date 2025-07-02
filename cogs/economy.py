import datetime
from discord.ext import commands
import discord
import json
import random

class EconomyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bank = self.__load_bank()
    def __load_bank(self):
        try:
            with open("users.json", "r") as s:
                return json.load(s)
        except (FileNotFoundError, json.JSONDecodeError, ValueError):
            return {'users': []}
    def __save_bank(self):
        with open("users.json", "w") as s:
            json.dump(self.bank, s, indent=4)

    @commands.command(name='work', aliases=['w'])
    @commands.cooldown(1,30, commands.BucketType.user)
    async def work(self, ctx: commands.Context):
        found = False
        responses = ['You did a great job and earned', 'You exploited a citizen and earned', 'You forfeited your evening to the mods and earned', 'You stole', 'You were such a cutie you got', 'You begged and got', 'You sent your nudes to the mods and were paid', 'You went to the mines and found', 'You posted on Patreon and got', 'You were so well-behaved you were given', 'You sold your kidney and got', 'You helped an old lady on the street and got', 'Your small business made you', 'Just take these']
        for current_acc in self.bank['users']:
            if ctx.author.name == current_acc['name']:
                found = True
                coins = int(current_acc['balance'])
                earn = random.randint(1,3001)
                newcoins = coins + earn
                current_acc['balance'] = newcoins
                if earn == 1984:
                    await ctx.send("Your speaking priviledges have been revoked")
                    newtime = newtime = datetime.timedelta(minutes=int("5"))
                    await ctx.author.edit(timed_out_until=discord.utils.utcnow() + newtime) # type: ignore
                else:    
                    await ctx.send(f"{random.choice(responses)} {earn} eden coins")
                break
        if not found:
            earn = random.randint(1,3000)
            self.bank['users'].append({
                'name': ctx.author.name,
                'balance': earn
                })
            await ctx.send(f"{random.choice(responses)} {earn} eden coins")

        with open("users.json", "w") as s:
            json.dump(self.bank, s, indent=4)

    @work.error
    async def work_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send("Please make an account with `;bal` first.")


async def setup(bot: commands.Bot):
    """Function to load the cog."""
    await bot.add_cog(EconomyCog(bot))
    print("EconomyCog has been (re-)loaded.")