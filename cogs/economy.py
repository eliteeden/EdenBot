import datetime
import math
from discord.ext import commands, tasks
import discord
from discord import Member
import json
import os
import random
from typing import Literal, Optional
from ..constants import CHANNELS

from typing import TypedDict

class BankEntry(TypedDict):
    name: str
    balance: int

class EconomyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bank: dict[Literal["users"], list[BankEntry]] = self.__load_bank() # type: ignore # Load the bank every reload
        # TODO: not destroy my micro sd card with this
        self.jackpot_file = open("jackpot.json", "w") # Open file descriptor 3 for writing
        with open("jackpot.json", "r") as f:
            try:
                self.jackpot = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError, ValueError):
                self.jackpot = {'jackpot': 0}
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
    def set(self, user: str, coins: int):
        """Sets the balance of a user."""
        found = False
        for current_acc in self.bank['users']:
            if user == current_acc['name']:
                found = True
                current_acc['balance'] = coins
                break
        if not found:
            self.bank['users'].append({
                'name': user,
                'balance': coins
            })
        self.__save_bank()
    def get(self, user: str) -> int:
        """Gets the balance of a user."""
        for current_acc in self.bank['users']:
            if user == current_acc['name']:
                return int(current_acc['balance'])
        else:
            self.set(user, 0)  # Create an account with 0 balance if not found
            return 0

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
                coins = int(current_acc['balance'])
                earn = random.randint(1,3001)
                newcoins = coins + earn
                self.set(ctx.author.name, newcoins)
                if earn == 1984:
                    await ctx.send("Your speaking priviledges have been revoked")
                    newtime = newtime = datetime.timedelta(minutes=int("5"))
                    await ctx.author.edit(timed_out_until=discord.utils.utcnow() + newtime) # type: ignore
                else:    
                    await ctx.send(f"{random.choice(responses)} {earn} eden coins")
                break
        if not found:
            earn = random.randint(1,3000)
            self.set(ctx.author.name, earn)
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
        for current_acc in self.bank['users']:
            if user.name == current_acc['name']:
                await ctx.send(f"{pronoun} balance is {current_acc['balance']} eden coins")
                break
        else:
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


            paginator = self.bot.cogs["PaginatorCog"].paginator()  # type: ignore

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
    @commands.cooldown(1, 5, commands.BucketType.user)
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
                            self.set(ctx.author.name, newcoins)
                            await ctx.send(f"You won {earn} eden coins")
                            break

                if not found:
                    self.set(ctx.author.name, earn)
                    await ctx.send(f"You won {earn} eden coins")

            else:
                    await ctx.send('You lost')
        else:
            await ctx.send('Pick either ``heads`` or ``tails``')



    @commands.command(name='subbal')
    @commands.has_any_role('MODERATOR', 'happy')
    @commands.cooldown(1,500, commands.BucketType.user)
    async def subbal(self, ctx: commands.Context, member: Member):
        userid = member.name
        found = False
        for current_acc in self.bank['users']:
            if userid == current_acc['name']:
                found = True
                self.set(userid, 0)  # Set balance to 0

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
        self.set(userid, coins)  # Set balance to specified coins
        await ctx.send(f"{member.mention} 's balance is {coins} eden coins")

    @setbal.error
    async def setbal_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingAnyRole):
            await ctx.send('You do not have permission to use this command.')

    @commands.command(name='win')
    async def win(self, ctx: commands.Context):
        userid = ctx.author.name
        price = 100_000
        for current_acc in self.bank['users']:
            if userid == current_acc['name']:
                coins = int(current_acc['balance'])
                if coins < price:
                    await ctx.send(f'You do not have enough coins, you need {price:,}')
                    break
                else:
                    newcoins = coins - price
                    current_acc['balance'] = newcoins
                    channel: discord.TextChannel = self.bot.get_channel(CHANNELS.WINNERS) # type: ignore
                    await channel.send(f'{ctx.author.mention} won the prize')
                    break
        else:
            self.set(userid, 0)
            await ctx.send("You do not have an account")





    @commands.command(name='roulette')
    @commands.cooldown(1,300, commands.BucketType.user)
    async def roulette(self, ctx: commands.Context, bullets: int):
        if bullets < 1 or bullets > 5:
            self.roulette.reset_cooldown(ctx) # type: ignore
            await ctx.send('Please choose between 1 and 5 bullets')
            return

        userid = ctx.author.name
        chamber = [1] * bullets + [0] * (6 - bullets)
        random.shuffle(chamber)
        print(f'shuffled chambers: {chamber}') # Debug feature

        fired_chamber = random.choice(chamber)

        if fired_chamber == 0:
            earn = 1000 * bullets
            for current_acc in self.bank['users']:
                if userid == current_acc['name']:
                    self.roulette.reset_cooldown(ctx) # type: ignore #Cooldown is reset
                    coins = int(current_acc['balance'])
                    newcoins = coins + earn
                    self.set(userid, newcoins)
                    await ctx.send(f'You won {earn} eden coins')
                    break
            else:
                self.roulette.reset_cooldown(ctx) # type: ignore #Cooldown is reset
                self.set(userid, earn)
                await ctx.send(f'You won {earn} eden coins')
        else:
            await ctx.send(f'You died! Try again in 5 minutes')

    @roulette.error
    async def roulette_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send('Only numbers please!')
            self.roulette.reset_cooldown(ctx) # type: ignore

    @commands.command(name='slots', aliases=['slot', 'oldgamble'])
    @commands.cooldown(1,5, commands.BucketType.user)
    async def slots(self, ctx: commands.Context):
        userid = ctx.author.name
        nega_earn = 6500
        bot_choice = random.randint(1, 35)
        if bot_choice == 5:
            for current_acc in self.bank['users']:
                if userid == current_acc['name']:
                    coins = int(current_acc['balance'])
                    if coins >= nega_earn:
                        earn = 1_000_000
                        newcoins = coins + earn
                        self.set(userid, newcoins)
                        await ctx.send(f'You won {earn:,} eden coins')
                        bot_updates_channel: discord.TextChannel = self.bot.get_channel(CHANNELS.BOT_LOGS)  # type: ignore
                        await bot_updates_channel.send(f"User {ctx.author.mention} won {earn:,} coins in slots!")
                        break
                    else:
                        await ctx.send(f'You do not have enough coins, you need {nega_earn:,} to participate')
            else:
                self.set(userid, 0)
                await ctx.send('You do not have an account')
            
            self.__save_bank()
        else:
            for current_acc in self.bank['users']:
                if userid == current_acc['name']:
                    coins = int(current_acc['balance'])
                    if coins >= nega_earn:
                        newcoins = coins - nega_earn
                        self.set(userid, newcoins)
                        await ctx.send(f'You lost {nega_earn:,} eden coins')
                        break
                    else:
                        await ctx.send(f'You do not have enough coins, you need {nega_earn:,} to participate')
            else:
                self.set(userid, 0)
                await ctx.send(f'You do not have an account')

    @commands.command(name='give')
    async def give(self, ctx: commands.Context, member: Member, coins: int):
        """Gives a specified amount of coins to another user."""
        if coins <= 0:
            await ctx.send("You must give a positive amount of coins.")
            return

        if member.bot:
            if member.id == self.bot.user.id: # type: ignore
                await ctx.send("Why are you giving me these coins? I don't need them!")
            else: 
                await ctx.send("You cannot give coins to bots.")
            return
        if member == ctx.author:
            await ctx.send("No, I won't let you commit tax fraud.") # TODO: change?
            return

        for current_acc in self.bank['users']:
            if ctx.author.name == current_acc['name']:
                if current_acc['balance'] < coins:
                    await ctx.send(random.choice([
                        f"{ctx.author.mention} is so broke they can't even afford to give {coins:,} coins.",
                        f"{ctx.author.mention} tried to help the poor but didn't realize they were the poor",
                        f"{coins:,} coins? {ctx.author.mention}, you need to work harder!",
                        f"{member.mention} won't be receiving any coins from {ctx.author.mention} today.",
                    ]))
                    return
                self.set(ctx.author.name, current_acc['balance'] - coins)
                break
        else:
            await ctx.send("You do not have an account. Use `;bal` to create one.")
            return
        for current_acc in self.bank['users']:
            if member.name == current_acc['name']:
                self.set(member.name, current_acc['balance'] + coins)
                break
        else:
            self.set(member.name, coins)
        await ctx.send(random.choice([
            f"{member.mention} gave {coins} eden coins.",
            f"{member.mention} generously donated {coins} eden coins.",
            f"{member.mention} is feeling generous and gave away {coins} eden coins.",
        ]))

    @commands.command(name='gamble', aliases=['newgamble'])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def gamble(self, ctx: commands.Context):
        """Let's go gambling!"""
        cost = 6_500
        userid = ctx.author.name
        balance = self.get(userid)
        if balance < cost:
            await ctx.send(random.choice([
                f"{ctx.author.mention} is so broke they can't even afford to gamble {cost:,} coins.",
                f"{ctx.author.mention} tried to gamble but didn't have enough coins.",
                f"{balance:,} coins? {ctx.author.mention}, you need to work harder!",
                f"I'm afraid {balance:,} coins isn't quite {cost:,} just yet",
                f"{ctx.author.mention} you need coins to blow if you wanna gamble.",
                f"{ctx.author.mention}, come back after earning {cost-balance:,} more coins.",
                f"You're still {cost-balance:,} coins short, buddy.",
                f"Only {balance:,} coins? Skill issue.",
            ]))
            return
        # https://www.desmos.com/calculator/o3meaagvzc
        chance = math.floor(math.log(self.jackpot['jackpot'], 10) * 50)
        # TODO: chance logic
        if random.randint(1, chance) <= 235: # replace with actual chance logic
            # User wins
            win_amount = max(10_000_000, self.jackpot['jackpot'] * 2)  # Maximum win amount is 10 million
            self.set(userid, balance + win_amount)
            self.jackpot['jackpot'] = min(100_000, self.jackpot['jackpot'] - win_amount)  # Reset jackpot after win
            await self.save_jackpot_task()
            await ctx.send(random.choice([
                f"{ctx.author.mention} won {win_amount:,} coins! The jackpot is now {self.jackpot['jackpot']:,} coins.",
                f"Congratulations {ctx.author.mention}! You hit the jackpot and won {win_amount:,} coins!",
                f"{ctx.author.mention} just won big! {win_amount:,} coins added to your balance.",
            ]))
            bot_updates_channel: discord.TextChannel = self.bot.get_channel(CHANNELS.BOT_LOGS)  # type: ignore
            await bot_updates_channel.send(f"User {ctx.author.mention} won {win_amount:,} coins in the jackpot!")
        else:
            # User loses
            self.set(userid, balance - cost)
            self.jackpot['jackpot'] += 6_000  # Increase jackpot by 6,000 coins
            await self.save_jackpot_task()
            await ctx.send(random.choice([
                "Aw dang it.",
                "maybe next time?",
                "99% of gamblers quit before they hit big",
                "'Let's go gambling' you said, 'I would win big' you said",
                "You might as well quit and save what's left of your balance",
                "You're addicted to this, aren't you?",
                "You are so lucky eden coins aren't real money",
                "~~Just one more~~ Just one more",
                "Don't quit your day job.",
                "Not my tempo. Do it again.",
                "Stopping so soon? Lame-o. Keep gambling!",
                "You almost made me feel pity and give it to you. Almost."
            ]))
    
    # Jackpot tasks
    @tasks.loop(minutes=1)
    async def jackpot_task(self):
        """A task that runs every minute to check if the jackpot should be increased."""
        if self.jackpot['jackpot'] < 10_000_000:
            self.jackpot['jackpot'] += 3600
            # print(f"Jackpot increased to {self.jackpot['jackpot']} coins")
    @tasks.loop(hours=1)
    async def save_jackpot_task(self):
        """A task that runs every hour to save the jackpot data."""
        self.jackpot_file.buffer.write(json.dumps(self.jackpot).encode('utf-8'))
        self.jackpot_file.buffer.flush()
        self.jackpot_file.seek(0)
        self.jackpot_file.flush()
        print("Jackpot data saved.")

    async def cog_unload(self):
        """Fires when the cog is unloaded."""
        self.__save_bank()
        # Save jackpot data
        self.jackpot_file.buffer.write(json.dumps(self.jackpot).encode('utf-8'))
        self.jackpot_file.buffer.flush()
        self.jackpot_file.seek(0)
        self.jackpot_file.flush()
        self.jackpot_file.close()
        return await super().cog_unload()

async def setup(bot: commands.Bot):
    """Function to load the cog."""
    await bot.add_cog(EconomyCog(bot))
    print("EconomyCog has been (re-)loaded.")