import datetime
import math
from discord.ext import commands, tasks
import discord
from discord import Member
import json
import random
from typing import Optional, overload
from constants import CHANNELS, ROLES, USERS

# Type Hints
from cogs.inventory import InventoryCog
from cogs.paginator import PaginatorCog

class EconomyCog(commands.Cog):
    """All economy related commands and tasks."""
    ECONOMY_FILE = "bank.json"
    JACKPOT_FILE = "jackpot.json"
    type strint = str # Contains an ID, not a string
    type MemberLike = discord.User | discord.Member | str | int | strint
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bank: dict[str, int] = self.__load_bank() # type: ignore # New bank maps ID directly to balance
        # self.bank: dict[Literal["users"], list[BankEntry]] = self.__load_bank() # type: ignore # Load the bank every reload
        # TODO: not destroy my micro sd card with this
        self.jackpot_file = open(self.JACKPOT_FILE, "w") # Open file descriptor 3 for writing
        with open(self.JACKPOT_FILE, "r") as f:
            try:
                self.jackpot = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError, ValueError):
                self.jackpot = {'jackpot': 0}
    # Other Cogs
    def inventory(self) -> "InventoryCog":
        """Returns the InventoryCog instance."""
        cog = self.bot.get_cog("InventoryCog")
        if cog is None:
            raise RuntimeError("InventoryCog is not loaded.")
        return cog # type: ignore

    def __get_id(self, member: MemberLike) -> strint:
        if member is None or member == "users":
            return "0"
        if isinstance(member, (discord.User, discord.Member)):
            return str(member.id)
        elif isinstance(member, int):
            return str(member)
        elif isinstance(member, str):
            member = member.lower()
            if member.startswith("<@") and member.endswith(">"):
                return member[2:-1]
            else:
                try: 
                    return str(int(member))  # If it's a string that can be converted to an int
                except ValueError:
                    for m in self.bot.get_all_members():
                        if member == m.name.lower() or member == m.display_name.lower():
                            return str(m.id)
        raise ValueError(f"Invalid member type (got: {member} of type {type(member)})")

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
        self.set(user, self.get(user) + coins)
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
            self.set(user_id, 0)  # If user doesn't exist, set balance to 0
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

    @work.error
    async def work_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send("Please make an account with `;bal` first.")
    # Economy commands
    @commands.command(name='bal')
    async def bal(self, ctx: commands.Context, user: Optional[Member] = None): # type: ignore
        await ctx.send(f"{user.mention + '\'s' if user else 'Your'} balance is {self.get(user or ctx.author):,} eden coins.")
    
    @commands.has_any_role(ROLES.TOTALLY_MOD)
    @commands.command(name='fixbank', aliases=['fixbal', 'wtfhappy'])
    async def fixbank(self, ctx: commands.Context, key: str = "users"):
        """Fixes the bank by reloading it from the file."""
        amount = self.bank[key]
        del self.bank[key]
        self.__save_bank()
        await ctx.send(f"Bank has been fixed. ({amount})")

    @commands.command(name="topbal", aliases=["bals", "baltop"])
    async def topbal(self, ctx: commands.Context):
        """Displays the top users with the highest balance"""
        try:
            # Extract and sort user balances
            sorted_users = sorted(self.bank.keys(), key=lambda x: self.get(x), reverse=True)
            # Limit to top 100 users
            top_users = list(sorted_users)[:100]
            # Remove protected users
            for user_id in self.protected_users:
                if str(user_id) in top_users:
                    top_users.remove(str(user_id))

            # Get paginator cog
            paginator_cog = self.bot.get_cog("PaginatorCog")
            if not paginator_cog:
                await ctx.send("PaginatorCog is not loaded.")
                return

            paginator: PaginatorCog.Paginator = paginator_cog()  # type: ignore # Assumes your PaginatorCog has this method

            # Create paginated embeds
            for i in range(0, len(top_users), 10):  # 10 users per page
                embed = discord.Embed(title="Economy Leaderboard", color=discord.Color.gold())
                for idx, user_id in enumerate(top_users[i:i + 10]):
                    embed.add_field(name=f"{i*10+idx+1}. {user.name or 'Unknown User' if (user:=self.bot.get_user(int(user_id))) else 'Unknown User'}", value=f"{self.get(user_id):,} Eden coins", inline=False)
                paginator.add_page(embed)

            await paginator.send(ctx)

        except Exception as e:
            await ctx.send(f"An error occurred: `{e}`")

    @commands.command(name='coinflip', aliases=['cf', 'toss'])
    async def coinflip(self, ctx: commands.Context, *, txt: str):
        earn = 1000
        sides = ['heads', 'tails']
        toss = random.choice(sides)

        if txt.lower() in sides:
            if txt.lower() == toss:
                self.add(ctx.author, earn)
                await ctx.send(f"{str(toss).capitalize()}! You won {earn} eden coins!")
            else:
                await ctx.send(f'{str(toss).capitalize()}! You lost')
        else:
            await ctx.send('Pick either ``heads`` or ``tails``')

    @commands.command(name='subbal')
    @commands.has_any_role(ROLES.MODERATOR, ROLES.TOTALLY_MOD)
    async def subbal(self, ctx: commands.Context, member: MemberLike, amount: int):
        self.sub(member, amount)
        await ctx.send(f"{member}'s balance is now {self.get(member)} eden coins")

    @commands.command(name='setbal')
    @commands.has_any_role("Bonked by Zi")
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
            earn = 5000 * bullets
            self.add(ctx.author, earn)
            await ctx.send(f'You earned {earn:,} eden coins!')
            self.roulette.reset_cooldown(ctx) # type: ignore
        else:
            await ctx.send(f'You died! Try again in 3 minutes')

    @roulette.error
    async def roulette_error(self, ctx: commands.Context, error):
        if not isinstance(error, commands.CommandOnCooldown):
            self.roulette.reset_cooldown(ctx)
        if isinstance(error, commands.BadArgument):
            await ctx.send(f'{" ".join(ctx.args)} isn\'t a number, dumbass.')
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
            earn = 800_000 # break-even is 750,000
            self.add(ctx.author, earn)
            await ctx.send(f'You won {earn:,} eden coins!')
            bot_updates_channel: discord.TextChannel = self.bot.get_channel(CHANNELS.BOT_LOGS)  # type: ignore
            await bot_updates_channel.send(f"User {ctx.author.mention} won {earn:,} coins in slots!")
        else:
            self.sub(ctx.author, cost)
            await ctx.send(f'You lost {cost:,} eden coins.')

    protected_users = [USERS.HAPPY, USERS.RAINBOW, USERS.FROST, USERS.SLOINAC, USERS.MASCIAN, USERS.VIC]
    @commands.command(name="steal", aliases=["rob", "heist"])
    @commands.cooldown(1, 7200, commands.BucketType.user)
    async def steal(self, ctx: commands.Context, member: Member):
        thief = ctx.author

        # Replace with the actual name or ID of the protected role

        # Check if the target has the protected role
        if member.id in self.protected_users:
            await ctx.send(f"{member.display_name} is protected and cannot be stolen from.")
            self.steal.reset_cooldown(ctx)  # type: ignore
            return

        if member.bot:
            if member.id == self.bot.user.id:  # type: ignore
                await ctx.send("Oh no you little rascal, you are NOT stealing from me!")
            else:
                await ctx.send("I won't let you steal from a bot.")
            self.steal.reset_cooldown(ctx)  # type: ignore
            return

        if member == thief:
            await ctx.send("That's already your money, genius.")
            self.steal.reset_cooldown(ctx)  # type: ignore
            return

        target_balance = self.get(member.id)
        if target_balance < 10:
            await ctx.send(f"{member.display_name} doesn't have enough money to steal from.")
            self.steal.reset_cooldown(ctx)  # type: ignore
            return

        reward = max(2_500_000, random.randint(target_balance // 20, target_balance // 5))  # Steal between 5% and 20% of the target's balance
        break_lock = False
        break_lockpick = False
        if self.inventory().has_item(member, "Lock", 1):
            if self.inventory().has_item(thief, "Lockpick", 1): # type: ignore
                break_lockpick = True
                chance = 4
            chance = 10
            break_lock = True
        else:
            chance = 3
        success = random.randint(1, chance)
        message = ""

        if success == 2:
            self.sub(member, reward)
            self.add(thief, reward)
            self.steal.reset_cooldown(ctx)  # type: ignore
            message += (
                f"You successfully stole {reward} coins from {member.display_name}!\n"
                f"-# Don't worry, I won't ping them like a snitch"
            )
            if break_lock:
                self.inventory().remove_item(member, "Lock", 1)
                message += "\nYou broke their lock, you little goblin!"
        else:
            message += "\nYou were caught! Leave it to the professionals next time, 'kay?"
            message += f"\n{member.mention}, someone just tried to steal from you!"
        if break_lockpick: # breaks every time
            self.inventory().remove_item(thief, "Lockpick", 1) # type: ignore
            if break_lock:
                message += "\nI guess you got what you needed out of that lockpick."
            else:
                message += "\nWell, there goes your lockpick."

        await ctx.send(message)

    @steal.error
    async def steal_error(self, ctx, error):
        command = self.bot.get_command("steal")
        reset = True
        if isinstance(error, commands.BadArgument):
            await ctx.send("Couldn't find that user. Please mention a valid member.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("You need to mention someone to steal from.")
        elif isinstance(error, commands.CommandOnCooldown):
            reset = False
            total_seconds = int(error.retry_after)
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60

            time_parts = []
            if hours > 0:
                time_parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
            if minutes > 0:
                time_parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
            if seconds > 0 or not time_parts:
                time_parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")

            time_string = ", ".join(time_parts)
            await ctx.send(f"You're on cooldown! Try again in {time_string}.")
        else:
            await ctx.send("An unexpected error occurred.")
        if reset:
            if command:
                command.reset_cooldown(ctx)


    @commands.command(name='give')
    @commands.cooldown(1,5, commands.BucketType.user)
    async def give(self, ctx: commands.Context, member: Member, coins: int):
        """Gives a specified amount of coins to another user."""
        if coins <= 0:
            await ctx.send("This isn't `;invest`, you can't just abuse the bot like that.")
            self.give.reset_cooldown(ctx) # type: ignore
            return

        if coins > 1000000:
            await ctx.send("You can't give more than a million bud\nWhere's the fun in that?")
            self.give.reset_cooldown(ctx) # type: ignore
            return

        if member.bot:
            if member.id == self.bot.user.id: # type: ignore
                await ctx.send("Why are you giving me these coins? I don't need them!")
            else: 
                await ctx.send("Bots don't have rights.")
            self.give.reset_cooldown(ctx) # type: ignore
            return
        if member == ctx.author:
            await ctx.send("That's already your money, dumbass.") # me when I can't use retard D:
            self.give.reset_cooldown(ctx) # type: ignore
            return
            
        if self.get(ctx.author) < coins:
            await ctx.send(random.choice([
                        f"{ctx.author.mention} is so broke they can't even afford to give {coins:,} coins.",
                        f"{ctx.author.mention} tried to help the poor but didn't realize they were the poor",
                        f"{coins:,} coins? {ctx.author.mention}, you need to work harder!",
                        f"{member.mention} won't be receiving any coins from {ctx.author.mention} today.",
                    ]))
            self.give.reset_cooldown(ctx) # type: ignore
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
    @commands.cooldown(1, 86400, commands.BucketType.user)  # 24-hour cooldown
    async def daily(self, ctx: commands.Context):
        """Log in every day for your rewards"""
        user = ctx.author
        user_id = user.id
        earn = 10_000

        # TODO: Add a JSON file that records a user's streak and gives an appropriate bonus
        current_balance = self.get(user_id)
        self.add(user, earn)

        await ctx.send(f"{user.display_name}, you’ve claimed your daily reward of {earn:,} Eden coins!")
    @daily.error
    async def daily_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send("Come back again tomorrow\n-# impatient ass")

    @commands.command(name='pot', aliases=['jackpot'])
    async def pot(self, ctx: commands.Context):
        """Displays the current jackpot amount."""
        await ctx.send(f"The current jackpot is {self.jackpot['jackpot']:,} coins.\nThe current chance of winning is 1 in {math.floor(math.log(self.jackpot['jackpot'], 10) * 50) - 235}.")
    @commands.command(name='setpot', aliases=['setjackpot'])
    @commands.has_any_role(ROLES.TOTALLY_MOD)
    async def setpot(self, ctx: commands.Context, amount: int):
        """Sets the jackpot to a specified amount."""
        if amount < 0:
            await ctx.send("The jackpot cannot be negative.")
            return
        self.jackpot['jackpot'] = amount
        await self.save_jackpot_task()
        await ctx.send(f"The jackpot has been set to {amount:,} coins.")

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
        chance = math.floor(math.log(self.jackpot['jackpot'], 10) * 50) - 235
        # TODO: chance logic
        if random.randint(1, chance) == 3:
            # User wins
            win_amount = min(10_000_000, self.jackpot['jackpot'] * 2)  # Maximum win amount is 10 million
            self.set(userid, balance + win_amount)
            self.jackpot['jackpot'] = max(100_000, self.jackpot['jackpot'] - win_amount)  # Reset jackpot after win
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
            self.jackpot['jackpot'] += 36_000
        if self.jackpot['jackpot'] < 100_000:
            self.jackpot['jackpot'] += 100_000
        await self.save_jackpot_task()
        # print(f"Jackpot increased to {self.jackpot['jackpot']} coins")
    @tasks.loop(hours=1)
    async def save_jackpot_task(self):
        """A task that runs every hour to save the jackpot data."""
        self.jackpot_file.write(json.dumps(self.jackpot))
        self.jackpot_file.seek(0, 0) # start of file
        self.jackpot_file.flush()
        print("Jackpot data saved.")

    async def cog_load(self):
        """Fires when the cog is loaded."""
        self.jackpot_task.start()
        self.save_jackpot_task.start()

    async def cog_unload(self):
        """Fires when the cog is unloaded."""
        self.__save_bank()
        # Save jackpot data
        await self.save_jackpot_task()
        return await super().cog_unload()

async def setup(bot: commands.Bot):
    """Function to load the cog."""
    await bot.add_cog(EconomyCog(bot))
    print("EconomyCog has been (re-)loaded.")