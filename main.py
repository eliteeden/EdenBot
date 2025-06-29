#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# Imports
from dotenv import load_dotenv
import json
from typing import Optional
from discord import Interaction
import requests
import datetime
import discord
from discord.ext import commands
from discord import Intents, Embed, User, Member, app_commands
import os
import random
import aiohttp
import asyncio
import unicodedata
from googlesearch import search
import webcolors
from constants import CHANNELS, ROLES, USERS

# Initialize the report dictionary
if os.path.exists("reports.json"):
    # Load the report from the file
    with open("reports.json", "r") as f:
        report = json.load(f)
else:
    # Create a new report if the file doesn't exist
    report = {
        "users": [],
        "next_warn_id": 1  # Start with warning ID 1
    }



try:
    with open('users.json', encoding='utf-8') as s:
        bank = json.load(s)
except (ValueError, FileNotFoundError):
    bank = {}
    bank['users'] = []


bot = commands.Bot(command_prefix=';', intents=Intents.all())


class Paginator:
    def __init__(self, bot):
        self.bot = bot
        self.pages = []

    def add_page(self, embed):
        self.pages.append(embed)

    async def send(self, ctx):
        current_page = 0
        message = await ctx.send(embed=self.pages[current_page])

        await message.add_reaction("◀️")
        await message.add_reaction("▶️")

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["◀️", "▶️"]

        while True:
            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)

                if str(reaction.emoji) == "▶️" and current_page < len(self.pages) - 1:
                    current_page += 1
                    await message.edit(embed=self.pages[current_page])
                    await message.remove_reaction(reaction, user)

                elif str(reaction.emoji) == "◀️" and current_page > 0:
                    current_page -= 1
                    await message.edit(embed=self.pages[current_page])
                    await message.remove_reaction(reaction, user)

            except asyncio.TimeoutError:
                break

SUBREDDITS = ["EliteEden", "memes"]  # Add more subreddits as needed
LAST_POST_IDS = {subreddit: None for subreddit in SUBREDDITS}  # Track last post ID per subreddit

async def check_subreddits():
    """Background task to monitor multiple subreddits for new posts."""
    global LAST_POST_IDS
    await bot.wait_until_ready()  # Ensure bot is ready

    while not bot.is_closed():
        for subreddit in SUBREDDITS:
            url = f"https://www.reddit.com/r/{subreddit}/new.json?limit=5"
            headers = {"User-Agent": "Mozilla/5.0"}

            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                posts = data["data"]["children"]

                if posts:
                    latest_post = posts[0]["data"]
                    post_id = latest_post["id"]

                    if LAST_POST_IDS[subreddit] is None:
                        LAST_POST_IDS[subreddit] = post_id  # Initialize on first run
                    elif LAST_POST_IDS[subreddit] != post_id:
                        LAST_POST_IDS[subreddit] = post_id
                        channel: discord.TextChannel = bot.get_channel(CHANNELS.REDDIT)  # type: ignore
                        post_embed = Embed(title=latest_post["title"])
                        post_embed.set_image(url=latest_post["url"])
                        await channel.send(f"New post detected in r/{subreddit}: ")
                        await channel.send(embed=post_embed)

        await asyncio.sleep(60)  # Wait 1 minute before checking again

@bot.event
async def on_ready():
    try:
        # Syncing the bot's command tree with Discord
        bot.tree.add_command(ConfessCog(bot).confess)
        bot.loop.create_task(check_subreddits())  # Start monitoring subreddit
        
        await bot.tree.sync()
        
        print("Slash commands synced successfully!")

        # Load cogs
        for filename in os.listdir("cogs"):
            if filename.endswith(".py"):
                try:
                    await bot.load_extension(f"cogs.{filename[:-3]}")
                    print(f"Loaded cog: {filename[:-3]}")
                except Exception as e:
                    print(f"Failed to load cog {filename[:-3]}: {e}")
    except Exception as e:
        print(f"Failed to sync commands: {e}")
    

    print('Systems online')

# Global tracking for repeated messages
global_repeat_counts = {}


# Command error handling
@bot.event
async def on_command_error(ctx, error):
    if hasattr(ctx.command, "on_error"):
        return
    if isinstance(error, commands.MissingAnyRole):
        await ctx.send("You are missing moderator permissions, you wannabe.")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send("That command doesn't exist stupid. Type `;help` to see available commands.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Some parameters are missing, Einstein.")
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"Slow down! Try again in {round(error.retry_after, 2)} seconds.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Invalid argument provided.")
    elif isinstance(error, commands.CommandInvokeError):
        await ctx.send("An error occurred while executing the command. Leave me alone for a bit.")
    else:
        raise error

# Autoresponse triggers and responses
AUTO_RESPONSES = {
    "might seem crazy": """Sunshine, she's here you can take a break
I'm a hot balloon that could go to space
With the air, like I don't care, baby, by the way huh
(Because I'm happy) clap along if you feel like a room without a roof
(Because I'm happy) clap along if you feel like happiness is the truth
(Because I'm happy) clap along if you know what happiness is to you
(Because I'm happy) clap along if you feel like that's what you wanna do""",
    "crash out": "Please be respectful in this channel.",
    "make me mod": "Unfortunately, we are not accepting mod applications at this time.",
    "ty eden bot": "You're welcome! <3",
    "arch btw": "bal",
    "linux user": "They'll tell you before you even ask.",
    "1984": "You should have never been given rights imo",
    "say bye to eden bot": "Later guys <3",
    "estrogen": "tmi",
    "absolute cinema": "https://tenor.com/view/me-atrapaste-es-cine-its-cinema-cinema-esto-es-cine-gif-12869046600151364058",
  
    "weird edener": "https://tenor.com/view/do-you-have-any-idea-how-little-that-narrows-it-down-that-narrows-it-down-clear-now-its-clear-now-i-understand-now-gif-21256627"

}

EXACT_RESPONSES = {
    "boost": """︶꒷꒦︶ ๋࣭ ⭑︶꒷꒦︶ ๋࣭ ⭑︶꒷꒦︶ ๋࣭ ⭑︶꒷꒦︶ ๋࣭ ⭑︶꒷꒦︶ ๋࣭┊Booster Benefits !
│╭────────────╯
││• ➛ **Own Custom Role**
││• ➛ **Access to VIP lounge + Vc**
││• ➛ **Custom Emojis**
││• ➛ **Event Priority**
││• ➛ **Nickname Perms**
││• ➛ **Booster Role That Displays above Online Members**
│╰─────────── ·﻿ ﻿ ﻿· ﻿ ·﻿ ﻿ ﻿· ﻿・✦ 
・┆✦ʚ♡ɞ✦ ┆・・┆✦ʚ♡ɞ✦ ┆・""",
    "zi": "literally the best member ever",
    "deadpool": "Shut the fuck up, Wade",
    "vicky": """I hoeee
    -Vicky 2025""",
    ":3": """:0 (=======8
    :0===8
    :0=8
    :3"""
}

HUGGINGFACE_API_KEY = "redacted"

swears = ["fuck", "shit", "ass", "dick", "pussy", "hell", "asshole", "douche", "motherfucker", "nonce", "bitch", "cunt", "cocksucker", "wanker", "twat", "bellend", "bastard", "damn", "asshat"]

@bot.command(aliases=["l", "lyric"])
async def lyrics(ctx, *, query: str):
    """Fetch song lyrics using the Lyrics.ovh API (format: Song - Artist)"""
    try:
        async with ctx.typing():
            if "-" not in query:
                return await ctx.send("Please use the format: `Song Title - Artist`")
            title, artist = map(str.strip, query.split("-", 1))

            async with aiohttp.ClientSession() as session:
                url = f"https://api.lyrics.ovh/v1/{artist}/{title}"
                async with session.get(url) as response:
                    if response.status != 200:
                        return await ctx.send(f"Error: Could not fetch lyrics. Status {response.status}")

                    data = await response.json()
                    lyrics_text = data.get("lyrics", None)
                    if not lyrics_text:
                        return await ctx.send("Lyrics not found.")

                    # Clean up formatting
                    lyrics_text = lyrics_text.replace("\n\n", "\n")  # Reduce excess breaks

                    # Split into chunks of 1024 characters
                    chunks = [lyrics_text[i:i+1024] for i in range(0, len(lyrics_text), 1024)]

                    for i, chunk in enumerate(chunks):
                        embed = discord.Embed(
                            title=f"{title} - {artist}" if i == 0 else f"{title} - {artist} (Part {i+1})",
                            description=chunk,
                            color=discord.Color.blurple()
                        )
                        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"An error occurred: `{e}`")
