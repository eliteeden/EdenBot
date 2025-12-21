import discord
from discord.ext import commands
import random
import asyncio
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

    def set_event(self, event_type, guild_id, channel_id, message):
        formatted_message = "\n".join(message.split("|"))
        self.events.setdefault(event_type, {})
        self.events[event_type][guild_id] = {
            "channel_id": channel_id,
            "message": formatted_message
        }
        self.save_events()

    async def send_formatted_message(self, channel, message, member):
        message = message.replace("{member}", member.mention)
        message = message.replace("{member.name}", member.name)
        message = message.replace("{member.id}", str(member.id))
        await channel.send(message)

    # Event commands

    @commands.command(name="setwelcome", aliases=["sethello", "hellomsg", "welcomemsg"])
    @commands.has_permissions(manage_guild=True)
    async def set_welcome(self, ctx, channel: discord.TextChannel, *, message: str):
        """Sets a welcome message for a specific channel."""
        guild_id = str(ctx.guild.id)
        self.set_event("welcome", guild_id, channel.id, message)
        await ctx.send(f"Welcome message set for {channel.mention}.")

    @commands.command(name="setban")
    @commands.has_permissions(manage_guild=True)
    async def set_ban(self, ctx, channel: discord.TextChannel, *, message: str):
        """Sets a ban message for a specific channel."""
        guild_id = str(ctx.guild.id)
        self.set_event("ban", guild_id, channel.id, message)
        await ctx.send(f"Ban message set for {channel.mention}.")

    @commands.command(name="setleave")
    @commands.has_permissions(manage_guild=True)
    async def set_leave(self, ctx, channel: discord.TextChannel, *, message: str):
        """Sets a leave message for a specific channel."""
        guild_id = str(ctx.guild.id)
        self.set_event("leave", guild_id, channel.id, message)
        await ctx.send(f"Leave message set for {channel.mention}.")

    @commands.command(name="removeevent", aliases=["delevent", "endevent"])
    @commands.has_permissions(manage_guild=True)
    async def remove_event(self, ctx, event_type: str):
        """Removes a configured event message for this server."""
        guild_id = str(ctx.guild.id)
        event_type = event_type.lower()

        if event_type in self.events and guild_id in self.events[event_type]:
            del self.events[event_type][guild_id]
            if not self.events[event_type]:
                del self.events[event_type]
            self.save_events()
            await ctx.send(f"{event_type.capitalize()} message removed for this server.")
        else:
            await ctx.send(f"No {event_type} message found for this server.")

    # Event listeners

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild_id = str(member.guild.id)
        if "welcome" in self.events and guild_id in self.events["welcome"]:
            data = self.events["welcome"][guild_id]
            channel = self.bot.get_channel(data["channel_id"])
            if channel:
                await self.send_formatted_message(channel, data["message"], member)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        guild_id = str(member.guild.id)
        if "leave" in self.events and guild_id in self.events["leave"]:
            data = self.events["leave"][guild_id]
            channel = self.bot.get_channel(data["channel_id"])
            if channel:
                await self.send_formatted_message(channel, data["message"], member)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        guild_id = str(guild.id)
        if "ban" in self.events and guild_id in self.events["ban"]:
            data = self.events["ban"][guild_id]
            channel = self.bot.get_channel(data["channel_id"])
            if channel:
                await self.send_formatted_message(channel, data["message"], user)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        TARGET_MESSAGE = "🎁"
        REQUIRED_ROLE_NAME = "MODERATOR"
        REPLACEMENT_MESSAGE = "🦋"
        # Prevent bot from responding to itself
        if message.author == self.bot.user:
            return

        # Check if the message matches the target
        if message.content.lower() == TARGET_MESSAGE.lower():
            # Check if the author has the required role
            if any(role.name == REQUIRED_ROLE_NAME for role in message.author.roles):
                try:
                    delay = random.randint(1, 8)
                    await asyncio.sleep(delay)
                    await message.delete()
                    await message.channel.send(REPLACEMENT_MESSAGE)
                except discord.Forbidden:
                    print("Missing permissions to delete or send messages.")
                except Exception as e:
                    print(f"An error occurred: {e}")


async def setup(bot):
    await bot.add_cog(EventsCog(bot))
    print("EventsCog has been loaded successfully")