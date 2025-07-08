import datetime
import math
from discord.ext import commands, tasks
import discord
from discord import Member
import json
import random
from typing import Optional, overload
from constants import CHANNELS

class EconomyCog(commands.Cog):
    """All economy related commands and tasks."""
    ECONOMY_FILE = "bank.json"
    JACKPOT_FILE = "jackpot.json"
    type strint = str # Contains an ID, not a string
    type MemberLike = discord.User | discord.Member | str | int | strint
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bank: dict[strint, int] = self.__load_bank() # type: ignore # New bank maps ID directly to balance
        # self.bank: dict[Literal["users"], list[BankEntry]] = self.__load_bank() # type: ignore # Load the bank every reload
        # TODO: not destroy my micro sd card with this
        self.jackpot_file = open(self.JACKPOT_FILE, "w") # Open file descriptor 3 for writing
        with open(self.JACKPOT_FILE, "r") as f:
            try:
                self.jackpot = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError, ValueError):
                self.jackpot = {'jackpot': 0}
    def __get_id(self, member: MemberLike) -> strint:
        if isinstance(member, (discord.User, discord.Member)):
            return str(member.id)
        elif isinstance(member, int):
            return str(member)
        elif isinstance(member, str):
            member = member.lower()
            if member.startswith("<@") and member.endswith(">"):
                return member[2:-1]
            elif member[0] in [str(i) for i in range(10)]:
                return member
            else:
                for m in self.bot.get_all_members():
                    if member == m.name.lower() or member == m.display_name.lower():
                        return str(m.id)
        raise ValueError("Invalid member type")

    def __load_bank(self):
        try:
            with open(self.ECONOMY_FILE, "r") as s:
                print(f"Reloading bank from {self.ECONOMY_FILE}!")
                return json.load(s)
        except (FileNotFoundError, json.JSONDecodeError, ValueError):
            return {'users': []}
    def __save_bank(self):
        with open(self.ECONOMY_FILE, "w") as s:
            json.dump(self.bank, s, indent=4)
    def add(self, user: MemberLike, coins: int):
        """Adds coins to a user's balance."""
        user_id = self.__get_id(user)
        self.set(user_id, self.get(user_id) + coins)
    def sub(self, user: MemberLike, coins: int):
        return self.add(user, -coins)
    def set(self, user: MemberLike, coins: int):
        """Sets the balance of a user."""
        self.bank[self.__get_id(user)] = coins
        self.__save_bank()
    def get(self, user: MemberLike) -> int:
        """Gets the balance of a user."""
        user_id = self.__get_id(user)
        if user_id in self.bank:
            return self.bank[user_id]
        else:
            self.bank[user_id] = 0
            self.__save_bank()
            return 0

    @commands.command(name='work', aliases=['w'])
    @commands.cooldown(1,45, commands.BucketType.user)
    async def work(self, ctx: commands.Context):
        found = False
        responses = [
            'You did a great job and earned', 
            'You exploited a citizen and earned', 
            'You forfeited your evening to the mods and earned', 
            # 'You stole', 
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
        # TODO: fix
        self.add(ctx.author, coins:=(random.randint(1, 5000)))
        await ctx.send(f"{random.choice(responses)} {coins} eden coins")

        self.__save_bank()

    @work.error
    async def work_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send("Please make an account with `;bal` first.")
    # Economy commands
    @commands.command(name='bal')
    async def bal(self, ctx: commands.Context, user: Optional[Member] = None): # type: ignore
        await ctx.send(f"{user.mention + '\'s' if user else 'Your'} balance is {self.get(user or ctx.author)} eden coins.")
        

    @commands.command(name="topbal", aliases=["bals"])
    async def topbal(self, ctx: commands.Context):
        """Displays the top 10 users with the highest balance"""
        try:
            if 'users' not in self.bank:
                await ctx.send("No users found in the economy system. Is the .json file empty?")
                return

            # Sort users by balance (highest first)
            sorted_users = sorted(self.bank.items(), key=lambda x: x[1], reverse=True)

            # Limit to top 10
            top_users = sorted_users[:100]


            paginator = self.bot.cogs["PaginatorCog"]()  # type: ignore

            # Create paginated embeds
            for i in range(0, len(top_users), 10):  # Show 10 users per page
                embed = discord.Embed(title="Economy Leaderboard", color=discord.Color.gold())
                for idx, (user_id, balance) in enumerate(top_users[i:i+10], start=i+1):
                    embed.add_field(name=f"{idx}. <@{user_id}>", value=f"{balance} eden coins", inline=False)

                paginator.add_page(embed)

            await paginator.send(ctx)  # Send paginated leaderboard

        except Exception as e:
            await ctx.send(e) # type: ignore

    @commands.command(name='coinflip', aliases=['cf', 'toss'])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def coinflip(self, ctx: commands.Context, *, txt: str):
        earn = 1000
        sides = ['heads', 'tails']
        toss = random.choice(sides)

        if txt.lower() in sides:
            if txt.lower() == toss:
                self.add(ctx.author, earn)
                await ctx.send(f"You won {earn} eden coins!")
            else:
                await ctx.send('You lost')
        else:
            await ctx.send('Pick either ``heads`` or ``tails``')

    @commands.command(name='subbal')
    @commands.has_any_role(ROLES.MODERATOR)
    @commands.cooldown(1,500, commands.BucketType.user)
    async def subbal(self, ctx: commands.Context, member: MemberLike, amount: int):
        self.sub(member, amount)
        await ctx.send(f"{member}'s balance is now {self.get(member)} eden coins")

    @commands.command(name='setbal')
    @commands.has_any_role('Bonked by Zi')
    async def setbal(self, ctx: commands.Context, member: MemberLike, coins: int):
        self.set(member, coins)  # Set balance to specified coins
        await ctx.send(f"{member.mention if isinstance(member, Member) else member} 's balance is {coins} eden coins")

    @setbal.error
    async def setbal_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingAnyRole):
            await ctx.send('You do not have permission to use this command.')

    @commands.command(name='win')
    async def win(self, ctx: commands.Context):
        userid = ctx.author.name
        price = 1_000_000
        if self.get(ctx.author) < price:
            await ctx.send(f"You do not have enough coins to win. You need at least {price:,} eden coins.")
            return
        else:
            self.sub(ctx.author, price)
            channel: discord.TextChannel = self.bot.get_channel(CHANNELS.WINNERS)  # type: ignore
            await channel.send(f"{ctx.author.mention} won the prize")

    @commands.command(name='roulette')
    @commands.cooldown(1,180, commands.BucketType.user)
    async def roulette(self, ctx: commands.Context, bullets: int):
        if bullets < 1 or bullets > 5:
            self.roulette.reset_cooldown(ctx) # type: ignore
            await ctx.send('Please choose between 1 to 5 bullets')
            return

        chamber = [1] * bullets + [0] * (6 - bullets)
        random.shuffle(chamber)
        print(f'shuffled chambers: {chamber}') # Debug feature

        fired_chamber = random.choice(chamber)

        if fired_chamber == 0:
            earn = 10000 * bullets
            self.add(ctx.author, earn)
            await ctx.send(f'You earned {earn:,} eden coins!')
        else:
            await ctx.send(f'You died! Try again in 3 minutes')

    @roulette.error
    async def roulette_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(f'{" ".join(ctx.args)} isn\'t a number, dumbass.')
            self.roulette.reset_cooldown(ctx) # type: ignore
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"You are still dead\nWait a little longer")

    @commands.command(name='slots', aliases=['slot', 'oldgamble'])
    async def slots(self, ctx: commands.Context):
        cost = 15_000
        bot_choice = random.randint(1, 50)
        if self.get(ctx.author) < cost:
            await ctx.send(f'You do not have enough coins, you need {cost:,} to participate')
            return
        if bot_choice == 6:
            earn = 2_500_000
            self.add(ctx.author, earn)
            await ctx.send(f'You won {earn:,} eden coins!')
            bot_updates_channel: discord.TextChannel = self.bot.get_channel(CHANNELS.BOT_LOGS)  # type: ignore
            await bot_updates_channel.send(f"User {ctx.author.mention} won {earn:,} coins in slots!")
        else:
            self.sub(ctx.author, cost)
            await ctx.send(f'You lost {cost:,} eden coins.')

    
    @commands.command(name="steal", aliases=["rob", "heist"])
    @commands.cooldown(1,1200, commands.BucketType.user)
    async def steal(self, ctx: commands.Context, member: Member):
        userid = ctx.author.id
        memberid = ctx.member.id
        balance = int(self.get(memberid))
        reward = balance // 2
        if member.bot:
            if member.id == self.bot.user.id: # type: ignore
                await ctx.send("Oh no you little shit, you are NOT stealing from me!")
            else: 
                await ctx.send("I won't let you steal from a bot.")
            return
        if member == ctx.author:
            await ctx.send("That's already your money, dumbass.") # me when I can't use retard D:
            return
        
        success = randint(1,5)
        if success == 3:
            self.sub(member, reward)
            self.add(ctx.author,reward)
            self.steal.reset_cooldown(ctx)
            await ctx.send(f"You have successfully stolen from {member.display_name}\n-# don't worry I'm not gonna ping like a snitch hehe~")
        else:
            #TODO: Add more responses 
            await ctx.send("You were caught dumbass\nLeave it to the professionals next time. 'kay?")
            await ctx.send(f"Oh {member.mention}\nSomeone was trying to steal from youuu")



    @commands.command(name='give')
    async def give(self, ctx: commands.Context, member: Member, coins: int):
        """Gives a specified amount of coins to another user."""
        if coins <= 0:
            await ctx.send("This isn't `;invest`, you can't just abuse the bot like that.")
            return

        if member.bot:
            if member.id == self.bot.user.id: # type: ignore
                await ctx.send("Why are you giving me these coins? I don't need them!")
            else: 
                await ctx.send("Bots don't have rights.")
            return
        if member == ctx.author:
            await ctx.send("That's already your money, dumbass.") # me when I can't use retard D:
            return
            
        if self.get(ctx.author) < coins:
            await ctx.send(random.choice([
                        f"{ctx.author.mention} is so broke they can't even afford to give {coins:,} coins.",
                        f"{ctx.author.mention} tried to help the poor but didn't realize they were the poor",
                        f"{coins:,} coins? {ctx.author.mention}, you need to work harder!",
                        f"{member.mention} won't be receiving any coins from {ctx.author.mention} today.",
                    ]))
            return
        if coins >= 25_000:
            await("You can't give more than 25k hun\nWhere's the fun in that?")
            return

        self.sub(ctx.author, coins)
        self.add(member, coins)
        await ctx.send(random.choice([
            f"{ctx.author.mention} gave {coins:,} eden coins to {member.mention}.",
            f"{ctx.author.mention} generously donated {coins:,} eden coins to {member.mention}.",
            f"{ctx.author.mention} is feeling generous and gave away {coins:,} eden coins to {member.mention}.",
            f"{member.mention} just received {coins:,} eden coins from {ctx.author.mention}.",
            f"{member.mention} was so poor that {ctx.author.mention} had to step in with {coins:,} eden coins.",
            f"{ctx.author.mention} spared {member.mention} some change. {coins:,} eden coins, to be exact.",
            f"{ctx.author.mention} did some charity work for {member.mention}, but only had the heart to give {coins:,} eden coins.",
            f"{ctx.author.mention} paid {member.mention} {coins:,} eden coins for their services.",
            f"{ctx.author.mention} decided to buy *totally legal* substances from {member.mention} for {coins:,} eden coins.",
            f"{member.mention}, you should buy \"sugar\" from {ctx.author.mention} with the {coins:,} eden coins they just gave you.\n-# (blame Germanic)",
        ]))

    @commands.command(name="daily")
    @commands.cooldown(1,86400, commands.BucketType.user)
    async def daily(self, ctx: commands.Context):
        """Log in every day for your rewards"""
        #TODO: Rework how daily records time
        userid = ctx.author.name
        earn = 10_000
        #TODO: Add a json file that records a user's streak and gives an appropriate bonus
        balance = self.get(userid)
        self.add(ctx.author, coins:=(earn))
        await ctx.send(f"You have completed your daily and earned {coins} eden coins")

        self.__save_bank()

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
                f"99% of gamblers quit before they hit big", # f-string because % formatting screws up syntax highlighting
                f"You lost, but don't worry, the jackpot is now at {self.jackpot['jackpot']:,} coins.",
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