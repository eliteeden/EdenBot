# TODO Add the modules for this command


from click import Command
import discord
from discord.ext import commands
import asyncio
import yt_dlp

class MusicCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.queue = []
        self.current = None
        self.voice_client = None
        self.skip_votes = set()
        self.skip_threshold = 2  # Default number of votes to skip

    @commands.command()
    async def join(self, ctx):
        """Joins the voice channel."""
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            self.voice_client = await channel.connect()
            await ctx.send(f"🎶 Joined {channel.name}")
        else:
            await ctx.send("You're not in a voice channel!")

    @commands.command()
    async def play(self, ctx, *, url: str):
        """Plays a song or playlist from YouTube or Spotify."""
        if not self.voice_client or not self.voice_client.is_connected():
            await self.join(ctx)

        self.queue.append(url)
        await ctx.send(f"🎵 Added to queue: {url}")

        if not self.voice_client.is_playing():
            await self._play_next(ctx)

    async def _play_next(self, ctx):
        if not self.queue:
            await ctx.send("Queue is empty.")
            return

        self.skip_votes.clear()
        self.current = self.queue.pop(0)

        ydl_opts = {
            'format': 'bestaudio',
            'quiet': True,
            'default_search': 'auto',
            'extract_flat': 'in_playlist',
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(self.current, download=False)
            if 'entries' in info:
                info = info['entries'][0]
            url = info['url']

        source = await discord.FFmpegOpusAudio.from_probe(url)
        self.voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(self._play_next(ctx), self.bot.loop))
        await ctx.send(f"▶️ Now playing: {info.get('title', 'Unknown')}")

    @commands.command()
    async def skip(self, ctx):
        """Votes to skip the current song."""
        user = ctx.author.id
        if user in self.skip_votes:
            await ctx.send("You've already voted to skip.")
            return

        self.skip_votes.add(user)
        votes = len(self.skip_votes)
        await ctx.send(f"⏭️ Skip vote added ({votes}/{self.skip_threshold})")

        if votes >= self.skip_threshold:
            await ctx.send("⏩ Skipping song!")
            self.voice_client.stop()

    @commands.command()
    async def setskip(self, ctx, threshold: int):
        """Sets the number of votes needed to skip."""
        self.skip_threshold = threshold
        await ctx.send(f"✅ Skip threshold set to {threshold}")

    @commands.command()
    async def leave(self, ctx):
        """Leaves the voice channel."""
        if self.voice_client:
            await self.voice_client.disconnect()
            self.voice_client = None
            await ctx.send("👋 Left the voice channel.")
        else:
            await ctx.send("I'm not in a voice channel.")

async def setup(bot):
    """Function to load the cog"""
    bot.add_cog(MusicCog(bot))
    print("MusicCog has been loaded successfully")