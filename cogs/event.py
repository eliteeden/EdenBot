import discord
from discord.ext import commands
import json
import os

CONFIG_FILE = "events.json"

class EventsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.events = self.load_events()

    def load_events(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        else:
            return {}

    def save_events(self):
        with open(CONFIG_FILE, "w") as f:
            json.dump(self.events, f, indent=4)

    # Event commands

    @commands.command(name="setwelcome", aliases=["sethello", "hellomsg", "welcomemsg"])
    @commands.has_permissions(manage_guild=True)
    async def set_welcome(self, ctx, channel: discord.TextChannel, *, message: str):
        """Sets a welcome message for a specific channel."""
        guild_id = str(ctx.guild.id)

        if "welcome" not in self.events:
            self.events["welcome"] = {}

        self.events["welcome"][guild_id] = {
            "channel_id": channel.id,
            "message": message
        }

        self.save_events()
        await ctx.send(f"Welcome message set for {channel.mention}.")


    @commands.command(name="setban")
    @commands.has_permissions(manage_guild=True)
    async def set_ban(self, ctx, channel: discord.TextChannel, *, message: str):
        """Sets a ban message for a specific channel."""
        guild_id = str(ctx.guild.id)
        self.events.setdefault("ban", {})
        self.events["ban"][guild_id] = {
            "channel_id": channel.id,
            "message": message
        }
        self.save_events()
        await ctx.send(f"Ban message set for {channel.mention}.")

    @commands.command(name="setleave")
    @commands.has_permissions(manage_guild=True)
    async def set_leave(self, ctx, channel: discord.TextChannel, *, message: str):
        """Sets a leave message for a specific channel."""
        guild_id = str(ctx.guild.id)
        self.events.setdefault("leave", {})
        self.events["leave"][guild_id] = {
            "channel_id": channel.id,
            "message": message
        }
        self.save_events()
        await ctx.send(f"Leave message set for {channel.mention}.")

    # Event listeners

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        guild_id = str(member.guild.id)
        if "leave" in self.events and guild_id in self.events["leave"]:
            data = self.events["leave"][guild_id]
            channel = self.bot.get_channel(data["channel_id"])
            if channel:
                await channel.send(data["message"].replace("{member}", member.name))

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        guild_id = str(guild.id)
        if "ban" in self.events and guild_id in self.events["ban"]:
            data = self.events["ban"][guild_id]
            channel = self.bot.get_channel(data["channel_id"])
            if channel:
                await channel.send(data["message"].replace("{member}", user.name))

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild_id = str(member.guild.id)

        if "welcome" in self.events and guild_id in self.events["welcome"]:
            data = self.events["welcome"][guild_id]
            channel = self.bot.get_channel(data["channel_id"])
            if channel:
                await channel.send(data["message"].replace("{member}", member.mention))


async def setup(bot):
    await bot.add_cog(EventsCog(bot))
    print("EventsCog has been loaded successfully")