@bot.command()
@commands.has_any_role("Bonked by Zi")
async def eat(ctx, *, victim):
    await ctx.send(f"{victim} has been eaten")

@eat.error
async def eat_error(ctx, error):
    if isinstance(error, commands.MissingAnyRole):
        await ctx.send("That command doesn't exist, stupid. Use `;help` to look for available commands")

@bot.command()
async def meme(ctx, subreddit: str = "memes"):
    """Fetches a random image from the specified subreddit using Reddit's JSON API."""
    try:
        async with ctx.typing():
            url = f"https://www.reddit.com/r/{subreddit}/new.json?limit=120"
            headers = {"User-Agent": "Mozilla/5.0"}
            
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                posts = [post["data"]["url"] for post in data["data"]["children"] if post["data"]["url"].endswith(("jpg", "png", "gif"))]
                embed = Embed(title="Here's your meme!", color=discord.colour.Color.orange())
                if posts:
                    random.shuffle(posts)
                
                chosen_post = random.choice(posts)
                embed.set_image(url=chosen_post)
                
                if posts:
                    await ctx.send(embed=embed)
                else:
                    await ctx.send("No images found in this subreddit.")
            else:
                await ctx.send(f"Error fetching data: {response.status_code}")
    except Exception as e:
        await ctx.send(f"Error: {e}")





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
async def stick(ctx, msg_content: str, *, channel: discord.TextChannel = None):
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
            "msg_content": msg_content
        }
        save_sticky_data(sticky_data)

        # Update last message timestamp
        last_update[str(channel.id)] = time.time()

        await ctx.send("Created sticky message successfully.")
    
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")

@bot.command()
@commands.has_any_role(ROLES.MODERATOR)
async def unstick(ctx, channel: discord.TextChannel = None):
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


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    channel_id = str(message.channel.id)

    await bot.process_commands(message)

    if channel_id in sticky_data:
        if channel_id not in sticky_queues:
            sticky_queues[channel_id] = asyncio.Queue()

        await sticky_queues[channel_id].put(message)  # Add message to queue

        if channel_id not in sticky_tasks or sticky_tasks[channel_id].done():
            sticky_tasks[channel_id] = asyncio.create_task(process_sticky_queue(channel_id))


    content = message.content.lower()
    channel_id = message.channel.id

    # Auto-response system
    for trigger, response in AUTO_RESPONSES.items():
        if trigger in content:
            await message.channel.send(response)
            return

    if content in EXACT_RESPONSES:
        await message.channel.send(EXACT_RESPONSES[content])
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
        if global_repeat_counts[channel_id]["repeat_count"] >= 3:
            await message.channel.send(
                f"Broke the chain of {global_repeat_counts[channel_id]['repeat_count']} messages!"
            )
        global_repeat_counts[channel_id]["last_message"] = content
        global_repeat_counts[channel_id]["repeat_count"] = 1

async def process_sticky_queue(channel_id):
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
        channel = await bot.fetch_channel(int(channel_id))

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
    channel: discord.TextChannel = bot.get_channel(CHANNELS.CAPITAL)  # type: ignore
    await channel.send(f'Welcome to Elite Eden {member.mention} \n<@&{ROLES.WELCOME_PING}> say hello to our new member!')

@bot.event
async def on_member_remove(member: User):
    try:
        await member.guild.fetch_ban(member)  # type: ignore # Check if the member was banned
        return  # Exit the function if they were banned
        # Can't on_member_ban just go here?
    except discord.NotFound:
        print(f"{member} left the server (not banned)")
        channel: discord.TextChannel = bot.get_channel(CHANNELS.CAPITAL) # type: ignore
        await channel.send(f'{member.mention} just left Elite Eden like a pussy.')

       

@bot.event
async def on_member_ban(guild, member: User):
    channel: discord.TextChannel = bot.get_channel(CHANNELS.CAPITAL) # type: ignore
    await channel.send(f'Good riddance to {member.mention}.')    


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

    paginator = Paginator(bot=bot)  # Initialize paginator

    # Create paginated embeds
    for i in range(0, len(top_users), 10):  # Show 10 users per page
        embed = discord.Embed(title="Profanity Leaderboard", color=discord.Color.red())
        for idx, (user_id, count) in enumerate(top_users[i:i+10], start=i+1):
            embed.add_field(name=f"{idx}. {user_id}", value=f"{count} profane words", inline=False)

        paginator.add_page(embed)

    await paginator.send(ctx)  # Send paginated leaderboard

# commands
@bot.command()
async def ping(ctx):
    await ctx.send('Pong')

@bot.command()
async def changelog(ctx):
      # Update with the correct path

    try:
        with open("eden bot changelog.txt", "r", encoding="utf-8") as file:
            content = file.read()
            
        if len(content) > 2000:
            await ctx.send("The file is too long to send as a message.")
        else:
            await ctx.send(f"```\n{content}\n```")  # Sends it in a code block for formatting
    except FileNotFoundError:
        await ctx.send("File not found. Please check the path.")
    except Exception as e:
        await ctx.send(f"Error: {e}")




@bot.command()
async def longday(ctx):
    await ctx.send('Its been a long day \n'
                   'Without you my friend \n'
                   'And I will tell you all about it when i see you again \n')



# Moderation commands

@bot.command()
@commands.has_any_role('MODERATOR', 'happy', 'Bonked by Zi', ROLES.PRESIDENT)
async def mute(ctx, member: Member, timelimit):
    if 's' in timelimit:
        gettime = timelimit.strip('s')
        if int(gettime) > 2419200:
            await ctx.send('Mute time cannot be greater than 28 days.')
        else:
            newtime = datetime.timedelta(seconds=int(gettime))
            await member.edit(timed_out_until=discord.utils.utcnow() + newtime)

    elif 'h' in timelimit:
        gettime = timelimit.strip('h')
        if int(gettime) > 720:
            await ctx.send('Mute time cannot be greater than 28 days.')
        else:
            newtime = datetime.timedelta(hours=int(gettime))
            await member.edit(timed_out_until=discord.utils.utcnow() + newtime)

    elif 'd' in timelimit:
        gettime = timelimit.strip('d')
        if int(gettime) > 28:
            await ctx.send('Mute time cannot be greater than 28 days.')
        else:
            newtime = datetime.timedelta(days=int(gettime))
            await member.edit(timed_out_until=discord.utils.utcnow() + newtime)
    elif 'w' in timelimit:
        gettime = timelimit.strip('w')
        if int(gettime) > 4:
            await ctx.send('Mute time cannot be greater than 28 days.')
        else:
            newtime = datetime.timedelta(weeks=int(gettime))
            await member.edit(timed_out_until=discord.utils.utcnow() + newtime)
    await ctx.send(f'{member.mention} was muted for {timelimit}')


@bot.command()
@commands.has_any_role('MODERATOR', 'happy', ROLES.PRESIDENT)
async def unmute(ctx, member: Member):
    await member.edit(timed_out_until=None)

@bot.command(pass_context=True)
@commands.has_any_role('VANGUARD', 'happy', ROLES.PRESIDENT)
async def ban(ctx, user_id: int = None, *, reason: str = None):
    # Check if a user ID is provided
    if not user_id:
        await ctx.send("Please provide a valid user ID to ban.")
        return

    # Ensure a reason is provided
    if not reason:
        reason = "No reason provided."

    try:
        # Ban the user by ID
        await ctx.guild.ban(discord.Object(id=user_id), reason=f"Banned by {ctx.author.name} - {reason}")
        await ctx.send(f"<@{user_id}> has been banned.")
        
    except Exception as e:
        await ctx.send(f"An error occurred while banning the user: {e}")


