# This is for LaTeX and the eventual calculator command cos im lazy 

import discord
from discord.ext import commands
import math
import matplotlib.pyplot as plt
import io


class MathCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="latex", aliases=["ltx", "silk", "mathrender"])
    async def latex(self, ctx, *, code: str):
        """
        Render LaTeX code into an image and reply with it.
        Usage: !latex \sqrt{a^2 + b^2}
        """

        # Configure matplotlib to use LaTeX-style rendering
        plt.rc('text', usetex=False)
        plt.rc('font', family='serif')

        # Create figure
        fig = plt.figure(figsize=(0.1, 0.1))
        fig.text(0.5, 0.5, f"${code}$", fontsize=20, ha='center', va='center')

        # Save to memory buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight', pad_inches=0.3)
        buf.seek(0)
        plt.close(fig)

        # Send as reply
        file = discord.File(buf, filename="latex.png")
        await ctx.reply(file=file)

 
    @commands.command(name="calc", aliases=["mth"])
    async def calc(self, ctx, *, expression: str):
        """
        Safely evaluate a math expression.
        Usage: !calc 2 + 3 * (4 - 1)
        """

        allowed = {
            k: v for k, v in math.__dict__.items()
            if not k.startswith("__")
        }

        allowed["abs"] = abs
        allowed["round"] = round

        try:
            result = eval(expression, {"__builtins__": {}}, allowed)
        except Exception as e:
            return await ctx.reply(f"Error: {e}")

        await ctx.reply(f"**Result:** `{result}`")


    @commands.command(name="calctex", aliases=["solve", "calc2", "wtfcalc"])
    async def calctex(self, ctx, *, expression: str):
        """
        Evaluate a math expression and render the result in LaTeX.
        Usage: !calctex 5 * sin(pi/4)
        """

        allowed = {
            k: v for k, v in math.__dict__.items()
            if not k.startswith("__")
        }

        allowed["abs"] = abs
        allowed["round"] = round

        try:
            result = eval(expression, {"__builtins__": {}}, allowed)
        except Exception as e:
            return await ctx.reply(f"Error: {e}")

        # Render LaTeX
        plt.rc('text', usetex=False)
        plt.rc('font', family='serif')

        fig = plt.figure(figsize=(0.1, 0.1))
        fig.text(
            0.5, 0.5,
            f"${expression} = {result}$",
            fontsize=20,
            ha='center',
            va='center'
        )

        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight', pad_inches=0.3)
        buf.seek(0)
        plt.close(fig)

        file = discord.File(buf, filename="calc.png")
        await ctx.reply(file=file)


async def setup(bot):
    await bot.add_cog(MathCog(bot))
    print("MathCog has been loaded successfully")
