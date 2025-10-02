import discord
from discord.ext import commands
import asyncio
import yt_dlp

class MusicCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_clients = {}  # Per-guild voice clients
        self.queues = {}         # Per-guild queues
        self.currents = {}       # Per-guild current track
        self.skip_votes = {}     # Per-guild skip votes
        self.skip_threshold = 2  # Default number of votes to skip

    def get_voice_client(self, ctx):
        return self.voice_clients.get(ctx.guild.id)

    def get_queue(self, ctx):
        return self.queues.setdefault(ctx.guild.id, [])

    def get_skip_votes(self, ctx):
        return self.skip_votes.setdefault(ctx.guild.id, set())

    @commands.command()
    async def join(self, ctx):
        """Joins the voice channel."""
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            self.voice_clients[ctx.guild.id] = await channel.connect()
            await ctx.send(f"🎶 Joined {channel.name}")
        else:
            await ctx.send("You're not in a voice channel!")

    @commands.command()
    async def play(self, ctx, *, url: str):
        """Plays a song or playlist from YouTube or Spotify."""
        vc = self.get_voice_client(ctx)
        if not vc or not vc.is_connected():
            await self.join(ctx)
            vc = self.get_voice_client(ctx)

        if not vc:
            await ctx.send("❌ Could not connect to voice channel.")
            return

        self.get_queue(ctx).append(url)
        await ctx.send(f"🎵 Added to queue: {url}")

        if not vc.is_playing():
            await self._play_next(ctx)

    async def _play_next(self, ctx):
        queue = self.get_queue(ctx)
        vc = self.get_voice_client(ctx)

        if not queue:
            await ctx.send("Queue is empty.")
            return

        self.get_skip_votes(ctx).clear()
        self.currents[ctx.guild.id] = queue.pop(0)

        ydl_opts = {
            'format': 'bestaudio',
            'quiet': True,
            'default_search': 'auto',
            'extract_flat': 'in_playlist',
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.currents[ctx.guild.id], download=False)
                if 'entries' in info:
                    info = info['entries'][0]
                stream_url = info['url']
                title = info.get('title', 'Unknown')
        except Exception as e:
            await ctx.send(f"❌ Failed to extract audio: {e}")
            return

        def after_playing(error):
            if error:
                print(f"Error: {error}")
            asyncio.run_coroutine_threadsafe(self._play_next(ctx), self.bot.loop)

        source = discord.FFmpegPCMAudio(
            stream_url,
            before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            options="-vn"
        )
        vc.play(source, after=after_playing)
        await ctx.send(f"▶️ Now playing: {title}")

    @commands.command()
    async def skip(self, ctx):
        """Votes to skip the current song."""
        user_id = ctx.author.id
        votes = self.get_skip_votes(ctx)

        if user_id in votes:
            await ctx.send("You've already voted to skip.")
            return

        votes.add(user_id)
        count = len(votes)
        await ctx.send(f"⏭️ Skip vote added ({count}/{self.skip_threshold})")

        if count >= self.skip_threshold:
            await ctx.send("⏩ Skipping song!")
            vc = self.get_voice_client(ctx)
            if vc and vc.is_playing():
                vc.stop()

    @commands.command()
    async def setskip(self, ctx, threshold: int):
        """Sets the number of votes needed to skip."""
        self.skip_threshold = threshold
        await ctx.send(f"✅ Skip threshold set to {threshold}")

    @commands.command()
    async def leave(self, ctx):
        """Leaves the voice channel."""
        vc = self.get_voice_client(ctx)
        if vc:
            await vc.disconnect()
            self.voice_clients[ctx.guild.id] = None
            await ctx.send("👋 Left the voice channel.")
        else:
            await ctx.send("I'm not in a voice channel.")

async def setup(bot: commands.Bot):
    await bot.add_cog(MusicCog(bot))
    print("MusicCog has been loaded successfully")