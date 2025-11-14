#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# Imports
import aiohttp
import asyncio
from asyncio import subprocess
import datetime
from dotenv import load_dotenv
import discord
from discord import app_commands, Embed, Guild, Intents, Interaction, Member, User
from discord.ext import commands
import json
import os
import random
import traceback
from typing import Optional, TYPE_CHECKING
import unicodedata

from constants import CHANNELS, GUILDS, ROLES
if TYPE_CHECKING:
    from cogs.inventory import InventoryCog


# Elite bot for a server of bitches

try:
    with open("users.json", encoding="utf-8") as s:
        bank = json.load(s)
except (ValueError, FileNotFoundError):
    bank = {}
    bank["users"] = []


bot = commands.Bot(command_prefix=";", intents=Intents.all())



DISABLED_COMMAND_CHANNEL_ID = CHANNELS.CAPITAL
BLOCK_MESSAGE = f"No commands in <#{CHANNELS.CAPITAL}>\nUse bot commands in <#{CHANNELS.EDEN_BOT_COMMANDS}>, you brat"
EXEMPT_COMMANDS = [
    "purge",
    "ping",
    "botpurge",
    "web",
    "roll",
    "d20",
    "d6",
    "d100",
    "endslow",
    "slowmode",
    "ban",
    "mute",
    "snipe",
    "afk",
    "bing",
    "rank"
]


@bot.check
async def block_commands_in_channel(ctx: commands.Context):
    if not any(
        role.id == ROLES.MODERATOR or role.id == ROLES.TOTALLY_MOD
        for role in ctx.author.roles
    ):
        if ctx.channel.id == DISABLED_COMMAND_CHANNEL_ID:
            if ctx.command.name not in EXEMPT_COMMANDS: # type: ignore
                try:
                    await ctx.send(BLOCK_MESSAGE)
                except discord.Forbidden:
                    pass
                return False  # Block execution
    return True  # Allow execution


@bot.event
async def on_ready():
    try:
        print("starting!")
        # Syncing the bot's command tree with Discord
        await bot.add_cog(ConfessCog(bot))  # Add the ConfessCog to the bot
    except Exception as e:
        print(f"Failed to start confessions: {e}")
    try:
        # Reddit background task got moved to the cog

        print("Slash commands synced successfully!")

        # Load cogs
        for filename in os.listdir("cogs"):
            if filename.endswith(".py"):
                try:
                    await bot.load_extension(f"cogs.{filename[:-3]}")
                    print(f"Loaded cog: {filename[:-3]}")
                except Exception as e:
                    print(f"Failed to load cog {filename[:-3]}: {e}")

        # TODO: this needs to be a command
        await bot.tree.sync()
    except Exception as e:
        print(f"Failed to sync commands: {e}")
    channel: discord.TextChannel = bot.get_channel(CHANNELS.CAPITAL) # type: ignore
    await channel.send("I'm backkkkk")
    print("Systems online")


# Global tracking for repeated messages
global_repeat_counts = {}


BLACKLIST_FILE = "blacklist.json"


