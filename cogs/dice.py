from discord.ext import commands
import random


class DiceCog(commands.Cog):
    """A cog for rolling dice."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="roll", aliases=["roll_dice"])
    async def better_roll(self, ctx: commands.Context, *, dice: str = ""):
        """Roll one or more dice. Example: ;roll 1d2 3d4. Put a + or a - after the roll (1d20+) for advantage or disadvantage"""
        if dice == "":
            return await ctx.send(
                "I'll roll this whole table over if you don't give me some dice."
            )
        dice_list = dice.split(" ")
        rolls = []
        total = 0
        if dice_list == []:
            return await ctx.send("No dice specified?")
        for die in dice_list:

            current_rolls = []
            advantage = 0
            if die[-1] == "+":
                advantage = 1
            elif die[-1] == "-":
                advantage = -1
            die = die.rstrip("+-")
            if "d" in die:
                num, side = die.split("d")
                num = 1 if num == "" else int(num)
                side = 20 if side == "" else int(side)
            elif die.isdigit():
                side = int(die)
                num = 1
            else:
                return await ctx.send(
                    f"Invalid die format: {die}. Use format like 1d20 or 3d6."
                )
            if advantage != 0:
                num += 1
            for _ in range(num):
                roll = random.randint(1, side)
                current_rolls += [roll]
            current_rolls.sort()
            match advantage:
                case 1:
                    current_rolls = current_rolls[1:]
                case -1:
                    current_rolls = current_rolls[:-1]
            total += sum(current_rolls)
            rolls += current_rolls

        match len(rolls):
            case 0:
                return await ctx.send("No dice rolled?")
            case 1:
                return await ctx.send(f"{ctx.author.mention} rolled a **{rolls[0]}**.")
            case 2:
                return await ctx.send(
                    f"{ctx.author.mention} rolled a {rolls[0]} and a {rolls[1]}, totalling: **{total}**"
                )
            case _ as num:
                return await ctx.send(
                    f"{ctx.author.mention} rolled {num} dice: {', '.join(map(str, rolls[:-1]))}, and a {rolls[-1]}, totalling: **{total}**"
                )

    @commands.command(name="roll_num", aliases=["dice", "d"])
    async def roll_dice(self, ctx: commands.Context, sides: int = 6):
        """Roll a dice with the specified number of sides (default is 6)."""
        if sides < 2:
            await ctx.send("The number of sides must be at least 2.")
            return

        result = random.randint(1, sides)
        await ctx.send(
            f"{ctx.author.mention} rolled a {result} on a {sides}-sided die."
        )

    @commands.command(name="d20")
    async def roll_d20(self, ctx: commands.Context):
        """Roll a 20-sided die."""
        result = random.randint(1, 20)
        if result == 20:
            await ctx.send(f"{ctx.author.mention}, you rolled a 20. Congratulations!")
        elif result == 1:
            await ctx.send(f"{ctx.author.mention}, you rolled a 1. Good luck...")
        else:
            await ctx.send(f"{ctx.author.mention}, you rolled a {result}.")

    @commands.command(name="d6")
    async def roll_d6(self, ctx: commands.Context):
        return await self.roll_dice(ctx, 6)

    @commands.command(name="d100")
    async def roll_d100(self, ctx: commands.Context):
        return await self.roll_dice(ctx, 100)

    @commands.command(name="d24")
    async def roll_d24(self, ctx: commands.Context):
        return await self.roll_dice(ctx, 24)


async def setup(bot: commands.Bot):
    """Function to load the DiceCog."""
    await bot.add_cog(DiceCog(bot))
    print("DiceCog has been loaded.")
