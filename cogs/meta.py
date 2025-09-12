import asyncio
import sys
from typing import Literal, Optional
import aiohttp
from discord.ext import commands
import discord
import json
import os
import subprocess
from datetime import datetime
from collections import Counter
import time
from dotenv import load_dotenv
import psutil

from constants import ROLES

start_time = time.time()
DATA_FILE = "memberstats.json"


class MetaCog(commands.Cog):
    """A cog for Eden Bot meta."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.snapshot = self.load_snapshot()

    def load_snapshot(self):
        if not os.path.exists(DATA_FILE):
            with open(DATA_FILE, "w") as f:
                json.dump({}, f)
            return {}
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            with open(DATA_FILE, "w") as f:
                json.dump({}, f)
            return {}

    def save_snapshot(self):
        with open(DATA_FILE, "w") as f:
            json.dump(self.snapshot, f, indent=2)

    async def execvc(self, program: str, *args, cwd=None, env=None) -> str:
        """
        Executes a command without shell (execv-style).
        Usage: await execvc("ls", "-la")
        """
        result = await asyncio.create_subprocess_exec(
            program,
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd or os.getcwd(),
            env=env or os.environ.copy(),
        )
        stdout, stderr = await result.communicate()
        stdout = stdout.decode("utf-8").strip()
        stderr = stderr.decode("utf-8").strip()
        if result.returncode == 0:
            return stdout
        return f"Error ({result.returncode}): {stderr}"

    @commands.command(name="memberstats", aliases=["serverstats", "guildinfo", "edenstats"])
    async def memberstats(self, ctx: commands.Context):
        """Imports live server data and compares member count to last snapshot."""
        guild = ctx.guild
        await guild.chunk()

        members = guild.members
        total = len(members)
        bots = sum(1 for m in members if m.bot)
        humans = total - bots
        online = sum(1 for m in members if m.status != discord.Status.offline)
        offline = total - online

        roles = guild.roles
        channels = guild.channels
        text_channels = sum(1 for c in channels if isinstance(c, discord.TextChannel))
        voice_channels = sum(1 for c in channels if isinstance(c, discord.VoiceChannel))
        category_channels = sum(1 for c in channels if isinstance(c, discord.CategoryChannel))

        gid = str(guild.id)
        previous = self.snapshot.get(gid, {
            "last_count": total,
            "last_checked": datetime.utcnow().isoformat()
        })
        previous_count = previous["last_count"]
        previous_time = previous["last_checked"]

        net_change = total - previous_count
        change_symbol = "📈" if net_change > 0 else "📉" if net_change < 0 else "➖"

        embed = discord.Embed(
            title=f"📊 Server Stats: {guild.name}",
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=guild.icon.url if guild.icon else discord.Embed.Empty)
        embed.add_field(name="👥 Total Members", value=f"{total:,}", inline=True)
        embed.add_field(name="🧍 Humans", value=f"{humans:,}", inline=True)
        embed.add_field(name="🤖 Bots", value=f"{bots:,}", inline=True)
        embed.add_field(name="🟢 Online", value=f"{online:,}", inline=True)
        embed.add_field(name="⚫ Offline", value=f"{offline:,}", inline=True)
        embed.add_field(name="📅 Server Created", value=guild.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"), inline=False)
        embed.add_field(name="🔐 Verification Level", value=str(guild.verification_level).title(), inline=True)
        embed.add_field(name="🌐 Locale", value=str(guild.preferred_locale).upper(), inline=True)
        embed.add_field(name="📁 Roles", value=f"{len(roles):,}", inline=True)
        embed.add_field(name="💬 Text Channels", value=f"{text_channels:,}", inline=True)
        embed.add_field(name="🔊 Voice Channels", value=f"{voice_channels:,}", inline=True)
        embed.add_field(name="📂 Categories", value=f"{category_channels:,}", inline=True)
        embed.add_field(
            name="📊 Comparison",
            value=f"{change_symbol} Change since last check: {net_change:+,}\n🕒 Last checked: {previous_time}",
            inline=False
        )
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)

        await ctx.send(embed=embed)

        self.snapshot[gid] = {
            "last_count": total,
            "last_checked": datetime.now().isoformat()
        }
        self.save_snapshot()

    @commands.command(
        name="countlines", aliases=["botlines", "countlinescode", "lines"]
    )
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
            f"📄 Counted `{file_count}` Python files.\n🧮 Total lines of code: `{total_lines}`\n✅ Files scanned:\n"
            + "\n".join(f"- `{p}`" for p in paths_checked)
        )

    @commands.command(name="truecount", aliases=["truelines", "linesplus", "alllines"])
    async def truecount_lines(self, ctx):
        """Counts lines in Python and JSON files across the project, sending results in chunks."""

        total_lines = 0
        file_count = 0
        paths_checked = []

        paths = ["main.py", "cogs", "*.json"]
        valid_exts = [".py", ".json"]

        for path in paths:
            if os.path.isfile(path) and any(path.endswith(ext) for ext in valid_exts):
                with open(path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    total_lines += len(lines)
                    file_count += 1
                    paths_checked.append(path)
            elif os.path.isdir(path):
                for root, _, files in os.walk(path):
                    for file in files:
                        if any(file.endswith(ext) for ext in valid_exts):
                            full_path = os.path.join(root, file)
                            try:
                                with open(full_path, "r", encoding="utf-8") as f:
                                    lines = f.readlines()
                                    total_lines += len(lines)
                                    file_count += 1
                                    paths_checked.append(full_path)
                            except Exception as e:
                                print(f"[countfiles] Failed to read {full_path}: {e}")

        await ctx.send(
            f"📁 Counted `{file_count}` files (.py + .json).\n🧮 Total lines: `{total_lines}`\n✅ Files scanned:"
        )

    @commands.command(
        name="contributions", aliases=["coderstats", "contribs", "gitstats"]
    )
    async def contributions(self, ctx):
        """Estimates contributor percentages using git blame."""
        async with ctx.typing():
            repo_path = os.getcwd()
            author_counter = Counter()
            total_lines = 0

            py_files = []
            for root, _, files in os.walk(repo_path):
                for file in files:
                    if file.endswith(".py"):
                        py_files.append(os.path.join(root, file))

            for file_path in py_files:
                try:
                    result = subprocess.run(
                        ["git", "blame", "--line-porcelain", file_path],
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    for line in result.stdout.splitlines():
                        if line.startswith("author "):
                            author = line[len("author ") :]
                            author_counter[author] += 1
                            total_lines += 1
                except subprocess.CalledProcessError:
                    continue

            if total_lines == 0:
                return await ctx.send("No tracked lines found. Is this a Git repo?")

            response = "📊 **Contribution Breakdown**:\n"
            for author, count in author_counter.most_common():
                percent = (count / total_lines) * 100
                response += f"- `{author}`: {count} lines ({percent:.2f}%)\n"

            await ctx.send(response)

    @commands.command(name="blame")
    async def blame_line(self, ctx, filename: str, line_number: int):
        """Blames a specific line in a file."""
        try:
            result = subprocess.run(
                ["git", "blame", "-L", f"{line_number},{line_number}", "--", filename],
                capture_output=True,
                text=True,
                check=True,
            )
            await ctx.send(
                f"🔍 Line {line_number} in `{filename}`: {result.stdout.strip()}"
            )
        except Exception as e:
            await ctx.send(f"Could not blame line: {e}")

    @commands.command(name="blamefile", aliases=["blamepy", "blameall"])
    async def blame_file(self, ctx, filename: str):
        """Blames an entire file."""
        try:
            result = subprocess.run(
                ["git", "blame", filename], capture_output=True, text=True, check=True
            )
            await ctx.send(
                f"🔍 Blame for `{filename}`:\n```\n{result.stdout.strip()}\n```"
            )
        except Exception as e:
            await ctx.send(f"Could not blame file: {e}")

    @commands.command(name="uptime")
    async def uptime(self, ctx):
        """Displays bot uptime and roasts the second latest contributor."""
        seconds = int(time.time() - start_time)
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{hours}h {minutes}m {seconds}s"

        author_map = {
            "Henry": "<@921605971577548820>",
            "HappyJuice3": "<@1021831032347033680>",
        }
        try:
            result = subprocess.run(
                ["git", "log", "--pretty=format:%an", "-n", "2"],
                capture_output=True,
                text=True,
                check=True,
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
        latency = self.bot.latency * 1000
        await ctx.send(f"🏓 Ping! Latency: `{latency:.2f}ms`")

    @commands.command(
        name="selfdestruct",
        aliases=[
            "windowsmoment",
            "bsod",
            "yesiknowwhatthefuckimdoingandwanttoreload",
            "noidontknowwhatimdoingandwanttoreloadanyways",
        ],
    )
    async def self_destruct(self, ctx: commands.Context, for_real: bool = False):
        if (
            isinstance(ctx.author, discord.Member)
            and ctx.author.get_role(ROLES.TOTALLY_MOD)
            and for_real
        ):
            async def shutdown_wrapper():
                for file in os.listdir("cogs"):
                    if file.endswith(".py") and file != "meta.py":
                        await self.bot.unload_extension(f"cogs.{file[:-3]}")

            await ctx.send("Restarting...")
            await shutdown_wrapper()
            return await self.execvc("reload")

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
        load_dotenv("/etc/os-release")
        os_name = os.getenv("PRETTY_NAME") or await self.execvc("uname", "-mor")
        await ctx.send(
            f"🧬 **Bot DNA**:\n"
            f"- Commands: `{len(self.bot.commands)}`\n"
            f"- Cogs: `{len(self.bot.cogs)}`\n"
            f"- Uptime: `{f'{hours}h ' if hours else ''}{mins}m {secs}s`\n"
            f"- RAM: `{mem:,.2f} MB`\n"
            f"- OS: `{os_name}`\n"
        )

    @commands.command(name="commandstats", aliases=["cmdstats", "cmdcount"])
    async def commandstats(self, ctx):
        """Lists command counts by Cog."""
        cog_map = {}
        for cmd in self.bot.commands:
            cog = cmd.cog_name or "Uncategorized"
            cog_map.setdefault(cog, []).append(cmd.name)

        response = "**📊 Command Stats:**\n"
        response += f"Total: {len(self.bot.commands)} commands\n"
        for cog, cmds in cog_map.items():
            response += f"- `{cog}`: {len(cmds)} commands\n"
        await ctx.send(response)

    @commands.command(name="fetch", aliases=["neofetch", "fastfetch"])
    async def fetch(self, ctx):
        await self.execvc("neofetch", ">", "/tmp/fetch.ansi")
        output = await self.execvc("cat", "/tmp/fetch.ansi")
        await ctx.send("```ansi\n" + output + "\n```")

    @commands.command(name="status", aliases=["botstatus", "botinfo"])
    async def status(self, ctx: commands.Context):
        """Displays the bot's status."""
        embed = discord.Embed(
            title="Eden Bot Status",
            description=f"Currently running with {len(self.bot.cogs)} cogs and {len(self.bot.commands)} commands.",
            color=discord.Color.blue(),
        )
        embed.add_field(
            name="Last Reload",
            value=f"{int(time.time() - start_time)} seconds ago",
            inline=True,
        )
        uptime_out = await self.execvc("uptime", "-p")
        embed.add_field(
            name="System Uptime",
            value=uptime_out.removeprefix("up "),
            inline=True,
        )
        embed.add_field(
            name="Memory Usage",
            value=f"{psutil.Process().memory_info().rss / 1024 / 1024:.2f} MB",
            inline=True,
        )
        embed.add_field(
            name="Python Version", value=sys.version.split()[0], inline=True
        )
        embed.add_field(
            name="Discord.py Version", value=discord.__version__, inline=True
        )
        load_dotenv("/etc/os-release")
        embed.add_field(
            name="OS", value=os.getenv("PRETTY_NAME", "Unknown"), inline=True
        )
        try:
            ip = "Unknown"
            async with aiohttp.ClientSession() as session:
                async with session.get("https://httpbin.org/get") as resp:
                    data = await resp.json()
                    ip = data["origin"]
            if ip.startswith("99.") and ip.endswith(".53"):
                ip = "99.**.**.53"
            embed.add_field(name="External IP", value=ip, inline=True)
        except:
            embed.add_field(name="External IP", value="Could not fetch IP", inline=True)
        internal_ip = await self.execvc("hostname", "-I")
        embed.add_field(
            name="Internal IP", value=internal_ip.split()[0] if internal_ip else "Unknown", inline=True
        )
        warp_status = await self.execvc("warp-cli", "status")
        if "Disconnected" in warp_status:
            embed.add_field(name="Cloudflare", value="Disconnected", inline=True)
        elif "Connected" in warp_status:
            embed.add_field(name="Cloudflare", value="Connected", inline=True)
        else:
            embed.add_field(name="Cloudflare", value=warp_status, inline=True)
        embed.add_field(name="Server Count", value=len(self.bot.guilds), inline=True)
        embed.add_field(name="User Count", value=len(self.bot.users), inline=True)
        branches = await self.execvc("git", "branch")
        name = branches.strip().split("*")[-1].split("\n")[0].strip()
        num = len(branches.strip().split("\n")) - 1
        embed.add_field(
            name="Branch",
            value=f"Current: **{name}**, {num} {'slave' if name == 'master' else 'branch'}{('s' if name == 'master' else 'es') if num != 1 else ''}",
            inline=True,
        )
        embed.set_footer(text=f"Ping: {self.bot.latency * 1000:.2f}ms")
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    """Load the MetaCog"""
    await bot.add_cog(MetaCog(bot))
    print("MetaCog has been (re-)loaded successfully!")