@bot.command()
async def listrole(ctx, member: Member = None):
    if not member:
        member = ctx.author
    roles = [role.name for role in member.roles]
    await ctx.send(f"{member.display_name}'s roles: {'\n'.join(roles)}\n**{member.display_name} has {len(roles)} roles**")


@bot.command()
@commands.has_any_role('VANGUARD', 'happy', ROLES.PRESIDENT)
async def unban(ctx, user: User):
    await ctx.guild.unban(user)
    await ctx.send(f'**{user}** was unbanned')

@bot.command()
@commands.has_any_role('GUARDIAN', 'happy', ROLES.PRESIDENT, ROLES.GUARDIAN)
async def kick(ctx, member: Member):
    try:
        await member.kick()
        await ctx.send(f'**{member}** was kicked')
    except discord.Forbidden:
        await ctx.send("I don't have permission to kick this member.")
    except discord.HTTPException:
        await ctx.send("An error occurred while trying to kick the member.")

@bot.command()
@commands.has_any_role('MODERATOR', 'happy', ROLES.PRESIDENT)
async def purge(ctx, limit: int):
    await ctx.message.delete()
    await ctx.channel.purge(limit=limit)


@bot.command()
@commands.has_any_role('MODERATOR', 'happy')
async def botpurge(ctx, limit: int):
    def is_bot_message(message):
        return message.author.bot #Filters messages sent by bots
    
    await ctx.message.delete()
    await ctx.channel.purge(limit=limit, check=is_bot_message)

snipe_messages = {}

@bot.event
async def on_message_delete(message):
    global snipe_messages
    attachments = [(attachment.url, attachment.content_type) for attachment in message.attachments]  # Store file type
    snipe_messages[message.channel.id] = (message.content, message.author, attachments)

@bot.command()
@commands.has_any_role("MODERATOR", ROLES.PRESIDENT)
async def snipe(ctx):
    global snipe_messages
    if ctx.channel.id not in snipe_messages:
        await ctx.send("There's nothing to snipe in this channel.")
    else:
        content, author, attachments = snipe_messages[ctx.channel.id]
        embed = discord.Embed(description=content, color=discord.Color.blue())
        embed.set_author(name=str(author), icon_url=author.avatar.url)

        # Display first image if available
        for attachment_url, content_type in attachments:
            if "image" in content_type:
                embed.set_image(url=attachment_url)
                break  # Stops after embedding one image

        await ctx.send(embed=embed)

        # Send ALL attachments separately
        # for attachment_url, content_type in attachments:
          #  await ctx.send(attachment_url)


@bot.command()
@commands.has_any_role('MODERATOR', ROLES.TOTALLY_MOD)
async def lurk(ctx):
    try:
        channel: discord.TextChannel = bot.get_channel(CHANNELS.CAPITAL) # type: ignore
        LURK_WINDOW_MINUTES = 5.0
        if not channel:
            await ctx.send("Channel not found.")
            return

        now = datetime.datetime.utcnow()
        cutoff_time = now - datetime.timedelta(minutes=LURK_WINDOW_MINUTES)

        messages = [msg async for msg in channel.history(limit=100, after=cutoff_time)]
        active_users = {msg.author.id for msg in messages if not msg.author.bot}

        members = [m for m in channel.guild.members if not m.bot and m.status != discord.Status.offline]
        lurkers = [m for m in members if m.id not in active_users]

        if lurkers:
            ping_count = min(4, len(lurkers))  # Handle if fewer than 4 lurkers
            selected = random.sample(lurkers, ping_count)
            mentions = ', '.join(member.mention for member in selected)

            await channel.send(f"Hey {mentions}, {'and everyone else, ' if len(lurkers) > 4 else ''}quit lurking like bitches 🥰")
        else:
            print("No lurkers found right now!")
    except Exception as e:
        await ctx.send(f"Error: {e}")

@bot.command(pass_context=True)
@commands.has_any_role('MODERATOR', 'happy', 'Midnight Watcher', ROLES.SERVER_BOOSTER, ROLES.PRESIDENT)
async def warn(ctx, user: discord.Member = None, *, reason: str = None): # type: ignore
    author = ctx.author
    if author.top_role.position > user.top_role.position:
        roles = [role.id for role in ctx.author.roles]
    
        # Check if the user is valid
        if not user:
            await ctx.send("Please specify a valid member to warn.")
            return

        # Ensure reason is not empty
        if not reason or not reason.strip():
            await ctx.send("Please provide a valid reason.")
            return
        
        if ROLES.MODERATOR in roles:
            # Get the next warning ID
            warn_id = report["next_warn_id"]
            report["next_warn_id"] += 1  # Increment the counter

            # Notify the user in the channel
            await ctx.send(f'{user.mention} has been warned for: {reason}.')

            # Attempt to DM the user and handle failure gracefully
            try:
                await user.send(f'You have been warned in **{ctx.guild.name}** by **{author.name}** for: {reason}. (ID: {warn_id})\nDM the mods your noods in order to appeal')
            except Exception:
                await ctx.send(f"Couldn't send DM to {user.mention}, but the warning has been recorded.")

            # Update the report dictionary
            found = False
            for current_user in report['users']:
                if current_user['name'] == user.name:
                    current_user['warnings'].append({'id': warn_id, 'reason': reason})
                    found = True
                    break

            # Add a new user if they don't already exist
            if not found:
                report['users'].append({
                    'name': user.name,
                    'warnings': [{'id': warn_id, 'reason': reason}]
                })

            # Save the report to file
            try:
                with open('reports.json', 'w+') as f:
                    json.dump(report, f, indent=4)  # Pretty-print for readability
            except Exception as file_error:
                await ctx.send("Couldn't save the report due to a file error.")
        else:
            await ctx.send(f'{user.mention} stop annoying **{ctx.author.name}** by {reason}.')

    else:
        await ctx.send("You are not high enough in role hierarchy to do that")

@bot.command(pass_context=True)
@commands.has_any_role('MODERATOR', 'happy')
async def removewarn(ctx, warn_id: int = None):
    if not warn_id:
        await ctx.send("Please provide the warning ID to remove.")
        return

    # Find and remove the warning by ID
    removed = False
    for current_user in report['users']:
        for warning in current_user['warnings']:
            if warning['id'] == warn_id:
                current_user['warnings'].remove(warning)
                removed = True
                break
        if removed:
            break

    if not removed:
        await ctx.send("Warning ID not found.")
        return

    # Save the updated report to file
    try:
        with open('reports.json', 'w+') as f:
            json.dump(report, f, indent=4)  # Pretty-print for readability
    except Exception as file_error:
        await ctx.send("Couldn't save the report due to a file error.")

    await ctx.send(f"Warning with ID `{warn_id}` has been removed.")

@bot.command(pass_context=True)
@commands.has_any_role("MODERATOR", 'happy')
async def warns(ctx, user: discord.Member):
    for current_user in report['users']:
        if user.name == current_user['name']:
            # Create a list of warnings with IDs and reasons
            warnings = "\n".join([f"ID: {warning['id']}, Reason: {warning['reason']}" for warning in current_user['warnings']])
            
            # Embed displaying warning details
            embed = discord.Embed(
                title=f"Warnings for {user.name}",
                description=f"{user.name} has {len(current_user['warnings'])} warnings:\n{warnings}",
                color=0xFFFFFF
            )
            await ctx.send(embed=embed)
            break
    else:
        await ctx.send(f"{user.name} has no warnings.")


@bot.command()
@commands.has_any_role('MODERATOR')
async def slowmode(ctx, duration:str):
    
    if 's' in duration:
        dur = duration.strip('s')
        seconds = int(dur)
        await ctx.channel.edit(slowmode_delay=seconds)
        await ctx.send(f"Set the slow mode delay in this channel to {dur} seconds!")
    elif 'm' in duration:
        dur = duration.strip('m')
        minutes = int(dur) * 60
        await ctx.channel.edit(slowmode_delay=minutes)
        await ctx.send(f"Set the slow mode delay in this channel to {dur} minutes!")
    elif 'h' in duration:
        dur = duration.strip('h')
        hours = int(dur) * 3600
        await ctx.channel.edit(slowmode_delay=hours)
        await ctx.send(f"Set the slow mode delay in this channel to {dur} hours!")

