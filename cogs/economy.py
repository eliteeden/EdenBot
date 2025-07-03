import datetime
from discord.ext import commands
import discord
from discord import Member
import json
import random
from typing import Optional
from ..constants import CHANNELS
from ..utils.paginator import Paginator

class EconomyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bank = self.__load_bank() # Load the bank every reload
    def __load_bank(self):
        try:
            with open("users.json", "r") as s:
                print("Reloading bank from users.json!")
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
        responses = [
            'You did a great job and earned', 
            'You exploited a citizen and earned', 
            'You forfeited your evening to the mods and earned', 
            'You stole', 
            'You were such a cutie you got', 
            'You begged and got', 
            'You sent your nudes to the mods and were paid', 
            'You went to the mines and found', 
            'You posted on Patreon and got', 
            'You were so well-behaved you were given', 
            'You sold your kidney and got', 
            'You helped an old lady on the street and got', 
            'Your small business made you', 
            'Just take these',
            'You cleaned the streets and got',
            'You bought a lottery ticket and won',
            'You "found"',
        ]
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

        self.__save_bank()

    @work.error
    async def work_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send("Please make an account with `;bal` first.")
    # Economy commands
    @commands.command()
    async def bal(self, ctx: commands.Context, user: Optional[Member] = None): # type: ignore
        if user is None:
            user: Member = ctx.author # type: ignore
            pronoun = "Your"
        else:
            pronoun = f"{user.mention}'s"
        found = False
        for current_acc in self.bank['users']:
            if user.name == current_acc['name']:
                found = True
                await ctx.send(f"{pronoun} balance is {current_acc['balance']} eden coins")
                break
        if not found:
            self.bank['users'].append({
                'name': user.name,
                'balance': 0
            })
            await ctx.send(f"{pronoun} balance is 0 eden coins")
            self.__save_bank()

    @commands.command(name="topbal")
    async def topbal(self, ctx: commands.Context):
        """Displays the top 10 users with the highest balance"""
        try:
            if 'users' not in self.bank:
                await ctx.send("No users found in the economy system. Is the .json file empty?")
                return

            # Sort users by balance (highest first)
            sorted_users = sorted(self.bank['users'], key=lambda x: x['balance'], reverse=True)

            # Limit to top 10
            top_users = sorted_users[:100]


            paginator = Paginator(bot=self.bot)  # Initialize paginator

            # Create paginated embeds
            for i in range(0, len(top_users), 10):  # Show 10 users per page
                embed = discord.Embed(title="Economy Leaderboard", color=discord.Color.gold())
                for idx, (user) in enumerate(top_users[i:i+10], start=i+1):
                    embed.add_field(name=f"{idx}. {user['name']}", value=f"{user['balance']} eden coins", inline=False)

                paginator.add_page(embed)

            await paginator.send(ctx)  # Send paginated leaderboard

        except Exception as e:
            await ctx.send(e) # type: ignore

    @commands.command(name='coinflip', aliases=['cf'])
    async def coinflip(self, ctx: commands.Context, *, txt: str):
        found = False
        sides = ['heads', 'tails']
        toss = random.choice(sides)

        if txt.lower() in sides:
            if txt.lower() == toss:
                earn = 1000
                for current_acc in self.bank['users']:
                    if ctx.author.name == current_acc['name']:
                            found = True
                            coins = int(current_acc['balance'])
                            newcoins = coins + earn
                            current_acc['balance'] = newcoins
                            await ctx.send(f"You won {earn} eden coins")
                            break

                if not found:
                    self.bank['users'].append({
                            'name': ctx.author.name,
                            'balance': earn
                            })
                    await ctx.send(f"You won {earn} eden coins")

            else:
                    await ctx.send('You lost')
        else:
            await ctx.send('Pick either ``heads`` or ``tails``')

        self.__save_bank()


    @commands.command(name='subbal')
    @commands.has_any_role('MODERATOR', 'happy')
    @commands.cooldown(1,500, commands.BucketType.user)
    async def subbal(self, ctx: commands.Context, member: Member):
        userid = member.name
        found = False
        for current_acc in self.bank['users']:
            if userid == current_acc['name']:
                found = True
                current_acc['balance'] = 0

                await ctx.send(f"{member.mention} 's balance is {current_acc['balance']} eden coins")
                break
        if not found:
              self.bank['users'].append({
                  'name': userid,
                  'balance': 0
              })
              await ctx.send(f"{member.mention} 's balance is 0 eden coins")

        self.__save_bank()


    @commands.command(name='setbal')
    @commands.has_any_role('Bonked by Zi')
    async def setbal(self, ctx: commands.Context, member: Member, coins: int):
        userid = member.name
        found = False
        for current_acc in self.bank['users']:
            if userid == current_acc['name']:
                found = True
                current_acc['balance'] = coins

                await ctx.send(f"{member.mention} 's balance is {current_acc['balance']} eden coins")
                break
        if not found:
              self.bank['users'].append({
                  'name': userid,
                  'balance': coins
              })
              await ctx.send(f"{member.mention} 's balance is {coins} eden coins")

        self.__save_bank()

    @setbal.error
    async def setbal_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingAnyRole):
            await ctx.send('You do not have permission to use this command.')

    @commands.command(name='win')
    async def win(self, ctx: commands.Context):
        userid = ctx.author.name
        found = False
        for current_acc in self.bank['users']:
            if userid == current_acc['name']:
                found = True
                coins = int(current_acc['balance'])
                if coins < 100000:
                    await ctx.send('You do not have enough coins, you need 100,000')
                    break
                else:
                    newcoins = coins - 100000
                    current_acc['balance'] = newcoins
                    channel: discord.TextChannel = self.bot.get_channel(CHANNELS.WINNERS) # type: ignore
                    await channel.send(f'{ctx.author.mention} won the prize')
                    break
        if not found:
            self.bank['users'].append({
                    'name': ctx.author.name,
                    'balance': 0
                    })
            await ctx.send("You do not have an account")

        self.__save_bank()




    @commands.command(name='roulette')
    @commands.cooldown(1,300, commands.BucketType.user)
    async def roulette(self, ctx: commands.Context, bullets: int):
        if bullets < 1 or bullets > 5:
            self.roulette.reset_cooldown(ctx) # type: ignore
            await ctx.send('Please choose between 1 and 5 bullets')
            return

        userid = ctx.author.name
        found = False
        chamber = [1] * bullets + [0] * (6 - bullets)
        random.shuffle(chamber)
        print(f'shuffled chambers: {chamber}') # Debug feature

        fired_chamber = random.choice(chamber)

        if fired_chamber == 0:
            earn = 1000 * bullets
            for current_acc in self.bank['users']:
                found = True
                if userid == current_acc['name']:
                    self.roulette.reset_cooldown(ctx) # type: ignore #Cooldown is reset
                    coins = int(current_acc['balance'])
                    newcoins = coins + earn
                    current_acc['balance'] = newcoins
                    await ctx.send(f'You won {earn} eden coins')
                    break
            if not found:
                self.roulette.reset_cooldown(ctx) # type: ignore #Cooldown is reset
                self.bank['users'].append({
                    'name': ctx.author.name,
                    'balance': earn
                })
                await ctx.send(f'You won {earn} eden coins')

            self.__save_bank()


        else:
            await ctx.send(f'You died! Try again in 5 minutes')

    @roulette.error
    async def roulette_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send('Only numbers please!')

    @commands.command(name='gamble')
    @commands.cooldown(1,5, commands.BucketType.user)
    async def gamble(self, ctx: commands.Context):
        userid = ctx.author.name
        found = False
        nega_earn = 6500
        bot_choice = random.randint(1, 35)
        if bot_choice == 5:
            for current_acc in self.bank['users']:
                found = True
                if userid == current_acc['name']:
                    coins = int(current_acc['balance'])
                    if coins >= nega_earn:
                        earn = 1000000
                        newcoins = coins + earn
                        current_acc['balance'] = newcoins
                        await ctx.send(f'You won {earn} eden coins')
                        break
                    else:
                        await ctx.send(f'You do not have enough coins, you need {nega_earn} to participate')
            if not found:
                self.bank['users'].append({
                    'name': ctx.author.name,
                    'balance': 0
                    })
                await ctx.send('You do not have an account')
            
            self.__save_bank()
        else:
            for current_acc in self.bank['users']:
                if userid == current_acc['name']:
                    found = True
                    coins = int(current_acc['balance'])
                    if coins >= nega_earn:
                        newcoins = coins - nega_earn
                        current_acc['balance'] = newcoins
                        await ctx.send(f'You lost {nega_earn} eden coins')
                        break
                    else:
                        await ctx.send(f'You do not have enough coins, you need {nega_earn} to participate')
            if not found:
                self.bank['users'].append({
                    'name': ctx.author.name,
                    'balance': 0
                })
                await ctx.send(f'You do not have an account')

            self.__save_bank()

async def setup(bot: commands.Bot):
    """Function to load the cog."""
    await bot.add_cog(EconomyCog(bot))
    print("EconomyCog has been (re-)loaded.")