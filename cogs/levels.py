from typing import Optional
import discord
from discord import Member
from discord.ext import commands
import asyncio
import logging
import os
import io 
from random import randint
import json
from PIL import Image, ImageDraw, ImageFont
from flask import ctx
import requests
from constants import ROLES


log = logging.getLogger(__name__)

class Levels(commands.Cog):
    def __init__(self, bot: commands.Bot, storage):
        self.bot = bot
        self.storage = storage
        self.cooldowns = {}

    def _get_level_xp(self, level: int) -> int:
        # XP needed to reach the *next* level
        return 5 * (level ** 2) + 50 * level + 100

    def _get_level_from_xp(self, xp: int) -> int:
        level = 0
        while xp >= sum(self._get_level_xp(i) for i in range(level + 1)):
            level += 1
        return level


    def is_ban(self, member: discord.Member) -> bool:
        banned_names = {"BadUser"}
        banned_roles = {"Muted"}
        return member.name in banned_names or any(role.name in banned_roles for role in member.roles)
    
    async def assign_level_roles(self, member: discord.Member):
        milestone_roles = {
            10: 1000316894567485471,
            20: 1000317394020995082,
            30: 1000317942065545327,
            50: 1000318886396309577,
            75: 1000321714837782529,
            100: 1000322372466909274
        }

        guild_id = str(member.guild.id)
        user_id = str(member.id)
        xp = int(self.storage.get(f"{guild_id}:{user_id}:xp") or 0)
        level = self._get_level_from_xp(xp)

        for milestone, role_id in milestone_roles.items():
            role = member.guild.get_role(role_id)
            if role and level >= milestone and role not in member.roles:
                try:
                    await member.add_roles(role)
                    log.info(f"Gave role {role.name} to {member.name} for Level {level}")
                except discord.Forbidden:
                    log.warning(f"Cannot assign {role.name} — check bot permissions!")

    @commands.command(name="import_mee6")
    async def import_mee6(self, ctx):
        """Imports full MEE6 leaderboard data into local storage"""
        guild_id = str(ctx.guild.id)
        all_players = []
        page = 0
        per_page = 100  # MEE6's default page size

        try:
            while True:
                api_url = f"https://mee6.xyz/api/plugins/levels/leaderboard/{guild_id}?page={page}"
                response = requests.get(api_url)
                response.raise_for_status()
                data = response.json().get("players", [])

                if response.status_code == 429:
                    await asyncio.sleep(10)
                    continue  # retry the same page
                if not data:
                    break  # Stop when no more data is returned

                all_players.extend(data)
                await asyncio.sleep(1) 
                page += 1

            if not all_players:
                await ctx.send("No leaderboard data found from MEE6.")
                return

            for player in all_players:
                user_id = str(player["id"])
                total_xp = int(player["xp"])
                self.storage.set(f"{guild_id}:{user_id}:xp", total_xp)
                self.storage.add(f"{guild_id}:players", user_id)

            await ctx.send(f"✅ Imported {len(all_players)} players from MEE6.")
        except requests.exceptions.RequestException as e:
            await ctx.send(f"⚠️ Failed to fetch MEE6 data: {str(e)}")
            
    @commands.command(name="rank")
    async def rank_cmd(self, ctx: commands.Context, member: Optional[discord.Member] = None): # type: ignore
        member: Member = member or ctx.author # type: ignore
        if self.is_ban(member):  # Assuming you have this method
            return
        if ctx.guild is None:
            await ctx.send("This command can only be used in a server.")
            return

        server_id = str(ctx.guild.id)
        user_id = str(member.id)
        xp_key = f"{server_id}:{user_id}:xp"
        xp = int(self.storage.get(xp_key) or 0)
        level = self._get_level_from_xp(xp)
        xp_in_level = xp - sum(self._get_level_xp(i) for i in range(level))
        level_xp = self._get_level_xp(level) or 1  # Avoid divide by zero
        players = self.storage.get(f"{server_id}:players") or []
        player_xps = [
            int(self.storage.get(f"{server_id}:{pid}:xp") or 0)
            for pid in players
        ]
        rank = 1 + sum(1 for other_xp in player_xps if other_xp > xp)

        # Create background
        width, height = 600, 150
        background = Image.new("RGBA", (width, height), (30, 30, 30, 255))
        draw = ImageDraw.Draw(background)

        # Fonts (safe fallback if arial.ttf not found)
        try:
            font_large = ImageFont.truetype("arial.ttf", 24)
            font_small = ImageFont.truetype("arial.ttf", 18)
        except OSError:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()

        # Avatar
        avatar_asset = member.display_avatar.with_size(128)
        avatar_bytes = await avatar_asset.read()
        avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA").resize((100, 100))
        background.paste(avatar, (20, 25), avatar)

        # Username and level
        draw.text((140, 30), member.name, font=font_large, fill=(255, 255, 255))
        draw.text((140, 65), f"Level: {level}", font=font_small, fill=(200, 200, 200))
        draw.text((140, 90), f"Rank: #{rank}", font=font_small, fill=(200, 200, 200))

        # Progress bar
        bar_x, bar_y = 140, 120
        bar_width, bar_height = 400, 20
        progress = xp_in_level / level_xp
        draw.rectangle([bar_x, bar_y, bar_x + bar_width, bar_y + bar_height], fill=(50, 50, 50))
        draw.rectangle(
            [bar_x, bar_y, bar_x + int(bar_width * progress), bar_y + bar_height],
            fill=(102, 255, 102)
        )
        draw.text(
            (bar_x + bar_width + 10, bar_y),
            f"{xp_in_level}/{level_xp}",
            font=font_small,
            fill=(255, 255, 255)
        )

        # Send image
        with io.BytesIO() as image_binary:
            background.save(image_binary, "PNG")
            image_binary.seek(0)
            await ctx.send(file=discord.File(fp=image_binary, filename="rank.png"))

    @commands.command(name="levels")
    async def levels_cmd(self, ctx):
        url = f"http://mee6.xyz/levels/{ctx.guild.id}"
        await ctx.send(f"Go check **{ctx.guild.name}**'s leaderboard here: {url} 😉")

    @commands.command(name="export_levels")
    async def export_levels(self, ctx):
        """Exports current level data to JSON file"""
        self.storage.export_to_json("levels_data.json")
        await ctx.send("✅ Level data exported to `levels_data.json`")

    @commands.command(name="setxp")
    @commands.has_any_role(ROLES.TOTALLY_MOD, ROLES.MODERATOR)
    async def setxp(self, ctx, member: discord.Member, level: int):
        try:
            """Sets a member's XP to match the requested level - 10 XP"""
            if self.is_ban(member):
                await ctx.send("⛔ Member is restricted from XP updates.")
                return

            # Calculate total XP needed to reach the target level
            target_xp = sum(self._get_level_xp(i) for i in range(level)) - 10

            server_id = str(ctx.guild.id)
            user_id = str(member.id)

            self.storage.set(f"{server_id}:{user_id}:xp", target_xp)
            self.storage.add(f"{server_id}:players", user_id)

            await ctx.send(f"✅ {member.mention}'s XP has been set to match **Level {level} - 10 XP**.")

            # Optionally, reassign level roles immediately
            await self.assign_level_roles(member)
        except Exception as e:
            await ctx.send(f"⚠️ Error setting XP: {str(e)}")
    

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        user_id = str(message.author.id)
        server_id = str(message.guild.id)
        now = asyncio.get_event_loop().time()

        if self.cooldowns.get(user_id, 0) > now:
            return

        self.cooldowns[user_id] = now + 60  # ⏱️ 60s cooldown per user

        xp_key = f"{server_id}:{user_id}:xp"
        prev_xp = int(self.storage.get(xp_key) or 0)
        xp_gain = randint(15, 25)  # slightly higher to match MEE6's pace
        new_xp = prev_xp + xp_gain

        prev_level = self._get_level_from_xp(prev_xp)
        new_level = self._get_level_from_xp(new_xp)

        self.storage.set(xp_key, new_xp)
        self.storage.add(f"{server_id}:players", user_id)

        if new_level > prev_level:
            await message.channel.send(f"{message.author.mention} leveled up to **Level {new_level}**! 🚀")
            await self.assign_level_roles(message.author)


    @commands.command(name="alllevels")
    async def alllevels(self, ctx):
        """DMs the author all stored level data in a TXT file"""

        # Build readable string from storage
        lines = []
        for key, value in self.storage.db.items():
            pretty_value = ", ".join(value) if isinstance(value, set) else str(value)
            lines.append(f"{key}: {pretty_value}")
        full_text = "\n".join(lines)

        # Create a binary file-like object for Discord
        file_bytes = io.BytesIO(full_text.encode("utf-8"))
        discord_file = discord.File(file_bytes, filename="levels_data.txt")

        try:
            await ctx.author.send("📄 Here's your server level data:", file=discord_file)
            await ctx.send("✅ Level data sent to your DMs.")
        except discord.Forbidden:
            await ctx.send("⚠️ I couldn't DM you. Check your privacy settings.")


# 💾 Dummy storage with JSON export
class DummyStorage:
    def __init__(self):
        self.db = {}

    def get(self, key):
        return self.db.get(key)

    def set(self, key, value):
        self.db[key] = value

    def add(self, key, value):
        self.db.setdefault(key, set()).add(value)

    def load_or_fetch_data(self):
        filepath = "levels_data.json"

        if os.path.exists(filepath):
            print("✅ Found cached data. Loading from file...")
            with open(filepath, "r") as f:
                data = json.load(f)
            return data
        else:
            return


    def export_to_json(self, filepath="levels_data.json"):
        json_ready = {k: list(v) if isinstance(v, set) else v for k, v in self.db.items()}
        with open(filepath, "w") as f:
            json.dump(json_ready, f, indent=4)


# 🔧 Cog setup function
async def setup(bot: commands.Bot):
    storage = DummyStorage()

    # Load previously exported data (if it exists)
    cached_data = storage.load_or_fetch_data()
    if cached_data:
        for key, value in cached_data.items():
            if isinstance(value, list):
                storage.db[key] = set(value)
            else:
                storage.db[key] = value

    await bot.add_cog(Levels(bot, storage))