from discord.ext import commands, tasks
import requests
import discord

import random
from discord import Embed
import constants
from constants import CHANNELS, USERS  # Make sure this has CHANNELS.REDDIT defined!


class RedditCog(commands.Cog):
    """A cog for fetching safe memes from Reddit."""

    def __init__(self, bot):
        self.bot = bot
        self.SUBREDDITS = ["EliteEden"]  # Add more subreddits if needed
        self.LAST_POST_IDS = {subreddit: None for subreddit in self.SUBREDDITS}
        self.check_subreddits.start()

    @tasks.loop(minutes=5.0)
    async def check_subreddits(self):
        """Background task to monitor subreddits for new posts."""
        await self.bot.wait_until_ready()
        headers = {"User-Agent": "Mozilla/5.0"}

        for subreddit in self.SUBREDDITS:
            url = f"https://www.reddit.com/r/{subreddit}/new.json?limit=10"
            try:
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    posts = [
                        post["data"]
                        for post in data["data"]["children"]
                        if post["data"]["url"].endswith(("jpg", "png", "gif", "jpeg"))
                        and not post["data"].get("over_18", False)
                    ]

                    if posts:
                        latest_post = posts[0]
                        post_id = latest_post["id"]

                        if (
                            self.LAST_POST_IDS.get(subreddit) or post_id != post_id
                        ):  # None should also fail this check
                            self.LAST_POST_IDS[subreddit] = post_id
                            embed = Embed(
                                title=latest_post["title"], color=discord.Color.orange()
                            )
                            embed.set_image(url=latest_post["url"])
                            channel = self.bot.get_channel(CHANNELS.REDDIT)
                            await channel.send("Latest post from r/EliteEden")
                            await channel.send(embed=embed)
                else:
                    print(f"Error fetching r/{subreddit}: {response.status_code}")
            except Exception as e:
                print(f"Error processing subreddit {subreddit}: {e}")

    @commands.command(name="meme")
    async def meme(self, ctx: commands.Context, subreddit: str = "memes"):
        """Fetches a random safe-for-work meme from Reddit."""
        subreddit = subreddit.lower().removeprefix("r/").strip()
        headers = {"User-Agent": "Mozilla/5.0"}
        url = f"https://www.reddit.com/r/{subreddit}/new.json?limit=120"
        try:
            async with ctx.typing():
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    valid_posts = [
                        post["data"]
                        for post in data["data"]["children"]
                        if post["data"]["url"].endswith(("jpg", "png", "gif", "jpeg"))
                        and not post["data"].get("over_18", False)
                    ]

                    if valid_posts:
                        random.shuffle(valid_posts)
                        latest_post = valid_posts[0]
                        post_id = latest_post["id"]

                        if self.LAST_POST_IDS.get(subreddit) is None:
                            self.LAST_POST_IDS[subreddit] = post_id
                        elif self.LAST_POST_IDS[subreddit] != post_id:
                            self.LAST_POST_IDS[subreddit] = post_id

                        # Send random meme to user
                        chosen_post = random.choice(valid_posts)
                        embed = Embed(
                            title=chosen_post["title"], color=discord.Color.yellow()
                        )
                        embed.set_image(url=chosen_post["url"])
                        meme_footer_responses = [
                            f"unfunny image brought to you by {ctx.author.name}",
                            "mildly amusing, this one",
                            "take this meme and leave me alone",
                            "LOL",
                            "I find this one rather amusing",
                            "This is humor for dummies but enjoy",
                            "",
                            "hehehe",
                            "memes are great",
                            "of course you'd find this funny",
                            "I don't get it but here you go",
                            "Is this good enough for you?",
                            "dank memer",
                            f"blame {ctx.author.name} for this",
                            "blame germanic, like usual.",
                            "it's always happy. blame happy.",
                            "why?",
                            f"brought to you by the idiots in r/{subreddit}",
                        ]
                        embed.set_footer(text=f"{random.choice(meme_footer_responses)}")
                        await ctx.send(embed=embed)
                    else:
                        await ctx.send("No safe images found in this subreddit.")
                else:
                    await ctx.send(f"Error fetching data: {response.status_code}")
        except Exception as e:
            await ctx.send(f"Error: {e}")

    @commands.command(name="fox", aliases=["cootshk", "fden", "foxes"])
    async def fox(self, ctx: commands.Context):
        """Fetches a random safe-for-work meme from Reddit."""
        subreddits = ["foxes", "programmerhumour", "fox", "linuxmemes"]
        chance = [0.6, 0.2, 0.1, 0.1]
        subreddited: str = random.choices(subreddits, weights=chance, k=1)[0]
        subreddit = subreddited.lower().removeprefix("r/").strip()
        headers = {"User-Agent": "Mozilla/5.0"}
        url = f"https://www.reddit.com/r/{subreddit}/new.json?limit=120"
        try:
            async with ctx.typing():
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    valid_posts = [
                        post["data"]
                        for post in data["data"]["children"]
                        if post["data"]["url"].endswith(("jpg", "png", "gif", "jpeg"))
                        and not post["data"].get("over_18", False)
                    ]

                    if valid_posts:
                        random.shuffle(valid_posts)
                        latest_post = valid_posts[0]
                        post_id = latest_post["id"]

                        if self.LAST_POST_IDS.get(subreddit) is None:
                            self.LAST_POST_IDS[subreddit] = post_id
                        elif self.LAST_POST_IDS[subreddit] != post_id:
                            self.LAST_POST_IDS[subreddit] = post_id

                        # Send random meme to user
                        chosen_post = random.choice(valid_posts)
                        embed = Embed(
                            title=chosen_post["title"], color=discord.Color.yellow()
                        )
                        embed.set_image(url=chosen_post["url"])
                        meme_footer_responses = [
                            f"Sponsored by <@{USERS.COOTSHK}>",
                            "Foxes!!!",
                            "Fden is love",
                            "West supremacy",
                            "",
                            "Linux",
                            "🦊🦊🦊",
                            f"brought to you by the idiots in r/{subreddit}",
                        ]
                        embed.set_footer(text=f"{random.choice(meme_footer_responses)}")
                        await ctx.send(embed=embed)
                    else:
                        await ctx.send("No safe images found in this subreddit.")
                else:
                    await ctx.send(f"Error fetching data: {response.status_code}")
        except Exception as e:
            await ctx.send(f"Error: {e}")


    async def cog_load(self) -> None:
        """This fires when the cog is loaded."""
        # Start the background task to check subreddits
        if not self.check_subreddits.is_running():
            self.check_subreddits.start()
        return await super().cog_load()

    async def cog_unload(self) -> None:
        """This fires when the cog is unloaded."""
        # Stop the background task to check subreddits
        if self.check_subreddits.is_running():
            self.check_subreddits.stop()
        return await super().cog_unload()


async def setup(bot: commands.Bot):
    """Function to load the cog."""
    await bot.add_cog(RedditCog(bot))
    print("RedditCog has been (re-)loaded.")