@bot.command()
@commands.has_any_role('MODERATOR')
async def endslow(ctx):
    await ctx.channel.edit(slowmode_delay=0)
    await ctx.send("Slow-mode is off!")
    

paginator = Paginator(bot)

# Text commands

# Red embed for moderation commands
embed1 = Embed(title='Moderation Commands', color=0xff0000)
embed1.add_field(name='ban', value='This command bans a member', inline=False)
embed1.add_field(name='unban', value='This command unbans a member', inline=False)
embed1.add_field(name='kick', value='This command kicks a member', inline=False)
embed1.add_field(name='mute', value='This command mutes a member', inline=False)
embed1.add_field(name='purge', value='This command purges messages', inline=False)
embed1.add_field(name='warn', value='This command warns a member', inline=False)
embed1.add_field(name='warns', value='This command checks member warns', inline=False)
embed1.add_field(name='removewarn', value='This command removes member warns', inline=False)
embed1.add_field(name='botpurge', value='Clears bot messages', inline=False)
embed1.add_field(name='listrole', value='Lists all roles in the server', inline=False)
paginator.add_page(embed1)

# Orange embed for economy commands
embed2 = Embed(title='Economy Commands', color=0xffa500)
embed2.add_field(name='bal', value='Shows the user balance', inline=False)
embed2.add_field(name='coinflip', value='Play Heads or Tails to win coins', inline=False)
embed2.add_field(name='roulette', value='Guess bullets for a chance to win coins', inline=False)
embed2.add_field(name='work', value='Earn Eden coins by working', inline=False)
embed2.add_field(name='invest', value='Invest coins to increase your balance', inline=False)
embed2.add_field(name='gamble', value='Try gambling to win coins', inline=False)
embed2.add_field(name='setbal', value='Manually set user balance', inline=False)
embed2.add_field(name='subbal', value='Subtract coins from user balance', inline=False)
embed2.add_field(name='topbal', value='Shows the top 10 richest users', inline=False)
embed2.add_field(name='districtclaim', value='Claim a district', inline=False)
paginator.add_page(embed2)

# Yellow embed for fun commands
embed3 = Embed(title='Fun Commands', color=0xFFFF00)
embed3.add_field(name='meme', value='Fetches a random image from Reddit', inline=False)
embed3.add_field(name='hug', value='Hug a user', inline=False)
embed3.add_field(name='kiss', value='Kiss a user', inline=False)
embed3.add_field(name='cheer', value='Cheer up a user', inline=False)
embed3.add_field(name='compliment', value='Compliment a user', inline=False)
embed3.add_field(name='howgay', value='Checks how gay a user is', inline=False)
embed3.add_field(name='fuck', value='Random fun response', inline=False)
embed3.add_field(name='longday', value="It's been a long day...", inline=False)
embed3.add_field(name='web', value='Fetch search results from the web', inline=False)
embed3.add_field(name='wiki', value='Fetch information from Wikipedia', inline=False)
paginator.add_page(embed3)

# Green embed for informational commands
embed4 = Embed(title='Informational Commands', color=0x008000)
embed4.add_field(name='define', value='Fetches the definition of a word', inline=False)
embed4.add_field(name='urban', value='Fetches word definition from Urban Dictionary', inline=False)
embed4.add_field(name='lyrics', value='Fetch song lyrics using Lyrics.ovh API', inline=False)
embed4.add_field(name='color', value='Retrieves a hex color code or color name from a hex code', inline=False)
embed4.add_field(name='changelog', value='Shows the bot changelog', inline=False)
embed4.add_field(name='halp', value='Displays help for bot commands', inline=False)
embed4.add_field(name='help', value='Shows this message', inline=False)
paginator.add_page(embed4)

# Blue embed for miscellaneous commands
embed5 = Embed(title='Miscellaneous Commands', color=0x0000FF)
embed5.add_field(name='ping', value='Returns Pong', inline=False)
embed5.add_field(name='slowmode', value='Sets a slow mode duration', inline=False)
embed5.add_field(name='endslow', value='Ends slow mode', inline=False)
embed5.add_field(name='snipe', value='Retrieves last deleted message', inline=False)
embed5.add_field(name='stick', value='Sticks a message', inline=False)
embed5.add_field(name='unstick', value='Removes a stuck message', inline=False)
embed5.add_field(name='timer', value='Sets a countdown timer', inline=False)
embed5.add_field(name='cinema', value='Movie-related command', inline=False)
embed5.set_footer(text='This bot was made by Happy')
paginator.add_page(embed5)

@bot.command()
async def halp(ctx):
    """Displays paginated bot command list"""
    await paginator.send(ctx)


@bot.command()
async def howgay(ctx):
    await ctx.send(f'{ctx.author.mention} is {random.randint(0, 100)}% gay')

@bot.command()
async def compliment(ctx):
    good_words = [
        'You are a valuable member',
        'You are an icon!',
        'Elite Eden has never seen a sweeter member',
        'You bring joy to us all',
        'I look up to you',
        'I love you!! (platonically)',
        'You make this server look good',
        'You are such a breath of fresh air',
        'Hi cutie~',
        'I love watching over you',
        'Hi my lil pog champ',
        'I cannot believe one person could be so cool',
        'It is truly an honor to be in the same server with you',
        "You have a brilliant mind", "Your creativity is inspiring", "You light up every room you enter", "Your kindness knows no bounds", "You have a fantastic sense of humor", "Your determination is truly admirable", "You must be swimming in babes"
        
       
    ]
    bad_words = [
        'No compliment for you',
        'You are a piece of shit',
        'Look at this loser fishing for online compliments',
        'Go touch grass',
        'Try this again with an actual person, oh wait-',
        f'I spell annoying with {len(str(ctx.author.name))} letters, {ctx.author.name}',
        'Ew',
        'Whatever you say gooner',
        'Boost the server first, then we can talk',
        "Go cry to your mama, oh right she doesn't like you either",
        'Um mods, this user is harassing me',
        "You're giving NPC energy right now.",
        "The server was a better place before you joined",
        "You're the human equivalent of a buffering wheel.",
        "You're like a TikTok trend, overhyped and irrelevant in a week.",
        "Your drip is dryer than the Sahara.",
        "You're the reason group chats have mute buttons.",
        "You're like a panda, cute but utterly useless"
    ]
    chance = [0.75, 0.25]
    words = random.choices([good_words, bad_words], weights=chance, k=1)[0]
    roles = [role.id for role in ctx.author.roles]
    if ROLES.MODERATOR not in roles and ROLES.SACRIFICE not in roles:
        await ctx.send(random.choice(words))
    elif ROLES.MODERATOR in roles:
        await ctx.send(random.choice(good_words))
    elif ROLES.SACRIFICE in roles:
        await ctx.send(random.choice(bad_words))

@bot.command()
async def ryan(ctx):
    await ctx.send('<:ee_Aira:1302116437594210435>')




# List of banned words (case-insensitive)
slur_words = {"retard", "fag", "faggot", "nigga", "tard", "nigger"}

# The ID of the channel where alerts should be sent
alert_channel_id = 999768498492428398  # Replace with your mod/log/alert channel ID

@bot.tree.command(name="talk")
async def talk(interaction: Interaction, message: str):
    await interaction.response.defer(ephemeral=True)

    # Check for bad words
    lowered = message.lower()
    flagged = any(bad_word in lowered for bad_word in slur_words)

    # Send the original message to the current channel
    await interaction.channel.send(message)  # type: ignore

    # If flagged, notify a specific channel
    if flagged:
        alert_channel = bot.get_channel(alert_channel_id)
        if alert_channel:
            await alert_channel.send(
                f"🚨 Message from {interaction.user.mention} in {interaction.channel.mention} "
                f"contained flagged content: ```{message}```"
            )

    # Clean up original interaction
    await interaction.delete_original_response()



