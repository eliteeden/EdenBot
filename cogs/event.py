import re
from typing import Literal, Optional
import discord
from discord.ext import commands
import random
import asyncio
import json
import os

from constants import ROLES

CONFIG_FILE = "events.json"
AR_FILE = "autoresponses.json"

class EventsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.events = self.load_events()
        self.last_target_message_id = None
        self.load_ar()

    def load_ar(self):
        r: dict[str, dict[str, str]] = {}
        with open(AR_FILE, "r") as f:
            r = json.load(f)
        self.responses.exact = r.get("exact", {})
        self.responses.line = r.get("line", {})
        self.responses.word = r.get("word", {})
        self.responses.auto = r.get("auto", {})
    def save_ar(self):
        with open(AR_FILE, "w") as f:
            json.dump({
                "exact": self.responses.exact,
                "line": self.responses.line,
                "word": self.responses.word,
                "auto": self.responses.auto,
            }, f, indent=4)

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
    async def on_message(self, message: discord.Message):
        # Claimed
        TARGET_MESSAGE = "🎁"
        ROLE_ID = ROLES.MODERATOR
        REPLACEMENT_MESSAGE = "🦋"
        REACTION_EMOJI = "🥳"  
        REPLY_TRIGGER = "claimed"

        # Prevent bot from responding to itself
        if message.author == self.bot.user:
            return

        # Check if the message matches the target
        if message.content.lower() == TARGET_MESSAGE.lower():
            if isinstance(message.author, discord.Member) and any(role.id == ROLE_ID for role in message.author.roles):
                self.last_target_message_id = message.id  # Save the target message ID
                delay = random.randint(2, 16)
                await asyncio.sleep(delay)
                await message.delete()
                await message.channel.send(REPLACEMENT_MESSAGE)
        elif (
            message.reference
            and message.reference.message_id == self.last_target_message_id
            and message.content.strip().lower() == REPLY_TRIGGER
        ):
            await message.add_reaction(REACTION_EMOJI)
            await asyncio.sleep(20)

        # Auto Responses
        msg: str = message.content
        # Exact is handled seperately
        if (response:= self.ar_value(msg)):
            await message.channel.send(response)

    # This should be called publicly (main.py)
    def ar_value(self, msg: Optional[str]) -> Optional[str]:
        """
        Returns the auto response that matches the given message, if any.
        
        Args:
            msg (Optional[str]): The message to check.
        Returns:
            Optional[str]: The auto response that matches the given message, or None if no match is found.
        """
        if msg is None:
            return None
        for k, v in self.responses.exact.items():
            if msg.lower() == k.lower():
                return v
        for response_type in ["line", "word", "auto"]:
            for k, v in self.responses()(response_type).items():
                pattern = {
                    "line": "^{}$",
                    "word": r"(^|\W){}($|\W)",
                    "auto": "{}"
                }[response_type].format(re.escape(k))
                if re.search(pattern, msg, re.IGNORECASE | re.MULTILINE | re.DOTALL): # /gmi
                    return v
        return None

    @commands.command(aliases=["autoresponse", "auto", "exactresponse", "maketheedenbotsaysomethingstupidsometimes"])
    @commands.has_any_role(ROLES.MODERATOR, ROLES.TOTALLY_MOD)
    async def ar(self, ctx: commands.Context, category: str, trigger: str, *, reply: str = ""):
        """
        Sets an auto response
        Usage:
        • ;ar auto hello Hi there!
        • ;ar exact ping pong
        • ;ar auto hello   ← Removes 'hello' from AUTO_RESPONSES
        The categories are:
        • exact - Matches the entire message exactly
        • line  - Matches entire lines in a multi-line message (same as exact for single-line messages)
        • word  - Matches whole words in the message
        • auto  - Matches anywhere in the message
        Categories are checked in the order: exact, line, word, auto.
        If the reply is empty, the auto response for the given trigger will be removed.
        """
        if category not in ["exact", "line", "word", "auto"]:
            # Shift the arguments if category is actually the trigger
            reply = trigger + reply
            trigger = category
            category = "auto"
        record = self.responses()(category)
        trigger_lower = trigger.lower()
        if reply.lower() == "":
            if trigger_lower in record:
                del record[trigger_lower]
                self.save_ar()
                await ctx.send(f"Removed auto response for '{trigger}' in category '{category}'.")
            else:
                await ctx.send(f"No auto response found for '{trigger}' in category '{category}'.")
        else:
            record[trigger_lower] = reply
            self.save_ar()
            await ctx.send(f"Set auto response for '{trigger}' in category '{category}'.")

    # AR shenanigans
    class responses:
        type record = dict[str, str]
        exact: record = {}
        line: record = {}
        word: record = {}
        auto: record = {}
        def __call__(self, name: str) -> record:
            return self.__getattribute__(name)

        

async def setup(bot):
    await bot.add_cog(EventsCog(bot))
    print("EventsCog has been loaded successfully")

async def teardown(bot: commands.Bot):
    EC: EventsCog = bot.get_cog("EventsCog") # type: ignore
    if EC:
        # Save autoresponses
        EC.save_ar()
        # Save events
        EC.save_events()
        print("EventsCog has been unloaded successfully")