# Load blacklist from file
def load_blacklist():
    try:
        with open(BLACKLIST_FILE, "r") as f:
            return json.load(f).get("users", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []


# Save updated blacklist to file
def save_blacklist(users):
    with open(BLACKLIST_FILE, "w") as f:
        json.dump({"users": users}, f, indent=4)


# Check if user is blacklisted
def is_blacklisted(user_id):
    return user_id in load_blacklist()


# Global check
@bot.check
async def block_blacklisted_users(ctx):
    if is_blacklisted(ctx.author.id):
        await ctx.send("Get your disgusting hands off of me, bitch.")
        return False
    return True


# Mod command to blacklist a user
@bot.command()
@commands.has_any_role(ROLES.MODERATOR)
async def blacklist(ctx, user: discord.User):
    users = load_blacklist()
    if user.id in users:
        await ctx.send("🚫 That user is already blacklisted.")
    else:
        users.append(user.id)
        save_blacklist(users)
        await ctx.send(f"✅ {user.name} has been blacklisted.")


# Mod command to blacklist a user
@bot.command()
@commands.has_any_role(ROLES.MODERATOR)
async def whitelist(ctx, user: discord.User):
    try:
        users = load_blacklist()
        if user.id in users:
            users.remove(user.id)
            save_blacklist(users)
            await ctx.send(f"{user.name} has been whitelisted.")
        else:
            await ctx.send(f"✅ {user.name} is already whitelisted.")
    except Exception as e:
        await ctx.send(f"Error: {e}")


# Command error handling
@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    if hasattr(ctx.command, "on_error"):
        return
    if isinstance(error, (commands.MissingAnyRole, commands.MissingRole, commands.MissingPermissions)):     
        await ctx.send("You are missing moderator permissions, you wannabe.")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send(
            "That command doesn't exist stupid. Type `;help` to see available commands."
        )
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Some parameters are missing, Einstein.")
    elif isinstance(error, commands.CommandOnCooldown):
        total_seconds = int(error.retry_after)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        time_parts = []
        if hours > 0:
            time_parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if minutes > 0:
            time_parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
        if seconds > 0 or not time_parts:
            time_parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")

        time_string = ", ".join(time_parts)
        await ctx.send(f"Slow down! Try again in {time_string}.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Invalid argument provided.")
    elif isinstance(error, commands.CommandInvokeError):
        await ctx.send(
            "An error occurred while executing the command. Leave me alone for a bit."
        )
        bot_channel: discord.TextChannel = bot.get_channel(CHANNELS.BOT_LOGS) # type: ignore
        message = "\n".join(
            [
                f"Error in command `{ctx.command}`: {error.original}",
                f"{'-' * 20}",
                "```py",
                f"{traceback.format_exception(error.original)}",
                "```",
            ]
        )
        if len(message) < 2000:
            await bot_channel.send(message)
        else:
            for i in range(0, len(message), 2000):
                await bot_channel.send(message[i : i + 2000])
        print(error)
    else:
        raise error


HUGGINGFACE_API_KEY = "redacted"

swears = [
    "fuck",
    "shit",
    "ass",
    "dick",
    "pussy",
    "hell",
    "asshole",
    "douche",
    "motherfucker",
    "nonce",
    "bitch",
    "cunt",
    "cocksucker",
    "wanker",
    "twat",
    "bellend",
    "bastard",
    "damn",
    "asshat",
    "cum",
    "hubbins",
    "r/teenagers",
]





@bot.command()
@commands.has_any_role("Bonked by Zi")
async def eat(ctx, *, victim):
    await ctx.send(f"{victim} has been eaten")


@eat.error
async def eat_error(ctx, error):
    if isinstance(error, commands.MissingAnyRole):
        await ctx.send(
            "That command doesn't exist, stupid. Use `;help` to look for available commands"
        )


def load_profanity_data():
    try:
        with open("profanities.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


# Save profanity data to a JSON file
def save_profanity_data(profanity_data):
    with open("profanities.json", "w") as file:
        json.dump(profanity_data, file, indent=4)


# Initialize profanity tracking
profanity_data = load_profanity_data()


import asyncio
import time

STICKY_FILE = "sticky_messages.json"
sticky_data = {}
last_update = {}
sticky_queues = {}  # Stores queues per channel
sticky_tasks = {}  # Tracks background tasks per channel


def load_sticky_data():
    if not os.path.exists(STICKY_FILE):
        return {}
    with open(STICKY_FILE, "r") as f:
        return json.load(f)


def save_sticky_data(data):
    with open(STICKY_FILE, "w") as f:
        json.dump(data, f, indent=4)


sticky_data = load_sticky_data()


@bot.command()
@commands.has_any_role(ROLES.MODERATOR)
async def stick(ctx, msg_content: str, *, channel: discord.TextChannel = None): # type: ignore
    try:
        if channel is None:
            channel = ctx.channel

        if str(channel.id) in sticky_data:
            await ctx.send("You already have a sticky message setup.")
            return

        msg = await channel.send(msg_content)

        sticky_data[str(channel.id)] = {
            "guild_id": ctx.guild.id,
            "message_id": msg.id,
            "msg_content": msg_content,
        }
        save_sticky_data(sticky_data)

        # Update last message timestamp
        last_update[str(channel.id)] = time.time()

        await ctx.send("Created sticky message successfully.")

    except Exception as e:
        await ctx.send(f"An error occurred: {e}")


@bot.command()
@commands.has_any_role(ROLES.MODERATOR)
async def unstick(ctx, channel: discord.TextChannel = None): # type: ignore
    try:
        if channel is None:
            channel = ctx.channel
        channel_id = str(channel.id)

        if channel_id not in sticky_data:
            await ctx.send("No sticky message found for this channel.")
            return

        try:
            old_msg = await channel.fetch_message(sticky_data[channel_id]["message_id"])
            await old_msg.delete()
        except discord.NotFound:
            pass

        del sticky_data[channel_id]
        save_sticky_data(sticky_data)

        await ctx.send("Sticky message removed successfully.")

    except Exception as e:
        await ctx.send(f"An error occurred: {e}")


# Load responses from file
def load_responses():
    with open("autoresponses.json", "r") as f:
        return json.load(f)


# Save updated responses
def save_responses(data):
    with open("autoresponses.json", "w") as f:
        json.dump(data, f, indent=4)


@bot.command()
@commands.has_any_role(ROLES.MODERATOR, ROLES.TOTALLY_MOD)
async def responses(ctx: commands.Context):
    await ctx.author.send(
        file=discord.File("autoresponses.json", "ar.json", spoiler=True)
    )


@bot.command()
@commands.has_any_role(ROLES.MODERATOR, ROLES.TOTALLY_MOD)
async def ar(ctx, category: str, trigger: str, *, reply: str = "remove"):
    """
    Sets an auto response
    Usage:
      • ;ar auto hello Hi there!
      • ;ar exact ping pong
      • ;ar auto hello remove   ← Removes 'hello' from AUTO_RESPONSES
    """
    responses = load_responses()
    category_key = "AUTO_RESPONSES" if category.lower() == "auto" else "EXACT_RESPONSES"
    trigger = trigger.lower()

    if reply.lower() == "remove":
        if trigger in responses[category_key]:
            del responses[category_key][trigger]
            save_responses(responses)
            await ctx.send(f"Removed `{trigger}` from {category_key}")
        else:
            await ctx.send(f"`{trigger}` not found in {category_key}")
    else:
        responses[category_key][trigger] = reply
        save_responses(responses)
        await ctx.send(f"Added `{trigger}` to {category_key}")


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    responses = load_responses()

    channel_id = str(message.channel.id)

    await bot.process_commands(message)

    if channel_id in sticky_data:
        if channel_id not in sticky_queues:
            sticky_queues[channel_id] = asyncio.Queue()

        await sticky_queues[channel_id].put(message)  # Add message to queue

        if channel_id not in sticky_tasks or sticky_tasks[channel_id].done():
            sticky_tasks[channel_id] = asyncio.create_task(
                process_sticky_queue(channel_id)
            )

    content = message.content.lower()
    channel_id = message.channel.id

    # Check triggers
    for trigger, response in responses["AUTO_RESPONSES"].items():
        if trigger in content:
            await message.channel.send(response)
            return

    # Check exact matches
    if content in responses["EXACT_RESPONSES"]:
        await message.channel.send(responses["EXACT_RESPONSES"][content])
        return

    # Profanity tracking
    for profanity in swears:
        if profanity in content:
            user_id = str(message.author.name)
            profanity_data[user_id] = profanity_data.get(user_id, 0) + 1
            save_profanity_data(profanity_data)

    # Track repeated messages per channel
    if channel_id not in global_repeat_counts:
        global_repeat_counts[channel_id] = {"last_message": None, "repeat_count": 0}

    if global_repeat_counts[channel_id]["last_message"] == content:
        global_repeat_counts[channel_id]["repeat_count"] += 1
    else:
        if (
            global_repeat_counts[channel_id]["repeat_count"] >= 3
            and content.strip() != ""
        ):
            await message.channel.send(
                f"Broke the chain of {global_repeat_counts[channel_id]['repeat_count']} messages!"
            )
        global_repeat_counts[channel_id]["last_message"] = content
        global_repeat_counts[channel_id]["repeat_count"] = 1


async def process_sticky_queue(channel_id: str):
    """Processes sticky messages periodically instead of immediately."""
    while True:
        if sticky_queues[channel_id].empty():
            await asyncio.sleep(3)  # Sleep a bit before checking again
            continue

        message = await sticky_queues[channel_id].get()

        # Throttle sticky updates (only update every 5 seconds)
        if time.time() - last_update.get(channel_id, 0) < 5:
            await asyncio.sleep(5)

        sticky_info = sticky_data[channel_id]
        channel: discord.TextChannel = await bot.fetch_channel(int(channel_id)) # type: ignore

        try:
            old_msg = await channel.fetch_message(sticky_info["message_id"])
            await old_msg.delete()
        except discord.NotFound:
            pass  # Ignore if message is already deleted

        new_msg = await channel.send(sticky_info["msg_content"])
        sticky_data[channel_id]["message_id"] = new_msg.id
        save_sticky_data(sticky_data)

        last_update[channel_id] = time.time()

        await asyncio.sleep(3)  # Ensures steady processing instead of instant reactions


@bot.event
async def on_member_join(member: User):
    if member.guild.id != GUILDS.ELITE_EDEN: # type: ignore
        return
    channel: discord.TextChannel = bot.get_channel(CHANNELS.CAPITAL) # type: ignore
    await channel.send(
        f"Welcome to Elite Eden {member.mention} \n<@&{ROLES.WELCOME_PING}> say hello to our new member!"
    )


@bot.event
async def on_member_remove(member: User):
    if member.guild.id != GUILDS.ELITE_EDEN: # type: ignore
        return
    try:
        await member.guild.fetch_ban(member) # type: ignore # Check if the member was banned
        return  # Exit the function if they were banned
        # Can't on_member_ban just go here?
    except discord.NotFound:
        print(f"{member} left the server (not banned)")
        channel: discord.TextChannel = bot.get_channel(CHANNELS.CAPITAL) # type: ignore
        await channel.send(
            f"{member.mention} ({member.name}) just left Elite Eden like a pussy."
        )


@bot.event
async def on_member_ban(guild: Guild, member: User):
    if guild.id != GUILDS.ELITE_EDEN: # type: ignore
        return
    channel: discord.TextChannel = bot.get_channel(CHANNELS.CAPITAL) # type: ignore
    await channel.send(f"Good riddance to {member.mention} ({member.name}).")


@bot.command()
async def profanity(ctx: commands.Context, member: Member = None): # type: ignore
    if member is None:
        member: Member = ctx.author  # Default to command user if no member specified

    user_id = str(member.name)
    profanity_data = load_profanity_data()  # Load stored data

    count = profanity_data.get(user_id, 0)
    await ctx.send(f"{member.mention} has used {count} profane words.")


@bot.command()
async def profanities(ctx):
    """Displays the top 100 users with the most profanity usage using pagination"""
    profanity_data = load_profanity_data()  # Load stored data

    # Sort users by profanity count (highest first)
    sorted_users = sorted(profanity_data.items(), key=lambda x: x[1], reverse=True)

    # Limit to top 100
    top_users = sorted_users[:100]

    paginator = bot.cogs["PaginatorCog"]() # type: ignore # Initialize paginator

    # Create paginated embeds
    for i in range(0, len(top_users), 10):  # Show 10 users per page
        embed = discord.Embed(title="Profanity Leaderboard", color=discord.Color.red())
        for idx, (user_id, count) in enumerate(top_users[i : i + 10], start=i + 1):
            embed.add_field(
                name=f"{idx}. {user_id}", value=f"{count} profane words", inline=False
            )

        paginator.add_page(embed)

    await paginator.send(ctx)  # Send paginated leaderboard


# commands
@bot.command()
async def ping(ctx):
    # the first ever command
    await ctx.send("Pong")


@bot.command()
async def changelog(ctx):
    try:
        with open("eden bot changelog.txt", "r", encoding="utf-8") as file:
            lines = file.readlines()

        chunks = []
        current_chunk = ""

        for line in lines:
            # If adding this line would push us over Discord's 2000-char limit…
            if (
                len(current_chunk) + len(line) + 7 > 2000
            ):  # 7 accounts for code block syntax
                chunks.append(current_chunk)
                current_chunk = ""
            current_chunk += line

        if current_chunk:
            chunks.append(current_chunk)

        for i, chunk in enumerate(chunks):
            await ctx.send(f"```txt\n{chunk}\n```")

    except FileNotFoundError:
        await ctx.send(
            "File not found. Please check the path: `eden bot changelog.txt`."
        )
    except Exception as e:
        await ctx.send(f"Error: `{e}`")


@bot.command()
async def longday(ctx):
    await ctx.send(
        "Its been a long day \n"
        "Without you my friend \n"
        "And I will tell you all about it when i see you again \n"
    )




# List of banned words (case-insensitive)
slur_words = {
    "retard",
    "fag",
    "faggot",
    "nigga",
    "*tard",
    "nigger",
    "tard",
    "dyke",
    "mentally ill",
}


@bot.tree.command(name="talk")
@app_commands.checks.has_any_role(
    ROLES.MODERATOR, ROLES.TOTALLY_MOD, ROLES.TALK_PERMS, "Fden Bot Perms", "happy"
)
async def talk(interaction: Interaction, message: str, channel: Optional[discord.TextChannel] = None): # type: ignore
    # Check for the item or the role
    allowed_roles = [ROLES.MODERATOR, ROLES.TOTALLY_MOD]  # ROLES.TALK_PERMS]
    has_role = any(role.id in allowed_roles for role in interaction.user.roles) # type: ignore
    inventory: InventoryCog = bot.get_cog("InventoryCog") # type: ignore
    if (
        has_role or interaction.guild_id != GUILDS.ELITE_EDEN
    ):  # or inventory.has_item(interaction.user, "Talk Command Permissions"):
        pass
    else:
        await interaction.response.send_message(
            "You do not have permission to use this command.\nGo check out the `;shop`.",
            ephemeral=True,
        )
        return

    await interaction.response.defer(ephemeral=True)
    if channel is None:
        channel: discord.TextChannel = interaction.channel # type: ignore
    if (not channel.permissions_for(interaction.user).send_messages) and (not has_role): # type: ignore
        await interaction.response.send_message(
            "You do not have permission to send messages in that channel.",
            ephemeral=True,
        )

    # Check for bad words
    lowered = message.lower()
    flagged = any(bad_word in lowered for bad_word in slur_words)
    blocked = False

    # If flagged, notify a specific channel
    alert_channel: discord.TextChannel = bot.get_channel(CHANNELS.STRIKES) # type: ignore
    if flagged and channel.guild.id == alert_channel.guild.id:
        blocked = True
        # The ID of the channel where alerts should be sent
        if alert_channel:
            await alert_channel.send(
                f"🚨 Message from {interaction.user.mention} in {interaction.channel.mention if isinstance(interaction.channel, discord.TextChannel) else f'(non-text-channel id: {interaction.channel_id})'} "
                f"contained flagged content: ```{message}```"
            )

    # Send the original message to the current channel
    try:
        if not blocked:
            await channel.send(message) # type: ignore
    except Exception as e:
        if isinstance(e, discord.Forbidden):
            await interaction.response.send_message(
                "I don't have permission to send messages in this channel.",
                ephemeral=True,
            )
            return
        await interaction.response.send_message(
            f"Error sending message: {e}", ephemeral=True
        )

    # Clean up original interaction
    await interaction.delete_original_response()


@bot.tree.command(name="embed")
@app_commands.describe(
    title="The title of the embed",
    message="The description of the embed, separate lines with '|'",
    color="The hexadecimal color code for the embed",
)
async def embed(
    interaction: Interaction,
    title: str,
    message: str,
    color: str = "#5865F2",  # Discord blurple hex
):
    """Create an embed with a title, description, and color."""
    try:
        # Format the message into separate lines
        formatted_message = "\n".join(message.split("|"))

        # Convert hex string to integer color
        color = color.lstrip("#")
        color_int = int(color, 16)

        # Create the embed
        embed = Embed(title=title, description=formatted_message, color=color_int)

        # Check user roles
        allowed_role_ids = [ROLES.MODERATOR, ROLES.TOTALLY_MOD]
        has_role = any(role.id in allowed_role_ids for role in interaction.user.roles)

        allowed_role_ids = [ROLES.MODERATOR, ROLES.TOTALLY_MOD]
        user_roles = [role.id for role in interaction.user.roles]
        has_role = any(role_id in allowed_role_ids for role_id in user_roles)

        # Fallback check: inventory item presence
        has_permission = has_role

        # Set footer only if user lacks required permissions
        if not has_permission:
            avatar_url = (
                interaction.user.avatar.url if interaction.user.avatar else None
            )
            embed.set_footer(
                text=f"Requested by {interaction.user.name}", icon_url=avatar_url
            )

        # Defer the response (ephemeral)
        await interaction.response.defer(ephemeral=True)

        # Send the embed to the channel
        await interaction.channel.send(embed=embed)

        # Clean up the original interaction message if needed
        await interaction.delete_original_response()

    except ValueError:
        await interaction.response.send_message(
            "Invalid color code. Please provide a valid hexadecimal value like #FF5733.",
            ephemeral=True,
        )


user_colors = {}  # Dictionary to store user-specific colors


def load_colors():
    if not os.path.exists("user_colors.json"):
        return {}  # Return an empty dictionary if the file doesn't exist

    try:
        with open("user_colors.json", "r") as file:
            data = json.load(file)
            return data if isinstance(data, dict) else {}  # Ensure it's a dictionary
    except json.JSONDecodeError:
        return {}  # Return an empty dictionary if JSON is invalid


# Save updated user colors to JSON
def save_colors(data):
    with open("user_colors.json", "w") as file:
        json.dump(data, file, indent=4)


# Generate a random hex color
def generate_hex_color():
    return f"#{random.randint(0, 0xFFFFFF):06x}"


user_colors = load_colors()  # Load colors at startup


class ConfessCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="confess", description="Send an anonymous confession")
    async def confess(
        self, interaction: discord.Interaction, message: str, image: str = ""
    ):
        user_name = str(
            interaction.user.name
        )  # Convert username to string for JSON compatibility

        if user_name not in user_colors:
            user_colors[user_name] = generate_hex_color()
            save_colors(user_colors)  # Save the updated data

        hex_code: str = user_colors[user_name]
        embed = discord.Embed(
            title=f"Anon-{hex_code.removeprefix('#')}".capitalize(),
            description=message,
            color=int(hex_code[1:], 16),
        )

        if image != "":
            embed.set_image(url=image)

        await interaction.response.defer(
            ephemeral=True
        )  # Prevents errors by deferring the interaction
        await interaction.channel.send(embed=embed) # type: ignore # Sends the embed without replying to the trigger
        await interaction.delete_original_response()

    @commands.command(name="resetconfessions")
    @commands.has_any_role(ROLES.TOTALLY_MOD, ROLES.MODERATOR)
    async def reset_confessions(self, ctx: commands.Context):
        """Reset everyone's colors."""
        global user_colors
        user_colors = {}
        save_colors(user_colors)  # Save the reset data
        await ctx.send("All user colors have been reset.")

    async def cog_load(self):
        try:
            self.bot.tree.add_command(ConfessCog(bot).confess)
        finally:
            return await super().cog_load()


def is_unusual_name(name):
    """Checks if a name contains non-standard characters or excessive symbols."""
    if name is None:
        return False

    normalized_name = unicodedata.normalize(
        "NFKD", name
    )  # Normalize Unicode characters
    standard_chars = set(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "
    )

    return any(char not in standard_chars for char in normalized_name)


@bot.command()
@commands.has_any_role(ROLES.MODERATOR)
async def rfs(ctx):
    author = ctx.author
    try:
        """Resets usernames of members whose names exceed the given length."""

        for member in ctx.guild.members:
            if member.nick and is_unusual_name(
                member.nick
            ):  # Check if nickname is unusual
                if author.top_role.position > member.top_role.position:
                    try:
                        await member.edit(nick=None)
                        await ctx.author.send(
                            f"Reset {member.display_name}'s nickname to their default."
                        )
                    except discord.Forbidden:
                        await ctx.author.send(
                            f"Failed to reset {member.display_name}'s nickname (insufficient permissions)."
                        )
                    except discord.HTTPException:
                        await ctx.author.send(
                            f"An error occurred while resetting {member.display_name}'s nickname."
                        )

    except Exception as e:
        await ctx.send(f"Error: {e}")


# Event commands


command_tracked_messages = {}


message_role_mapping = {}


@bot.command()
@commands.has_any_role("MODERATOR")
async def districtclaim(ctx, category_id: int):
    # Find the category
    category = discord.utils.get(ctx.guild.categories, id=category_id)
    if not category:
        await ctx.send("Category not found. Please provide a valid category ID.")
        return

    # Get text channels within the category
    text_channels = category.text_channels

    # List of channel IDs to exclude
    excluded_channels = [
        CHANNELS.VIP_LOUNGE,
        CHANNELS.HONEYMOON,
        CHANNELS.DISTRICT_SOUTH,
        CHANNELS.DISTRICT_EAST,
        CHANNELS.DISTRICT_WEST,
        CHANNELS.DISTRICT_NORTH,
    ]  # Replace with actual IDs of channels to skip

    # Filter out excluded channels
    valid_channels = [
        channel for channel in text_channels if channel.id not in excluded_channels
    ]

    if len(valid_channels) < 4:
        await ctx.send(
            "Not enough valid channels in this category to send unique messages!"
        )
        return

    # Randomly select 4 unique channels
    random_channels = random.sample(valid_channels, 4)

    # Define 4 unique messages and assign specific roles to them using role IDs
    messages = ["South: 🌴", "East: 🌾", "West: 🍁", "North: 🌲"]
    role_ids = [
        ROLES.DISTRICT_SOUTH,
        ROLES.DISTRICT_EAST,
        ROLES.DISTRICT_WEST,
        ROLES.DISTRICT_NORTH,
    ]  # Replace with actual role IDs

    # Send messages and map them to roles
    for channel, message, role_id in zip(random_channels, messages, role_ids):
        sent_message = await channel.send(message)
        message_role_mapping[sent_message.id] = (
            role_id  # Map message ID to its unique role ID
        )

    await ctx.send("Messages sent! Reply with 'claimed' to these messages to interact.")

    try:
        while message_role_mapping:  # Continue until all messages are claimed
            # Wait for a valid reply
            reply = await bot.wait_for(
                "message",
                timeout=60.0,
                check=lambda r: (
                    r.reference and r.reference.message_id in message_role_mapping
                ),
            )

            if "claimed" in reply.content.lower():  # Check for the keyword 'claimed'
                assigned_role_id = message_role_mapping[reply.reference.message_id]
                member_role_ids = [role.id for role in reply.author.roles]

                if assigned_role_id in member_role_ids:
                    await reply.channel.send(
                        f"{reply.author.mention} successfully claimed the message!"
                    )
                    del message_role_mapping[
                        reply.reference.message_id
                    ]  # Remove the claimed message

                    # Check if all messages have been claimed
                    if not message_role_mapping:  # Dictionary is empty
                        await ctx.send(
                            "All messages have been claimed! Great job, everyone! 🎉"
                        )
                        break
                else:
                    await reply.channel.send(f"{reply.author.mention}, Wrong district!")
            else:
                await reply.channel.send(
                    f"{reply.author.mention}, *try again... and maybe read the instructions this time?* 🙄"
                )
    except asyncio.TimeoutError:
        # Stop listening after timeout if no reply occurs
        await ctx.send(
            "No replies detected for remaining messages within the timeout period."
        )


# Cog commands
@commands.has_any_role(ROLES.TOTALLY_MOD, "happy")
@bot.command()
async def cogs(ctx: commands.Context):
    await ctx.send("Loaded cogs: `" + "`, `".join(bot.cogs.keys()) + "`")
    # List available cogs in the cogs directory
    cogs = os.listdir("cogs")
    send_cogs = []
    for cog in cogs:
        if cog.endswith(".py"):
            cog_name = cog[:-3]
            send_cogs.append(cog_name)
    await ctx.send("Available cogs: `" + "`, `".join(send_cogs) + "`")


@cogs.error
async def cogs_error(ctx: commands.Context, error: commands.CommandError):
    if isinstance(error, commands.MissingAnyRole):
        await ctx.send("Trust me, you can't untangle the spaghetti inside.")
    else:
        await ctx.send(f"An unexpected error occurred: {error}")


@bot.command()
@commands.has_any_role(ROLES.TOTALLY_MOD, "happy")
async def reload(ctx: commands.Context, cog: str):
    """Reloads a specific cog."""
    try:
        await bot.reload_extension(f"cogs.{cog}")
        await ctx.send(f"{cog} cog reloaded successfully!")
    except Exception as e:
        await ctx.send(f"Failed to reload {cog} cog: {e}")
        print(e)


@reload.error
async def reload_error(ctx: commands.Context, error: commands.CommandError):
    """Handles errors for the reload command."""
    if isinstance(error, commands.MissingAnyRole):
        await ctx.send(
            "buzz off butterfingers, only an elite few can tinker with me like that"
        )
    elif isinstance(error, commands.ExtensionNotFound):
        await ctx.send("The specified cog does not exist.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("What do you want me to do, reload *everything*?")
    else:
        await ctx.send(f"An unexpected error occurred: {error}")


@bot.command()
@commands.has_any_role(ROLES.TOTALLY_MOD, "happy")
async def load(ctx: commands.Context, cog: str):
    """Loads a specific cog."""
    try:
        await bot.load_extension(f"cogs.{cog}")
        await ctx.send(f"{cog} cog loaded successfully!")
    except Exception as e:
        await ctx.send(f"Failed to load {cog} cog: {e}")
        print(e)


@load.error
async def load_error(ctx: commands.Context, error: commands.CommandError):
    """Handles errors for the load command."""
    if isinstance(error, commands.MissingAnyRole):
        await ctx.send("what do you even mean to do with that command, filthy peasant?")
    elif isinstance(error, commands.ExtensionNotFound):
        await ctx.send("The specified cog does not exist.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("What even is there to load?")
    else:
        await ctx.send(f"An unexpected error occurred: {error}")


# Main commands


@bot.command()
@commands.has_any_role(ROLES.TOTALLY_MOD)
async def nohup(ctx):
    try:
        with open("nohup.out", "r") as f:
            await ctx.author.send(f.read()[-1999:])
    except Exception as e:
        await ctx.send(f"Error: {e}")


@bot.command()
@commands.has_any_role(ROLES.TOTALLY_MOD, "happy")
async def pull(ctx: commands.Context):
    """Fetches the latest changes from git."""
    try:
        # Run the git pull command
        result = await subprocess.create_subprocess_shell(
            "git pull", stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        stdout, stderr = await result.communicate()
        if stdout:
            print(stdout.decode())
        if stderr:
            print(stderr.decode())
        if result.returncode == 0:
            await ctx.send("Successfully pulled the latest changes from git.")
            await ctx.author.send("Git pull output:\n" + stdout.decode())
        else:
            await ctx.send(f"Failed to pull changes: {stderr.decode()}")
    except Exception as e:
        await ctx.send(f"An error occurred while pulling changes: {e}")


@pull.error
async def pull_error(ctx: commands.Context, error: commands.CommandError):
    """Handles errors for the pull command."""
    if isinstance(error, commands.MissingAnyRole):
        await ctx.send(
            "Where are you trying to pull from, the depths of hell? Only the elite can do that."
        )
    else:
        await ctx.send(f"An unexpected error occurred: {error}")


# This was mostly created by Happy!
load_dotenv()

token = os.environ.get("TOKEN")
if not token:
    token = input("Bot token not found. Please enter your token:\n> ")

bot.run(token)