@bot.tree.command(name="embed")
@app_commands.describe(title="The title of the embed", message="The description of the embed", color="The hexadecimal color code for the embed")
async def embed(interaction: Interaction, title: str, message: str, color: str = None):
    """Create an embed with a title, description, and color."""
    try:

        lines = message.split('|')
        formatted_message = "\n".join(lines)

        # Convert the color from string to integer
        if color == None:
            color = discord.Color.blurple()
        color = color.lstrip('#')  # Remove leading '#' if present
        color = int(color, 16) # type: ignore
        embed = Embed(title=title, description=formatted_message, color=color) # type: ignore
        await interaction.response.defer(ephemeral=True)
        
        # Send the embed
        await interaction.channel.send(embed=embed) # type: ignore

        # Optionally delete the original interaction message if visible
        await interaction.delete_original_response()

    except ValueError:
        await interaction.response.send_message("Invalid color code. Please provide a valid hexadecimal value.", ephemeral=True)

# Run 

@bot.command()
async def define(ctx,*,  word: str):
    """Fetches the definition of a word"""
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    async with ctx.typing():
        response = requests.get(url)

        if response.status_code == 200:
        
            data = response.json()
            definition = data[0]["meanings"][0]["definitions"][0]["definition"]
            await ctx.send(f"**{word.capitalize()}**: {definition}")
        else:
            await ctx.send(f"Sorry, I couldn't find a definition for '{word}'.")




@bot.command()
@commands.has_any_role(ROLES.SERVER_BOOSTER, ROLES.MODERATOR, ROLES.WORDLES_WIDOWER, 1118650807785619586) # last role is unknown (remove?)
async def urban(ctx, *, word: str):
    """Fetches the definition of a word from Urban Dictionary"""
    url = f"https://api.urbandictionary.com/v0/define?term={word}"
    async with ctx.typing():
        response = requests.get(url)
        

        if response.status_code == 200:
            data = response.json()
            
            if data["list"]:  # Ensure there's a definition
                definition = data["list"][0]["definition"]
                await ctx.send(f"**{word.capitalize()}**: {definition}")
            else:
                await ctx.send(f"Sorry, I couldn't find a definition for '{word}'.")
        else:
            await ctx.send("Error fetching data from Urban Dictionary.")
@urban.error
async def urban_error(ctx, error):
    if isinstance(error, commands.MissingAnyRole):
        await ctx.send("Exclusive to boosters")


@bot.command()
@commands.cooldown(1,40, commands.BucketType.channel)
async def web(ctx,*,search_msg):
    banned_words = ["milf", 'porn', 'dick', 'pussy', 'femboy', 'milf', 'hentai', '177013', 'r34', 'rule 34', 'nsfw', 'skibidi', 'mpreg', 'sexual', 'lgbt', 'boob', 'creampie', 'goon', 'edging', 'cum', 'slut', 'penis', 'clit', 'breast', 'futa', 'pornhub', 'phallus', 'anus', 'naked', 'nude', 'rule34', 'loli', 'shota', 'gore', 'doggystyle', 'sex position', 'doggy style', 'backshots', 'onlyfans', 'Footjob', 'yiff', 'vagin', 'cliloris', 'pennis', 'nipple', 'areola', 'pubic hair', 'foreskin', 'glans', 'labia', 'scrotum', 'taint', 'thong', 'g-string', 'orgy', 'creamoie']
    eden_meta = {
        "beautiful member": f"<@{USERS.ESMERY}>",
        "beautiful mod": f"<@{USERS.ZI}>",
        "gayest ship": "Emi and Niki.",
        "average eden iq": "The average eden IQ is still below room temperature.",
        "glorious leader": f"<@{USERS.ZI}>",
        "who stole the cheese": f"<@{USERS.SCAREX}>"
    }


    if search_msg.lower() in eden_meta:
        await ctx.send(eden_meta[search_msg.lower()])
        return  # Exit the function after responding

    if any(banned_word in search_msg.lower() for banned_word in banned_words):
        await ctx.send("Your search contains banned words and cannot be processed.")
        web.reset_cooldown(ctx) # type: ignore
        return
    else:
        async with ctx.typing():
            for URL in search(search_msg, stop=1, safe='on', country='us'):
                if "archive.org" not in URL or "files.catbox.moe" not in URL:
                    await ctx.send(URL)
                else:
                    await ctx.send("No results found")



@bot.command()
@commands.has_any_role(ROLES.SERVER_BOOSTER, ROLES.MODERATOR)
@commands.cooldown(1,2, commands.BucketType.channel)
async def wiki(ctx,*,search_msg):
    wiki_sites = ["https://en.wikipedia.org/wiki/", "fandom.com"]
    banned_words = ["milf", 'porn', 'dick', 'pussy', 'femboy', 'milf', 'hentai', '177013', 'r34', 'rule 34', 'nsfw', 'skibidi', 'mpreg', 'sexual', 'lgbt', 'boob', 'creampie', 'goon', 'edging', 'cum', 'slut', 'penis', 'clit', 'breast', 'futa', 'pornhub', 'phallus', 'anus', 'naked', 'nude', 'rule34', 'loli', 'shota', 'gore', 'doggystyle', 'sex position', 'doggy style', 'backshots', 'onlyfans', 'Footjob', 'yiff', 'vagin', 'cliloris', 'pennis', 'nipple', 'areola', 'pubic hair', 'foreskin', 'glans', 'labia', 'scrotum', 'taint', 'thong', 'g-string', 'orgy', 'creamoie']
    if any(banned_word in search_msg.lower() for banned_word in banned_words):
        await ctx.send("Your search contains banned words and cannot be processed.")
        wiki.reset_cooldown(ctx)
        return
    else:
        async with ctx.typing():
            for URL in search(search_msg, stop=1, safe='on', country='us'):
                if any(site in URL for site in wiki_sites):
                    await ctx.send(URL)
                else:
                    await ctx.send("No wiki results found")

@wiki.error
async def wiki_error(ctx, error):
    if isinstance(error, commands.MissingAnyRole):
        await ctx.send("Exclusive to boosters")

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
    async def confess(self, interaction: discord.Interaction, message: str):
        user_name = str(interaction.user.name)  # Convert username to string for JSON compatibility

        if user_name not in user_colors:
            user_colors[user_name] = generate_hex_color()
            save_colors(user_colors)  # Save the updated data

        hex_code = user_colors[user_name]
        color_name = closest_color(hex_code)  # Get closest CSS3 color name

        embed = discord.Embed(title=f"Anon-{hex_code}".capitalize(), description=message, color=int(hex_code[1:], 16))

        await interaction.response.defer(ephemeral=True)  # Prevents errors by deferring the interaction
        await interaction.channel.send(embed=embed)  # Sends the embed without replying to the trigger
        await interaction.delete_original_response()


@bot.command()
@commands.has_any_role(ROLES.SERVER_BOOSTER, ROLES.MODERATOR)
async def fuck(ctx, member: Member):
    embed = Embed(title=f'**{ctx.author.display_name}**! Where are you taking **{member.display_name}**', color=0x00FFFF)
    makeouts = ['https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExMmYwNjUyeXJ6M2l5bTc3anc5bWxnN2szODJjMnd5aXZzZDVweGg3ciZlcD12MV9naWZzX3NlYXJjaCZjdD1n/dWrnYmDucWhDvkbLF6/giphy.gif',
          'https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExOHJldHM5b2Nhc2tpcmQwM2xtdjcxNWlzNnI0eGFwczM4NXVucjJodCZlcD12MV9naWZzX3NlYXJjaCZjdD1n/jUJgL0iByjsAS2MQH1/giphy.gif',
          'https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExbDY2dm5pdmVldTQzdTl1MXRzMHBtdDBzOW5vYXAzdzh2dHplYXdqMCZlcD12MV9naWZzX3NlYXJjaCZjdD1n/KptaYW4AuV2vSkn0Bh/giphy.gif',
          'https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNnUyY3lnOTF4bzlyMzlzdngweTEwdGYxd3N0M20yYzlsdjdlaHZnMSZlcD12MV9naWZzX3NlYXJjaCZjdD1n/mpWQkl5jGLOjjApXUJ/giphy.gif',
          'https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNnUyY3lnOTF4bzlyMzlzdngweTEwdGYxd3N0M20yYzlsdjdlaHZnMSZlcD12MV9naWZzX3NlYXJjaCZjdD1n/iMJwjtL5GLxPYWMob3/giphy.gif',
          'https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExdHNxYTg0aXdyMGV3NGZmZzQ2NmttOTZtZGw4M3pmNW5iMDB2ZHRyYyZlcD12MV9naWZzX3NlYXJjaCZjdD1n/huCxiZ4aibaMngURGX/giphy.gif',
          'https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExM2Q4amdnY216eTl1Z3NlZTR4emdvaGVncGttanRwNW03bnN1c2htayZlcD12MV9naWZzX3NlYXJjaCZjdD1n/cu1l1wN5bNDGUg9QME/giphy.gif',
          'https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExMDkxcmtyZzB4dGw2OWxoNTUyc2lkd2RhZDl0N3I2NGx2eXhzZWdwYiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/oAvQOD7hJMXQFDDhBI/giphy.gif']
    embed.set_image(url=random.choice(makeouts))
    if ctx.author != member:
        await ctx.send(embed=embed)
    else:
        await ctx.send("That sounds like a lonely thing to do")

