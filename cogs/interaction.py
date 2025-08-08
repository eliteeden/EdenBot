from datetime import datetime
import os
from typing import Optional
import discord
from discord import Embed, Member
import aiohttp
from discord import File
from discord.ext import commands
from discord.utils import utcnow
from googlesearch import search
import math 
import asyncio
import random
import requests
import pytz

from constants import ROLES, USERS

class InteractionCog(commands.Cog):
    """Some more random commands"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.messages: dict[int, discord.Message] = {}

    def get_gif(self, folder: str) -> File:
        """Returns a random gif from the specified folder"""
        files = os.listdir("media/" + folder)
        if files:
            return File(f"media/{folder}/" + random.choice(files))
        else:
            raise FileNotFoundError(f"No files found in media/{folder}")

    @commands.command(name='howgay', aliases=['gaydar', 'howgayareyou', 'ilikecheese'])
    async def howgay(self, ctx: commands.Context, user: Member = None): # type: ignore
        try:
            if user is None:
                user = ctx.author
            await ctx.send(f'{user.mention} is {random.randint(0, 100)}% gay')
        except Exception as e:
            await ctx.send(f"Error: {e}")
    
    @commands.command(name='compliment')
    async def compliment(self, ctx: commands.Context):
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
            "You have a brilliant mind",
            "Your creativity is inspiring",
            "You light up every room you enter",
            "Your kindness knows no bounds",
            "You have a fantastic sense of humor",
            "Your determination is truly admirable",
            "You must be swimming in babes"
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
        roles = [role.id for role in ctx.author.roles] # type: ignore
        if ROLES.MODERATOR not in roles and ROLES.SACRIFICE not in roles:
            await ctx.send(random.choice(words))
        elif ROLES.MODERATOR in roles:
            await ctx.send(random.choice(good_words))
        elif ROLES.SACRIFICE in roles:
            await ctx.send(random.choice(bad_words))
    
    @commands.command("ryan")
    async def ryan(self, ctx: commands.Context):
        await ctx.send("Ryan this, Ryan that\nI just want to know what the fate of my 6 siblings is")

    @commands.command(name="define", aliases=['wtfenglish'])
    async def define(self, ctx: commands.Context, *, word: str):
        """Fetches the definition of a word using Free Dictionary API (no API key required)"""
        import aiohttp

        api_url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"

        async with ctx.typing():
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if isinstance(data, list) and data and "meanings" in data[0]:
                            meanings = data[0]["meanings"]
                            if meanings and "definitions" in meanings[0] and meanings[0]["definitions"]:
                                definition = meanings[0]["definitions"][0]["definition"]
                                await ctx.send(f"**{word.capitalize()}**: {definition}")
                            else:
                                await ctx.send(f"Sorry, I couldn't find a definition for '{word}'.")
                        else:
                            await ctx.send(f"Sorry, I couldn't find a definition for '{word}'.")
                    else:
            
                        await ctx.send(f"Sorry, I couldn't find a definition for '{word}'.")
    @commands.command(name="urban", aliases=['urbandictionary', 'dic'])
    @commands.has_any_role(ROLES.SERVER_BOOSTER, ROLES.MODERATOR, ROLES.WORDLES_WIDOWER, "Fden Bot Perms", 1118650807785619586, "happy")
    async def urban(self, ctx: commands.Context, *, word: str):
        """Fetches the definition of a word from Urban Dictionary (no API key required)"""

        url = f"https://api.urbandictionary.com/v0/define?term={word}"
        async with ctx.typing():
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data["list"]:
                            definition = data["list"][0]["definition"]
                            await ctx.send(f"**{word.capitalize()}**: {definition}")
                        else:
                            await ctx.send(f"Sorry, I couldn't find a definition for '{word}'.")
                    else:
                        await ctx.send("Error fetching data from Urban Dictionary.")
    @urban.error
    async def urban_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingAnyRole):
            await ctx.send("Exclusive to boosters")


    @commands.command(name="xkcd", aliases=["comic"])
    @commands.has_any_role("Fden Bot Perms", "happy", 1118650807785619586, ROLES.SERVER_BOOSTER, ROLES.MODERATOR)
    async def xkcd(self, ctx: commands.Context, *, title: str = None):
        """Fetches an xkcd comic by title. If no title is given, returns the latest comic."""

        async with ctx.typing():
            try:
                if not title:
                    # Get latest comic
                    latest = requests.get("https://xkcd.com/info.0.json").json()
                    await ctx.send(
                        f"**xkcd #{latest['num']}: {latest['title']}**\n{latest['alt']}\n{latest['img']}"
                    )
                    return

                # Get latest comic number
                latest_num = requests.get("https://xkcd.com/info.0.json").json()["num"]

                # Search for title match
                for num in range(1, latest_num + 1):
                    url = f"https://xkcd.com/{num}/info.0.json"
                    response = requests.get(url)
                    if response.status_code != 200:
                        continue
                    data = response.json()
                    if title.lower() in data["title"].lower():
                        await ctx.send(
                            f"**xkcd #{data['num']}: {data['title']}**\n{data['alt']}\n{data['img']}"
                        )
                        return self.web(ctx, search_msg=data["title"])

                await ctx.send(f"No xkcd comic found with title containing '{title}'.")
            except Exception as e:
                await ctx.send(f"Error fetching xkcd comic: {str(e)}")
    
    @commands.command(name='web', aliases=['search', 'google'])
    async def web(self, ctx: commands.Context, *, search_msg: str):
        banned_words = ["milf", 'porn', 'dick', 'pussy', 'femboy', 'milf', 'hentai', '177013', 'r34', 'rule 34', 'nsfw', 'skibidi', 'mpreg', 'sexual', 'lgbt', 'boob', 'creampie', 'goon', 'edging', 'cum', 'slut', 'penis', 'clit', 'breast', 'futa', 'pornhub', 'phallus', 'anus', 'naked', 'nude', 'rule34', 'loli', 'shota', 'gore', 'doggystyle', 'sex position', 'doggy style', 'backshots', 'onlyfans', 'Footjob', 'yiff', 'vagin', 'cliloris', 'pennis', 'nipple', 'areola', 'pubic hair', 'foreskin', 'glans', 'labia', 'scrotum', 'taint', 'thong', 'g-string', 'orgy', 'creamoie']
        eden_meta = {
            "beautiful member": f"<@{USERS.ESMERY}>",
            "beautiful mod": f"<@{USERS.ZI}>",
            "gayest ship": "Emi and Niki.",
            "average eden iq": "The average eden IQ is still below room temperature.",
            "glorious leader": f"<@{USERS.ZI}>",
            "who stole the cheese": f"<@{USERS.SCAREX}>",
            "who is eden's most annoying person": f"<@{USERS.DECK}>",
            "best bot": "it's obviously me",
            "retard": f"<@{USERS.COOTSHK}> until one of the mods bans you for this" # heh heh heh
        }


        if search_msg.lower() in eden_meta:
            await ctx.send(eden_meta[search_msg.lower()])
            return  # Exit the function after responding

        if any(banned_word in search_msg.lower() for banned_word in banned_words):
            await ctx.send("Your search contains banned words and cannot be processed.")
            return
        else:
            async with ctx.typing():
                for URL in search(search_msg, stop=1, safe='on', country='us'):
                    if "archive.org" not in URL or "files.catbox.moe" not in URL:
                        await ctx.send(URL)
                    else:
                        await ctx.send("No results found")

    @commands.command(name='wiki', aliases=['wikipedia', 'fandom'])
    @commands.has_any_role(ROLES.SERVER_BOOSTER, ROLES.MODERATOR, "Fden Bot Perms")
    async def wiki(self, ctx: commands.Context, *, search_msg: str):
        wiki_sites = ["https://en.wikipedia.org/wiki/", "fandom.com"]
        banned_words = ["milf", 'porn', 'dick', 'pussy', 'femboy', 'milf', 'hentai', '177013', 'r34', 'rule 34', 'nsfw', 'skibidi', 'mpreg', 'sexual', 'lgbt', 'boob', 'creampie', 'goon', 'edging', 'cum', 'slut', 'penis', 'clit', 'breast', 'futa', 'pornhub', 'phallus', 'anus', 'naked', 'nude', 'rule34', 'loli', 'shota', 'gore', 'doggystyle', 'sex position', 'doggy style', 'backshots', 'onlyfans', 'Footjob', 'yiff', 'vagin', 'cliloris', 'pennis', 'nipple', 'areola', 'pubic hair', 'foreskin', 'glans', 'labia', 'scrotum', 'taint', 'thong', 'g-string', 'orgy', 'creamoie']
        if any(banned_word in search_msg.lower() for banned_word in banned_words):
            await ctx.send("Your search contains banned words and cannot be processed.")
            return
        else:
            async with ctx.typing():
                for URL in search(search_msg, stop=1, safe='on', country='us'):
                    if any(site in URL for site in wiki_sites):
                        await ctx.send(URL)
                    else:
                        await ctx.send("No wiki results found")
    @wiki.error
    async def wiki_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingAnyRole):
            await ctx.send("Exclusive to boosters")
    
    @commands.command(name='fuck')
    @commands.has_any_role(ROLES.SERVER_BOOSTER, ROLES.MODERATOR, "Fden Bot Perms")
    async def fuck(self, ctx: commands.Context, member: Member):
        embed = Embed(title=f'**{ctx.author.display_name}**! Where are you taking **{member.display_name}**', color=0x00FFFF)
        file = self.get_gif("fuck")
        embed.set_image(url=f"attachment://{file.filename}")
        if ctx.author == member:
            await ctx.send("That sounds like a lonely thing to do")
        elif self.bot.user == member:
            if ctx.author.id == USERS.COOTSHK:
                await ctx.send("What did you break this time, Henry?")
            else:
                await ctx.send("But why?")
        else:
            await ctx.send(embed=embed, file=file)
    @fuck.error
    async def fuck_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingAnyRole):
            await ctx.send("Exclusive to boosters")

    @commands.command(name='hug')
    async def hug(self, ctx: commands.Context, member: Member):
        embed = Embed(title=f'**{ctx.author.display_name}** is giving **{member.display_name}** a hug', color=0x00FFFF)
        file = self.get_gif("hugs")
        embed.set_image(url=f"attachment://{file.filename}")
        if ctx.author == member:
            await ctx.send("That's a weird thing to do but okay")
        elif member == self.bot.user:
            if ctx.author.id == USERS.COOTSHK:
                # me waiting on kiki to finish that drawing
                await ctx.send("Thanks, Henry! I needed that. <3")
            else:
                await ctx.send("Sorry... I have trust issues. People call me slurs way too much.")
        else:
            await ctx.send(embed=embed, file=file)
    
    @commands.command(name='kiss')
    async def kiss(self, ctx: commands.Context, member: Member):
        embed = Embed(title=f'**{ctx.author.display_name}** is giving **{member.display_name}** a kiss', color=0xFFC0CB)
        file = self.get_gif("kiss")
        embed.set_image(url=f"attachment://{file.filename}")
        if ctx.author == member:
            await ctx.send("Kissing yourself won't make you feel better")
        elif member == self.bot.user:
            if ctx.author.id == USERS.COOTSHK:
                if (hour:=datetime.now(pytz.timezone("America/Chicago")).hour) >= 23 or hour < 6: # 11 - 6
                    await ctx.send("Get some sleep, Henry. You need it.")
                else:
                    await ctx.send("Shouldn't you be programming?")
            else:
                await ctx.send("I'm flattered but your loneliness is such a turn off")
        else:
            await ctx.send(embed=embed, file=file)

    @commands.command(name="murder")
    @commands.has_any_role('MODERATOR', ROLES.SERVER_BOOSTER, "Fden Bot Perms")
    async def murder(self, ctx: commands.Context, member: Member):
        author: Member = ctx.author # type: ignore
        if author.get_role(ROLES.TOTALLY_MOD) is not None or author.top_role.position > member.top_role.position:
            try:
                extra_text = "'s ghost"

                current_nick = member.nick if member.nick else member.name

                # Prevent nickname length issues
                if current_nick and len(current_nick) >= 22:
                    current_nick = member.name


                new_nick = f"{current_nick.strip()}{extra_text}"  # Append new words
                await member.edit(nick=new_nick, reason=f"Murdered by {author.name}")
                await ctx.send(f"{member.name} is dead")

            except Exception as e:
                await ctx.send(f"An unexpected error occurred: {e}")
                print(f"An error occurred: {e}")

        else:
            await ctx.send("You are not high enough in role hierarchy to do this")
    @murder.error
    async def murder_error(self, ctx: commands.Context, error):
        if isinstance(error, discord.errors.HTTPException):
            await ctx.send("Member is dead but the name is too long in length to edit.")

    @commands.command(name='cheer', aliases=['yass'])
    async def cheer(self, ctx: commands.Context, member: Member):
        embed = Embed(title=f'{ctx.author.display_name} is cheering {member.display_name} up', color=0xf0e130)
        cheers = ['https://tenor.com/view/hug-brandon-terry-carson-the-ms-pat-show-good-job-gif-22509570',
              'https://tenor.com/view/sami-en-dina-sami-dina-dina-sami-dina-en-sami-gif-15422575992980791421',
              'https://tenor.com/view/hug-warm-hug-depressed-hug-gif-45850647380683423']
        embed.set_image(url=random.choice(cheers))
        await ctx.send(embed=embed)

    @commands.command(name='kill', aliases=['poormansmurder'])
    async def kill(self, ctx: commands.Context, member: Member):
        embed = Embed(title=f'**{ctx.author.display_name}** just killed **{member.display_name}**', color=0x780606)
        kills = [
            #'https://cdn.discordapp.com/attachments/968071856055808050/1287417809290395720/anime-dokuro-chan.gif',
            #'https://cdn.discordapp.com/attachments/968071856055808050/1287417810254823565/Meet_the_Spy.gif',
            #'https://cdn.discordapp.com/attachments/968071856055808050/1287395920631173151/mobile-suit-gundam.gif',
            'https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExZnJ1M3JrbDM1N3NzOXhicDIxc3B2dndldmIyYXk4aWU2eWxsanhyZiZlcD12MV9naWZzX3NlYXJjaCZjdD1n/U0KOiTfDChnuyauMpB/giphy.gif',
            'https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExa3lqeGIxYzA5c3hsNWZjNjBoazh3anBzdnZ3djd4c2VvaWxwcW42ZSZlcD12MV9naWZzX3NlYXJjaCZjdD1n/dVcdb4nSu7RXC9j0q4/giphy.gif',
            'https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExeXM5YmNveDNpbmkxN2g4ZzhhZDZvenhzbmptcnBhN3FrZ3dxeWo1ZyZlcD12MV9naWZzX3NlYXJjaCZjdD1n/moWba8OhAmhZ6/giphy.gif',
            'https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExOWRteWxrZm16MjB5YXVyYm9yMjk3YXZkeXFnc2Jmc2tybDhpYmoxYiZlcD12MV9naWZzX3NlYXJjaCZjdD1n/FduDZQp8oRb86aMEbe/giphy.gif',
            'https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExZmd6ZGE1Y2ttajdhbWZnMmNlM2N3am5nbjhzczNyNzdodDJxMTRwayZlcD12MV9naWZzX3NlYXJjaCZjdD1n/HdVtsppIpBigM/giphy.gif',
            'https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExdXV1ZTducXR1czh3MGI1cnprcjFkY3M5N2NydGJ2cTZ5cjMwamF5dyZlcD12MV9naWZzX3NlYXJjaCZjdD1n/CatCCFZa6U8nK/giphy.gif'
        ]
        embed.set_image(url=random.choice(kills))
        if ctx.author == member:
            await ctx.send("Suicide is so last year smh")
        elif member == self.bot.user:
            await ctx.send("What did I do this time?")
        else:
            await ctx.send(embed=embed)
    
    @commands.command(name="getmods", aliases=["mods", "listusers", "rolelist"])
    @commands.has_any_role(ROLES.MODERATOR, ROLES.TOTALLY_MOD)
    async def getmods(self, ctx: commands.Context, chosen_role: discord.Role = None):
        # Use default role ID if no role is provided
        role_id = 993475229798113320 if not chosen_role else chosen_role.id

        # Find the role object by ID
        role = discord.utils.get(ctx.guild.roles, id=role_id)

        if not role:
            await ctx.send("Role not found.")
            return

        if not role.members:
            await ctx.send("No members have that role.")
            return

        # Get paginator cog
        paginator_cog = self.bot.get_cog("PaginatorCog")
        if not paginator_cog:
            await ctx.send("PaginatorCog is not loaded.")
            return

        paginator: PaginatorCog.Paginator = paginator_cog()  # type: ignore

        members = role.members
        for i in range(0, len(members), 10):  # 10 members per page
            embed = discord.Embed(
                title=f"{role.name} Members ({len(role.members)} total)",
                color=discord.Color.blurple()
            )
            for idx, member in enumerate(members[i:i + 10]):
                embed.add_field(
                    name=f"{i + idx + 1}. {member.display_name}",
                    value=member.mention,
                    inline=False
                )
            paginator.add_page(embed)

        await paginator.send(ctx)

    @commands.command(name="pinglist", aliases=["modlist", "pings"])
    @commands.has_any_role(ROLES.MODERATOR, ROLES.TOTALLY_MOD)
    async def pinglist(self, ctx: commands.Context, role: Optional[discord.Role | int] = None):
        # Use default role ID if no role is provided
        assert ctx.guild is not None
        if not isinstance(role, discord.Role):
            role = ctx.guild.get_role(role or ROLES.PROTECTOR)

        if not role:
            await ctx.send("Role not found.")
            return

        if not role.members or len(role.members) == 0:
            await ctx.send("No members have that role.")
            return

        # Get mentions of all members
        mentions = [member.mention for member in role.members]

        # Break into chunks of up to 50 mentions per message
        chunk_size = 50
        for i in range(0, len(mentions), chunk_size):
            chunk = '\n'.join(mentions[i:i + chunk_size])
            await ctx.send(chunk)

    @commands.command(name='find', aliases=["zii", "yoink", "stalk", "hunt", "track"])
    @commands.has_any_role(ROLES.MODERATOR, ROLES.TOTALLY_MOD)
    async def find(self, ctx: commands.Context, member: Optional[discord.Member] = None): # type: ignore
        """Finds the most recent message from a member across all text channels, using cache + parallel scanning."""
        try:
            async with ctx.typing():
                member: Member = member or ctx.guild.get_member(USERS.ZI) # type: ignore
                member_id = member.id # type: ignore

                # Try cached message first
                if member_id in self.messages:
                    cached_msg = self.messages[member_id]
                    timestamp = int(cached_msg.created_at.timestamp())
                    await ctx.send(
                        f"{member.display_name} was last seen in <#{cached_msg.channel.id}> — <t:{timestamp}:R>. [Jump!]({cached_msg.jump_url})"
                    )
                    return

                # Scan all channels concurrently
                async def scan_channel(channel):
                    try:
                        async for msg in channel.history(limit=100):
                            if msg.author.id == member_id:
                                return msg
                    except discord.Forbidden:
                        return None

                tasks = [scan_channel(channel) for channel in ctx.guild.text_channels] # type: ignore
                results = await asyncio.gather(*tasks)
                messages = [msg for msg in results if msg]

                if messages:
                    latest_msg = max(messages, key=lambda m: m.created_at)
                    timestamp = int(latest_msg.created_at.timestamp())
                    await ctx.send(
                        f"It has been <t:{timestamp}:R> since {member.display_name} was last seen in #{getattr(latest_msg.channel, 'name', 'DMs')}. [Jump!]({latest_msg.jump_url})"
                    )
                else:
                    await ctx.send(f"Couldn’t find any recent messages from {member.display_name}.")
        except Exception as e:
            await ctx.send(f"Error: {e}")
    # On message event
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Listens for messages and responds to specific keywords."""
        self.messages[message.author.id] = message


async def setup(bot: commands.Bot):
    await bot.add_cog(InteractionCog(bot))
    print("InteractionCog loaded successfully.")
