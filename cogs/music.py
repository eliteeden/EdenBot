
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
        """Joins the voice channel and returns the voice client."""
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            existing_vc = self.get_voice_client(ctx)
            if existing_vc and existing_vc.is_connected():
                await ctx.send("Already connected to a voice channel.")
                return existing_vc
            try:
                vc = await channel.connect()
                self.voice_clients[ctx.guild.id] = vc
                await ctx.send(f"🎶 Joined {channel.name}")
                return vc
            except Exception as e:
                await ctx.send(f"❌ Failed to join: {e}")
                return None
        else:
            await ctx.send("You're not in a voice channel!")
            return None
            
    @commands.command()
    async def play(self, ctx, *, url: str):
        """Plays a song or playlist from YouTube or Spotify."""
        vc = self.get_voice_client(ctx)
        if not vc or not vc.is_connected():
            vc = await self.join(ctx)

        if not vc or not vc.is_connected():
            await ctx.send("❌ Could not connect to voice channel.")
            return

        self.get_queue(ctx).append(url)
        await ctx.send(f"🎵 Added to queue: {url}")

        if not vc.is_playing():
            await self._play_next(ctx)
            
    async def _play_next(self, ctx):
        queue = self.get_queue(ctx)
        vc = self.get_voice_client(ctx)

        if not vc or not vc.is_connected():
            await ctx.send("❌ Not connected to a voice channel.")
            return

        if not queue:
            await ctx.send("Queue is empty. Staying in channel.")
            return

        self.get_skip_votes(ctx).clear()
        self.currents[ctx.guild.id] = queue.pop(0)

        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'default_search': 'auto',
            'noplaylist': True,
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

        try:
            source = discord.FFmpegPCMAudio(
                stream_url,
                before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                options="-vn"
            )
            vc.play(source, after=after_playing)
            await ctx.send(f"▶️ Now playing: {title}")
        except Exception as e:
            await ctx.send(f"❌ Playback failed: {e}")

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