@fuck.error
async def fuck_error(ctx, error):
    if isinstance(error, commands.MissingAnyRole):
        await ctx.send("Exclusive to boosters")


@bot.command()
async def hug(ctx, member: Member):
    embed = Embed(title=f'**{ctx.author.display_name}** is giving **{member.display_name}** a hug', color=0x00FFFF)
    hugs = ['https://www.icegif.com/wp-content/uploads/hug-icegif-3.gif',
          'https://media.giphy.com/media/XsVaoJbWMASZUmWjT9/giphy.gif?cid=ecf05e470psm6ftj52elckjyyndiv9d3m85j0po2oj3zzgtp&ep=v1_gifs_search&rid=giphy.gif',
          'https://media.giphy.com/media/3o6Zth3OnNv6qDGQ9y/giphy.gif?cid=790b7611fk69752zuim3jfbjuztlsehpjl8270trdbc6e1ad&ep=v1_gifs_search&rid=giphy.gif']
    embed.set_image(url=random.choice(hugs))
    if ctx.author != member:
        await ctx.send(embed=embed)
    else:
        await ctx.send("That's a weird thing to do but okay")




@bot.command()
async def kiss(ctx, member: Member):
    embed = Embed(title=f'**{ctx.author.display_name}** is giving **{member.display_name}** a kiss', color=0xFFC0CB)
    kisses = ['https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExMDl5YTg4NHQ0OWp5ZXAwZm96ZW00NjE1em1yNG84YWR3cHN0MHg0ZCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/hJioaFkX7sjSe7Tkd1/giphy.gif',
              'https://cdn.discordapp.com/attachments/1328742188384911422/1332983986397380638/IMG_6977.gif',
              'https://media.giphy.com/media/4H28yacGCjrkQ/giphy.gif?cid=ecf05e47425g9kf69f1i2kddb1jcln6zkf5ewb2o8z39ljo3&ep=v1_gifs_related&rid=giphy.gif',
              'https://cdn.discordapp.com/attachments/760988796249833472/857741056237764648/image0.gif',
              'https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExbXZ0c2VxcHk2Mjh1NGIzbXE2am9sdjB5NDF3anJyZXYyNWZrNXllbSZlcD12MV9naWZzX3NlYXJjaCZjdD1n/9G0AdBbVrkV3O/giphy.gif',
              'https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExMHJxcHYyMmE0enQ2YjN0aWR2dzB0OHN4anlwN252ejd6ZGx5MXlsNyZlcD12MV9naWZzX3NlYXJjaCZjdD1n/G3va31oEEnIkM/giphy.gif',
              'https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExc2lvZWpza25oeTU3bzd4MTI4bzFuMjZzbDN2ZWowNW00dzJqcmVnZyZlcD12MV9naWZzX3NlYXJjaCZjdD1n/DhclkBm2dRlRKSgRmV/giphy.gif',
              'https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExamZxM3dub25hOWdrbzlibzlicWx4MjV4MXR1dzNxeWZzcHY2cWJvbyZlcD12MV9naWZzX3NlYXJjaCZjdD1n/c7mnNZUxrK8VxXIioH/giphy.gif',
              'https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExbXZ0c2VxcHk2Mjh1NGIzbXE2am9sdjB5NDF3anJyZXYyNWZrNXllbSZlcD12MV9naWZzX3NlYXJjaCZjdD1n/11hAbqRK5D0pnW/giphy.gif',
              'https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExbXZ0c2VxcHk2Mjh1NGIzbXE2am9sdjB5NDF3anJyZXYyNWZrNXllbSZlcD12MV9naWZzX3NlYXJjaCZjdD1n/frHK797nhEUow/giphy.gif',
              'https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExbXZ0c2VxcHk2Mjh1NGIzbXE2am9sdjB5NDF3anJyZXYyNWZrNXllbSZlcD12MV9naWZzX3NlYXJjaCZjdD1n/Vi0Ws3t4JSLOgdkaBq/giphy.gif',
              'https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExMHJxcHYyMmE0enQ2YjN0aWR2dzB0OHN4anlwN252ejd6ZGx5MXlsNyZlcD12MV9naWZzX3NlYXJjaCZjdD1n/5ubHiAtBlv9lSlhVld/giphy.gif',
              'https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExMHJxcHYyMmE0enQ2YjN0aWR2dzB0OHN4anlwN252ejd6ZGx5MXlsNyZlcD12MV9naWZzX3NlYXJjaCZjdD1n/bm2O3nXTcKJeU/giphy.gif']
    embed.set_image(url=random.choice(kisses))
    if ctx.author != member:
        await ctx.send(embed=embed)
    else:
        await ctx.send("Kissing yourself won't make you feel better")

def is_unusual_name(name):
    """Checks if a name contains non-standard characters or excessive symbols."""
    if name is None:
        return False
    
    normalized_name = unicodedata.normalize('NFKD', name)  # Normalize Unicode characters
    standard_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789' ")
    
    return any(char not in standard_chars for char in normalized_name)


@bot.command()
@commands.has_any_role('MODERATOR', ROLES.SERVER_BOOSTER)
async def rsf(ctx):
    author = ctx.author
    try:
        """Resets usernames of members whose names exceed the given length."""
        
        for member in ctx.guild.members:
            if member.nick and is_unusual_name(member.nick):  # Check if nickname is unusual
                if author.top_role.position > member.top_role.position:
                    try:
                        await member.edit(nick=None)
                        await ctx.author.send(f"Reset {member.display_name}'s nickname to their default.")
                    except discord.Forbidden:
                        await ctx.author.send(f"Failed to reset {member.display_name}'s nickname (insufficient permissions).")
                    except discord.HTTPException:
                        await ctx.author.send(f"An error occurred while resetting {member.display_name}'s nickname.")


    except Exception as e:
        await ctx.send(f"Error: {e}")


@bot.command()
@commands.has_any_role('MODERATOR', ROLES.SERVER_BOOSTER)
async def murder(ctx, member: Member):
    author = ctx.author
    if author.top_role.position > member.top_role.position:
        try:
            extra_text = "'s ghost"

            current_nick = member.nick if member.nick else member.name
            
            # Prevent nickname length issues
            if current_nick and len(current_nick) >= 22:
                current_nick = member.name


            new_nick = f"{current_nick} {extra_text}"  # Append new words
            await member.edit(nick=new_nick)
            await ctx.send(f"{member.name} is dead")
        

        except Exception as e:
            await ctx.send(f"An unexpected error occurred: {e}")
            print(f"An error occurred: {e}")

    else:
        await ctx.send("You are not high enough in role hierarchy to do this")


@murder.error
async def murder_error(ctx, error):
    if isinstance(error, discord.errors.HTTPException):
        await ctx.send("Member is dead but the name is too long in length to edit.")



