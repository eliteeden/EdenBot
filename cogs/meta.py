from encodings import aliases
from discord.ext import commands
import discord
import os
import subprocess
from collections import Counter
import time
import psutil, platform
start_time = time.time()
#SO META

class MetaCog(commands.Cog):
    """A cog for Eden Bot meta."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot


    @commands.command(name="countlines", aliases=["botlines", "countlinescode", "lines"])
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

    @commands.command(name="contributions", aliases=["coderstats", "contribs", "gitstats"])
    async def contributions(self, ctx):
        """Estimates contributor percentages using git blame."""
        async with ctx.typing():
            repo_path = os.getcwd()
            author_counter = Counter()
            total_lines = 0

            # Collect all .py files
            py_files = []
            for root, _, files in os.walk(repo_path):
                for file in files:
                    if file.endswith(".py"):
                        py_files.append(os.path.join(root, file))

            # Run git blame on each file
            for file_path in py_files:
                try:
                    result = subprocess.run(
                        ["git", "blame", "--line-porcelain", file_path],
                        capture_output=True, text=True, check=True
                    )
                    for line in result.stdout.splitlines():
                        if line.startswith("author "):
                            author = line[len("author "):]
                            author_counter[author] += 1
                            total_lines += 1
                except subprocess.CalledProcessError:
                    continue  # Skip files not tracked by Git

            if total_lines == 0:
                return await ctx.send("No tracked lines found. Is this a Git repo?")

            # Build response
            response = "📊 **Contribution Breakdown**:\n"
            for author, count in author_counter.most_common():
                percent = (count / total_lines) * 100
                response += f"- `{author}`: {count} lines ({percent:.2f}%)\n"

            await ctx.send(response)

    @commands.command(name="blame")
    async def blame_line(self, ctx, filename: str, line_number: int):
        """Blames a specific line in a file."""
        import subprocess
        try:
            result = subprocess.run(
                ["git", "blame", "-L", f"{line_number},{line_number}", "--", filename],
                capture_output=True, text=True, check=True
            )
            await ctx.send(f"🔍 Line {line_number} in `{filename}`: {result.stdout.strip()}")
        except Exception as e:
            await ctx.send(f"Could not blame line: {e}")

    @commands.command(name="blamefile", aliases=["blamepy", "blameall"])
    async def blame_file(self, ctx, filename: str):
        """Blames an entire file."""
        import subprocess
        try:
            result = subprocess.run(
                ["git", "blame", filename],
                capture_output=True, text=True, check=True
            )
            await ctx.send(f"🔍 Blame for `{filename}`:\n```\n{result.stdout.strip()}\n```")
        except Exception as e:
            await ctx.send(f"Could not blame file: {e}")


    @commands.command(name="uptime")
    async def uptime(self, ctx):
        """Displays bot uptime and roasts the second latest contributor."""
        # Calculate uptime
        seconds = int(time.time() - start_time)
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{hours}h {minutes}m {seconds}s"

        # Author mapping
        author_map = {
            "Henry": "<@921605971577548820>",
            "HappyJuice3": "<@1021831032347033680>"

        }
        # Get second latest commit author
        try:
            result = subprocess.run(
                ["git", "log", "--pretty=format:%an", "-n", "2"],
                capture_output=True, text=True, check=True
            )
            authors = result.stdout.strip().splitlines()
            if len(authors) >= 2:
                culprit = authors[1]
                if culprit in author_map:
                    culprit = author_map[culprit]
                else:
                    culprit = f"@{culprit.replace(' ', '').lower()}"
                
            else:
                culprit = "someone mysterious"
        except Exception as e:
            culprit = "an unknown force"
            print(f"[uptime] Git error: {e}")

        await ctx.send(f"⏱️ It has been {uptime_str} since **{culprit}** fucked up.")


    @commands.command(name="pong")
    async def pong(self, ctx):
        """Shows bot latency."""
        latency = self.bot.latency * 1000  # ms
        await ctx.send(f"🏓 Ping! Latency: `{latency:.2f}ms`")

    @commands.command(name="selfdestruct")
    async def self_destruct(self, ctx):
        """Fake bot shutdown sequence."""
        import asyncio
        await ctx.send("Initiating self-destruct sequence...")
        for i in range(10, 0, -1):
            await ctx.send(f"{i}...")
            await asyncio.sleep(1)
        await ctx.send("Just kidding teehee.")

    @commands.command(name="dna")
    async def dna(self, ctx):
        """Displays bot's internal stats."""
        
        process = psutil.Process()
        mem = process.memory_info().rss / 1024 / 1024
        uptime = int(time.time() - start_time)
        hours, rem = divmod(uptime, 3600)
        mins, secs = divmod(rem, 60)
        await ctx.send(
            f"🧬 **Bot DNA**:\n"
            f"- Commands: `{len(self.bot.commands)}`\n"
            f"- Cogs: `{len(self.bot.cogs)}`\n"
            f"- Uptime: `{hours}h {mins}m {secs}s`\n"
            f"- RAM: `{mem:.2f} MB`\n"
            f"- OS: `{platform.system()} {platform.release()}`"
        )

    @commands.command(name="commandstats", aliases=["cmdstats", "cmdcount"])
    async def commandstats(self, ctx):
        """Lists command counts by Cog."""
        cog_map = {}
        for cmd in self.bot.commands:
            cog = cmd.cog_name or "Uncategorized"
            cog_map.setdefault(cog, []).append(cmd.name)

        response = "**📊 Command Stats:**\n"
        for cog, cmds in cog_map.items():
            response += f"- `{cog}`: {len(cmds)} commands\n"
        await ctx.send(response)

async def setup(bot):
    """Load the MetaCog cog."""
    await bot.add_cog(MetaCog(bot))
    print("MetaCog has been loaded.")