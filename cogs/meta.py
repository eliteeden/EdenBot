from discord.ext import commands
import discord
import os

class MetaCog(commands.Cog):
    """A cog for Eden Bot meta."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot


    @commands.command(name="countlines", aliases=["countlines", "countlinescode", "lines"])
    async def count_lines(self, ctx):
        """Counts all lines in main.py and cogs/*.py"""
        total_lines = 0
        file_count = 0
        paths_checked = []

        # Define paths to check
        paths = ["main.py", "cogs"]

        for path in paths:
            if os.path.isfile(path) and path.endswith(".py"):
                with open(path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    total_lines += len(lines)
                    file_count += 1
                    paths_checked.append(path)
            elif os.path.isdir(path):
                for root, _, files in os.walk(path):
                    for file in files:
                        if file.endswith(".py"):
                            full_path = os.path.join(root, file)
                            with open(full_path, "r", encoding="utf-8") as f:
                                lines = f.readlines()
                                total_lines += len(lines)
                                file_count += 1
                                paths_checked.append(full_path)

        await ctx.send(
            f"📄 Counted `{file_count}` Python files.\n🧮 Total lines of code: `{total_lines}`\n✅ Files scanned:\n" +
            "\n".join(f"- `{p}`" for p in paths_checked)
        )

async def setup(bot):
    """Load the MetaCog cog."""
    await bot.add_cog(MetaCog(bot))
    print("MetaCog has been loaded.")