@bot.command()
async def kill(ctx, member: Member):
    embed = Embed(title=f'**{ctx.author.display_name}** just killed **{member.display_name}**', color=0x780606)
    kills = ['https://cdn.discordapp.com/attachments/968071856055808050/1287417809290395720/anime-dokuro-chan.gif',
          'https://cdn.discordapp.com/attachments/968071856055808050/1287417810254823565/Meet_the_Spy.gif',
          'https://cdn.discordapp.com/attachments/968071856055808050/1287395920631173151/mobile-suit-gundam.gif',
          'https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExZnJ1M3JrbDM1N3NzOXhicDIxc3B2dndldmIyYXk4aWU2eWxsanhyZiZlcD12MV9naWZzX3NlYXJjaCZjdD1n/U0KOiTfDChnuyauMpB/giphy.gif',
          'https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExa3lqeGIxYzA5c3hsNWZjNjBoazh3anBzdnZ3djd4c2VvaWxwcW42ZSZlcD12MV9naWZzX3NlYXJjaCZjdD1n/dVcdb4nSu7RXC9j0q4/giphy.gif',
          'https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExeXM5YmNveDNpbmkxN2g4ZzhhZDZvenhzbmptcnBhN3FrZ3dxeWo1ZyZlcD12MV9naWZzX3NlYXJjaCZjdD1n/moWba8OhAmhZ6/giphy.gif',
          'https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExOWRteWxrZm16MjB5YXVyYm9yMjk3YXZkeXFnc2Jmc2tybDhpYmoxYiZlcD12MV9naWZzX3NlYXJjaCZjdD1n/FduDZQp8oRb86aMEbe/giphy.gif',
          'https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExZmd6ZGE1Y2ttajdhbWZnMmNlM2N3am5nbjhzczNyNzdodDJxMTRwayZlcD12MV9naWZzX3NlYXJjaCZjdD1n/HdVtsppIpBigM/giphy.gif',
          'https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExdXV1ZTducXR1czh3MGI1cnprcjFkY3M5N2NydGJ2cTZ5cjMwamF5dyZlcD12MV9naWZzX3NlYXJjaCZjdD1n/CatCCFZa6U8nK/giphy.gif']
    embed.set_image(url=random.choice(kills))
    if ctx.author != member:
        await ctx.send(embed=embed)
    else:
        await ctx.send("Suicide is so last year smh")


@bot.command()
async def cheer(ctx, member: Member):
    embed = Embed(title=f'{ctx.author.display_name} is cheering {member.display_name} up', color=0xf0e130)
    cheers = ['https://tenor.com/view/hug-brandon-terry-carson-the-ms-pat-show-good-job-gif-22509570',
          'https://tenor.com/view/sami-en-dina-sami-dina-dina-sami-dina-en-sami-gif-15422575992980791421',
          'https://tenor.com/view/hug-warm-hug-depressed-hug-gif-45850647380683423']
    embed.set_image(url=random.choice(cheers))
    await ctx.send(embed=embed)

@bot.command()
async def timer(ctx):
    await ctx.send('WIP')



# Economy commands
@bot.command()
async def bal(ctx, user: Optional[Member] = None): # type: ignore
    if user is None:
        user: Member = ctx.author
        pronoun = "Your"
    else:
        pronoun = f"{user.mention}'s"
    found = False
    for current_acc in bank['users']:
        if user.name == current_acc['name']:
            found = True
            await ctx.send(f"{pronoun} balance is {current_acc['balance']} eden coins")
            break
    if not found:
          bank['users'].append({
              'name': user.name,
              'balance': 0
          })
          await ctx.send(f"{pronoun} balance is 0 eden coins")
    with open("users.json", "w+") as s:
        json.dump(bank, s, indent=4)

@bot.command()
async def topbal(ctx):
    """Displays the top 10 users with the highest balance"""
    try:
        if 'users' not in bank:
            await ctx.send("No users found in the economy system.")
            return

        # Sort users by balance (highest first)
        sorted_users = sorted(bank['users'], key=lambda x: x['balance'], reverse=True)

        # Limit to top 10
        top_users = sorted_users[:100]

        
        paginator = Paginator(bot=bot)  # Initialize paginator

        # Create paginated embeds
        for i in range(0, len(top_users), 10):  # Show 10 users per page
            embed = discord.Embed(title="Economy Leaderboard", color=discord.Color.gold())
            for idx, (user) in enumerate(top_users[i:i+10], start=i+1):
                embed.add_field(name=f"{idx}. {user['name']}", value=f"{user['balance']} eden coins", inline=False)

            paginator.add_page(embed)

        await paginator.send(ctx)  # Send paginated leaderboard

    except Exception as e:
        await ctx.send(e)


    """Displays the top 100 users with the most profanity usage using pagination"""
    profanity_data = load_profanity_data()  # Load stored data

    # Sort users by profanity count (highest first)
    sorted_users = sorted(profanity_data.items(), key=lambda x: x[1], reverse=True)

    # Limit to top 100
    top_users = sorted_users[:100]


@bot.command()
@commands.cooldown(1,30, commands.BucketType.user)
async def work(ctx):
    found = False
    for current_acc in bank['users']:
        if ctx.author.name == current_acc['name']:
            found = True
            responses = ['You did a great job and earned', 'You exploited a citizen and earned', 'You forfeited your evening to the mods and earned', 'You stole', 'You were such a cutie you got', 'You begged and got', 'You sent your nudes to the mods and were paid', 'You went to the mines and found', 'You posted on Patreon and got', 'You were so well-behaved you were given', 'You sold your kidney and got', 'You helped an old lady on the street and got', 'Your small business made you', 'Just take these']
            coins = int(current_acc['balance'])
            earn = random.randint(1,3001)
            newcoins = coins + earn
            current_acc['balance'] = newcoins
            if earn == 1984:
                await ctx.send("Your speaking priviledges have been revoked")
                newtime = newtime = datetime.timedelta(minutes=int("5"))
                await ctx.author.edit(timed_out_until=discord.utils.utcnow() + newtime)
            else:    
                await ctx.send(f"{random.choice(responses)} {earn} eden coins")
            break
    if not found:
        earn = random.randint(1,3000)
        bank['users'].append({
            'name': ctx.author.name,
            'balance': earn
            })
        await ctx.send(f"{random.choice(responses)} {earn} eden coins")

    with open("users.json", "w") as s:
        json.dump(bank, s, indent=4)

@work.error
async def work_error(ctx, error):
    if isinstance(error, commands.CommandInvokeError):
        await ctx.send("Please make an account with `;bal` first.")


@bot.command()
async def coinflip(ctx, *, txt:str):
    found = False
    sides = ['heads', 'tails']
    toss = random.choice(sides)
    
    if txt.lower() in sides:
        if txt.lower() == toss:
            for current_acc in bank['users']:
                if ctx.author.name == current_acc['name']:
                        found = True
                        coins = int(current_acc['balance'])
                        earn = 1000
                        newcoins = coins + earn
                        current_acc['balance'] = newcoins
                        await ctx.send(f"You won {earn} eden coins")
                        break

            if not found:
                bank['users'].append({
                        'name': ctx.author.name,
                        'balance': earn
                        })
                await ctx.send(f"You won {earn} eden coins")

        else:
                await ctx.send('You lost')
    else:
        await ctx.send('Pick either ``heads`` or ``tails``')

    with open("users.json", "w+") as s:
        json.dump(bank, s, indent=4)


@bot.command()
@commands.has_any_role('MODERATOR', 'happy')
@commands.cooldown(1,500, commands.BucketType.user)
async def subbal(ctx, member: Member):
    userid = member.name
    found = False
    for current_acc in bank['users']:
        if userid == current_acc['name']:
            found = True
            current_acc['balance'] = 0
            
            await ctx.send(f"{member.mention} 's balance is {current_acc['balance']} eden coins")
            break
    if not found:
          bank['users'].append({
              'name': userid,
              'balance': 0
          })
          await ctx.send(f"{Member} 's balance is 0 eden coins")

    with open("users.json", "w+") as s:
        json.dump(bank, s, indent=4)


@bot.command()
@commands.has_any_role('Bonked by Zi')
async def setbal(ctx, member: Member, coins: int):
    userid = member.name
    found = False
    for current_acc in bank['users']:
        if userid == current_acc['name']:
            found = True
            current_acc['balance'] = coins
            
            await ctx.send(f"{member.mention} 's balance is {current_acc['balance']} eden coins")
            break
    if not found:
          bank['users'].append({
              'name': userid,
              'balance': coins
          })
          await ctx.send(f"{Member} 's balance is {coins} eden coins")

    with open("users.json", "w+") as s:
        json.dump(bank, s, indent=4)

