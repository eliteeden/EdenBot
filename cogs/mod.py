import discord
from discord.ext import commands
from discord import Member, User
import datetime
import asyncio
import random
import json
import os

from sympy import true
from constants import ROLES, CHANNELS

# Initialize the report dictionary
if os.path.exists("reports.json"):
    # Load the report from the file
    with open("reports.json", "r") as f:
        report = json.load(f)
else:
    # Create a new report if the file doesn't exist
    report = {"users": [], "next_warn_id": 1}  # Start with warning ID 1


class ModCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.snipe_messages = {}

    @commands.command(aliases=["timeout"])
    @commands.has_permissions(moderate_members=True)
    async def mute(self, ctx, member: Member, timelimit):
        if "s" in timelimit:
            gettime = timelimit.strip("s")
            if int(gettime) > 2419200:
                await ctx.send("Mute time cannot be greater than 28 days.")
            else:
                newtime = datetime.timedelta(seconds=int(gettime))
                await member.edit(timed_out_until=discord.utils.utcnow() + newtime)

        elif "h" in timelimit:
            gettime = timelimit.strip("h")
            if int(gettime) > 720:
                await ctx.send("Mute time cannot be greater than 28 days.")
            else:
                newtime = datetime.timedelta(hours=int(gettime))
                await member.edit(timed_out_until=discord.utils.utcnow() + newtime)

        elif "d" in timelimit:
            gettime = timelimit.strip("d")
            if int(gettime) > 28:
                await ctx.send("Mute time cannot be greater than 28 days.")
            else:
                newtime = datetime.timedelta(days=int(gettime))
                await member.edit(timed_out_until=discord.utils.utcnow() + newtime)
        elif "w" in timelimit:
            gettime = timelimit.strip("w")
            if int(gettime) > 4:
                await ctx.send("Mute time cannot be greater than 28 days.")
            else:
                newtime = datetime.timedelta(weeks=int(gettime))
                await member.edit(timed_out_until=discord.utils.utcnow() + newtime)
        await ctx.send(f"{member.mention} was muted for {timelimit}")

    @commands.command(aliases=["untimeout", "timein"])
    @commands.has_permissions(moderate_members=True)
    async def unmute(self, ctx, member: Member):
        await member.edit(timed_out_until=None)

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, user_id: int = None, *, reason: str = None):
        if not user_id:
            await ctx.send("Please provide a valid user ID to ban.")
            return
        if not reason:
            reason = "No reason provided."
        try:
            await ctx.guild.ban(
                discord.Object(id=user_id),
                reason=f"Banned by {ctx.author.name} - {reason}",
            )
            await ctx.send(f"<@{user_id}> has been banned.")
        except Exception as e:
            await ctx.send(f"An error occurred while banning the user: {e}")

    @commands.command(name="tempban")
    @commands.has_permissions(ban_members=True)
    async def tempban(
        self, ctx, user_id: int = None, duration: str = None, *, reason: str = None
    ):
        # Validate inputs
        if user_id is None or duration is None:
            await ctx.send("Usage: `!tempban <user_id> <duration> [reason]`")
            return

        # Convert duration string to seconds
        time_units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        try:
            unit = duration[-1]
            value = int(duration[:-1])
            seconds = value * time_units[unit]
        except (ValueError, KeyError):
            await ctx.send(
                "Invalid duration format. Use formats like `10m`, `2h`, `1d`."
            )
            return

        # Fetch user and ban
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.ban(user, reason=reason)
            await ctx.send(
                f"🔨 Banned {user} for {duration}. Reason: {reason or 'No reason provided'}"
            )
        except discord.NotFound:
            await ctx.send("User not found.")
            return
        except discord.Forbidden:
            await ctx.send("I don't have permission to ban that user.")
            return

        # Schedule unban
        await asyncio.sleep(seconds)
        try:
            await ctx.guild.unban(user)
            await ctx.send(f"✅ Unbanned {user} after {duration}.")
        except discord.NotFound:
            await ctx.send("User was already unbanned.")
        except discord.Forbidden:
            await ctx.send("I don't have permission to unban that user.")

    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def listrole(self, ctx, member: Member = None):
        if not member:
            member = ctx.author
        roles = [role.name for role in member.roles]
        await ctx.send(
            f"{member.display_name}'s roles: {'\n'.join(roles)}\n**{member.display_name} has {len(roles)} roles**"
        )

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user: User):
        await ctx.guild.unban(user)
        await ctx.send(f"**{user}** was unbanned")

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: Member):
        try:
            await member.kick()
            await ctx.send(f"**{member}** was kicked")
        except discord.Forbidden:
            await ctx.send("I don't have permission to kick this member.")
        except discord.HTTPException:
            await ctx.send("An error occurred while trying to kick the member.")

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, limit: int):
        await ctx.message.delete()
        await ctx.channel.purge(limit=limit)

    @commands.command(aliases=["userdel", "hpurge"])
    @commands.has_permissions(manage_messages=True)
    async def userpurge(self, ctx, limit: int):
        def is_user_message(message):
            return not message.author.bot

        await ctx.message.delete()
        await ctx.channel.purge(limit=limit, check=is_user_message)

    @commands.command(aliases=["bpurge", "botdel"])
    @commands.has_permissions(manage_messages=True)
    async def botpurge(self, ctx, limit: int):
        def is_bot_message(message):
            return message.author.bot

        await ctx.message.delete()
        await ctx.channel.purge(limit=limit, check=is_bot_message)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        attachments = [(a.url, a.content_type) for a in message.attachments]
        self.snipe_messages[message.channel.id] = (
            message.content,
            message.author,
            attachments,
        )

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def snipe(self, ctx):
        if ctx.channel.id not in self.snipe_messages:
            await ctx.send("There's nothing to snipe in this channel.")
        else:
            content, author, attachments = self.snipe_messages[ctx.channel.id]
            embed = discord.Embed(description=content, color=discord.Color.blue())
            embed.set_author(name=str(author), icon_url=author.avatar.url)
            for url, content_type in attachments:
                if "image" in content_type:
                    embed.set_image(url=url)
                    break
            await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def lurk(self, ctx):
        try:
            channel: discord.TextChannel = self.bot.get_channel(CHANNELS.CAPITAL)
            LURK_WINDOW_MINUTES = 5.0
            if not channel:
                await ctx.send("Channel not found.")
                return
            now = datetime.datetime.utcnow()
            cutoff_time = now - datetime.timedelta(minutes=LURK_WINDOW_MINUTES)
            messages = [
                msg async for msg in channel.history(limit=100, after=cutoff_time)
            ]
            active_users = {msg.author.id for msg in messages if not msg.author.bot}
            members = [
                m
                for m in channel.guild.members
                if not m.bot and m.status != discord.Status.offline
            ]
            lurkers = [m for m in members if m.id not in active_users]
            if lurkers:
                ping_count = min(4, len(lurkers))
                selected = random.sample(lurkers, ping_count)
                mentions = ", ".join(m.mention for m in selected)
                await channel.send(
                    f"Hey {mentions}, {'and everyone else, ' if len(lurkers) > 4 else ''}quit lurking like bitches 🥰"
                )
        except Exception as e:
            await ctx.send(f"Error: {e}")

    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def warn(self, ctx, user: discord.Member = None, *, reason: str = None):
        author = ctx.author
        if not user:
            await ctx.send("Please specify a valid member to warn.")
            return
        if author.top_role.position <= user.top_role.position:
            await ctx.send("You are not high enough in role hierarchy to do that")
            return
        roles = [role.id for role in ctx.author.roles]
        if not reason or not reason.strip():
            await ctx.send("Please provide a valid reason.")
            return
        if ROLES.MODERATOR in roles:
            warn_id = report["next_warn_id"]
            report["next_warn_id"] += 1
            await ctx.send(f"{user.mention} has been warned for: {reason}.")
            try:
                await user.send(
                    f"You have been warned in **{ctx.guild.name}** by **{author.name}** for: {reason}. (ID: {warn_id})\nDM the mods your noods in order to appeal"
                )
            except:
                await ctx.send(
                    f"Couldn't send DM to {user.mention}, but the warning has been recorded."
                )
            found = False
            for current_user in report["users"]:
                if current_user["name"] == user.name:
                    current_user["warnings"].append({"id": warn_id, "reason": reason})
                    found = True
                    break
            if not found:
                report["users"].append(
                    {"name": user.name, "warnings": [{"id": warn_id, "reason": reason}]}
                )
            with open("reports.json", "w+") as f:
                json.dump(report, f, indent=4)
        else:
            await ctx.send(
                f"{user.mention} stop annoying **{ctx.author.name}** by {reason}."
            )

    @commands.command(aliases=["rwarn", "-warn"])
    @commands.has_permissions(moderate_members=True)
    async def removewarn(self, ctx, warn_id: int = None):
        if not warn_id:
            await ctx.send("Please provide the warning ID to remove.")
            return
        removed = False
        for current_user in report["users"]:
            for warning in current_user["warnings"]:
                if warning["id"] == warn_id:
                    current_user["warnings"].remove(warning)
                    removed = True
                    break
            if removed:
                break
        if not removed:
            await ctx.send("Warning ID not found.")
            return
        with open("reports.json", "w+") as f:
            json.dump(report, f, indent=4)
        await ctx.send(f"Warning with ID `{warn_id}` has been removed.")

    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def warns(self, ctx, user: discord.Member):
        for current_user in report["users"]:
            if user.name == current_user["name"]:
                warnings = "\n".join(
                    [
                        f"ID: {w['id']}, Reason: {w['reason']}"
                        for w in current_user["warnings"]
                    ]
                )
                embed = discord.Embed(
                    title=f"Warnings for {user.name}",
                    description=f"{user.name} has {len(current_user['warnings'])} warnings:\n{warnings}",
                    color=0xFFFFFF,
                )
                await ctx.send(embed=embed)
                break
        else:
            await ctx.send(f"{user.name} has no warnings.")

    @commands.command(aliases=["sm", "slow"])
    @commands.has_permissions(manage_channels=True)
    async def slowmode(self, ctx, duration: str):
        if "s" in duration:
            dur = duration.strip("s")
            seconds = int(dur)
            await ctx.channel.edit(slowmode_delay=seconds)
            await ctx.send(f"Set the slow mode delay in this channel to {dur} seconds!")
        elif "m" in duration:
            dur = duration.strip("m")
            minutes = int(dur) * 60
            await ctx.channel.edit(slowmode_delay=minutes)
            await ctx.send(f"Set the slow mode delay in this channel to {dur} minutes!")
        elif "h" in duration:
            dur = duration.strip("h")
            hours = int(dur) * 3600
            await ctx.channel.edit(slowmode_delay=hours)
            await ctx.send(f"Set the slow mode delay in this channel to {dur} hours!")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def endslow(self, ctx):
        await ctx.channel.edit(slowmode_delay=0)
        await ctx.send("Slow-mode is off!")


async def setup(bot):
    await bot.add_cog(ModCog(bot))
    print("ModCog has been loaded successfully.")