@setbal.error
async def setbal_error(ctx, error):
    if isinstance(error, commands.MissingAnyRole):
        await ctx.send('Only the bot dev is allowed to use this.')

@bot.command()
async def win(ctx):
    userid = ctx.author.name
    found = False
    for current_acc in bank['users']:
        if userid == current_acc['name']:
            found = True
            coins = int(current_acc['balance'])
            if coins < 100000:
                await ctx.send('You do not have enough coins, you need 100,000')
                break
            else:
                newcoins = coins - 100000
                current_acc['balance'] = newcoins
                channel: discord.TextChannel = bot.get_channel(CHANNELS.WINNERS) # type: ignore
                await channel.send(f'{ctx.author.mention} won the prize')
                break
    if not found:
        bank['users'].append({
                'name': ctx.author.name,
                'balance': 0
                })
        await ctx.send("You do not have an account")

        with open("users.json", "w+") as s:
            json.dump(bank, s, indent=4)




@bot.command()
@commands.cooldown(1,300, commands.BucketType.user)
async def roulette(ctx, bullets:int):
    if bullets < 1 or bullets > 5:
        roulette.reset_cooldown(ctx)
        await ctx.send('Please choose between 1 and 5 bullets')
        return
        
    userid = ctx.author.name
    found = False
    chamber = [1] * bullets + [0] * (6 - bullets)
    random.shuffle(chamber)
    print(f'shuffled chambers: {chamber}') # Debug feature

    fired_chamber = random.choice(chamber)

    if fired_chamber == 0:
        for current_acc in bank['users']:
            found = True
            if userid == current_acc['name']:
                roulette.reset_cooldown(ctx) #Cooldown is reset
                coins = int(current_acc['balance'])
                earn = 1000 * bullets
                newcoins = coins + earn
                current_acc['balance'] = newcoins
                await ctx.send(f'You won {earn} eden coins')
                break
        if not found:
            roulette.reset_cooldown(ctx) #Cooldown is reset
            bank['users'].append({
                'name': ctx.author.name,
                'balance': earn
            })
            await ctx.send(f'You won {earn} eden coins')

        with open("users.json", "w+") as s:
            json.dump(bank, s, indent=4)

        
    else:
        await ctx.send(f'You died! Try again in 5 minutes')

@roulette.error
async def roulette_error(ctx, error):
    if isinstance(error, commands.BadArgument):
        await ctx.send('Only numbers please!')

@bot.command()
@commands.cooldown(1,5, commands.BucketType.user)
async def gamble(ctx):
    userid = ctx.author.name
    found = False
    nega_earn = 6500
    bot_choice = random.randint(1, 35)
    if bot_choice == 5:
        for current_acc in bank['users']:
            found = True
            if userid == current_acc['name']:
                coins = int(current_acc['balance'])
                if coins >= 6500:
                    earn = 1000000
                    newcoins = coins + earn
                    current_acc['balance'] = newcoins
                    await ctx.send(f'You won {earn} eden coins')
                    break
                else:
                    await ctx.send(f'You do not have enough coins, you need {nega_earn} to participate')
        if not found:
            bank['users'].append({
                'name': ctx.author.name,
                'balance': 0
                })
            await ctx.send('You do not have an account')
        with open('users.json', 'w+') as s:
            json.dump(bank, s)
    else:
        for current_acc in bank['users']:
            if userid == current_acc['name']:
                found = True
                coins = int(current_acc['balance'])
                if coins >= nega_earn:
                    newcoins = coins - nega_earn
                    current_acc['balance'] = newcoins
                    await ctx.send(f'You lost {nega_earn} eden coins')
                    break
                else:
                    await ctx.send(f'You do not have enough coins, you need {nega_earn} to participate')
        if not found:
            bank['users'].append({
                'name': ctx.author.name,
                'balance': 0
            })
            await ctx.send(f'You do not have an account')

        with open("users.json", "w+") as s:
            json.dump(bank, s, indent=4)


# Event commands


command_tracked_messages = {}


message_role_mapping = {}



@bot.command()
@commands.has_any_role('MODERATOR')
async def districtclaim(ctx, category_id: int):
    # Find the category
    category = discord.utils.get(ctx.guild.categories, id=category_id)
    if not category:
        await ctx.send("Category not found. Please provide a valid category ID.")
        return

    # Get text channels within the category
    text_channels = category.text_channels

    # List of channel IDs to exclude
    excluded_channels = [CHANNELS.VIP_LOUNGE, CHANNELS.HONEYMOON, CHANNELS.DISTRICT_SOUTH , CHANNELS.DISTRICT_EAST, CHANNELS.DISTRICT_WEST, CHANNELS.DISTRICT_NORTH]  # Replace with actual IDs of channels to skip

    # Filter out excluded channels
    valid_channels = [channel for channel in text_channels if channel.id not in excluded_channels]

    if len(valid_channels) < 4:
        await ctx.send("Not enough valid channels in this category to send unique messages!")
        return

    # Randomly select 4 unique channels
    random_channels = random.sample(valid_channels, 4)

    # Define 4 unique messages and assign specific roles to them using role IDs
    messages = [
        "South: 🌴",
        "East: 🌾",
        "West: 🍁",
        "North: 🌲"
    ]
    role_ids = [ROLES.DISTRICT_SOUTH, ROLES.DISTRICT_EAST, ROLES.DISTRICT_WEST, ROLES.DISTRICT_NORTH]  # Replace with actual role IDs

    # Send messages and map them to roles
    for channel, message, role_id in zip(random_channels, messages, role_ids):
        sent_message = await channel.send(message)
        message_role_mapping[sent_message.id] = role_id  # Map message ID to its unique role ID

    await ctx.send("Messages sent! Reply with 'claimed' to these messages to interact.")

    try:
        while message_role_mapping:  # Continue until all messages are claimed
            # Wait for a valid reply
            reply = await bot.wait_for("message", timeout=60.0, check=lambda r: (
                r.reference
                and r.reference.message_id in message_role_mapping
            ))

            if "claimed" in reply.content.lower():  # Check for the keyword 'claimed'
                assigned_role_id = message_role_mapping[reply.reference.message_id]
                member_role_ids = [role.id for role in reply.author.roles]

                if assigned_role_id in member_role_ids:
                    await reply.channel.send(f"{reply.author.mention} successfully claimed the message!")
                    del message_role_mapping[reply.reference.message_id]  # Remove the claimed message

                    # Check if all messages have been claimed
                    if not message_role_mapping:  # Dictionary is empty
                        await ctx.send("All messages have been claimed! Great job, everyone! 🎉")
                        break
                else:
                    await reply.channel.send(f"{reply.author.mention}, Wrong district!")
            else:
                await reply.channel.send(f"{reply.author.mention}, *try again... and maybe read the instructions this time?* 🙄")
    except asyncio.TimeoutError:
        # Stop listening after timeout if no reply occurs
        await ctx.send("No replies detected for remaining messages within the timeout period.")

@bot.command()
@commands.has_any_role(ROLES.TOTALLY_MOD)
async def reload(ctx: commands.Context, cog: str):
    """Reloads a specific cog."""
    try:
        await bot.reload_extension(f"cogs.{cog}")
        await ctx.send(f"{cog} cog reloaded successfully!")
    except Exception as e:
        await ctx.send(f"Failed to reload {cog} cog: {e}")
@reload.error
async def reload_error(ctx: commands.Context, error: commands.CommandError):
    """Handles errors for the reload command."""
    if isinstance(error, commands.MissingAnyRole):
        await ctx.send("buzz off butterfingers, only an elite few can tinker with me like that")
    elif isinstance(error, commands.ExtensionNotFound):
        await ctx.send("The specified cog does not exist.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("What do you want me to do, reload *everything*?")
    else:
        await ctx.send(f"An unexpected error occurred: {error}")


# This was created by Happy!
load_dotenv('token.env')

token = os.environ.get("TOKEN")
if not token:
    token = input("Bot token not found. Please enter your token:\n> ")

bot.run(token)
