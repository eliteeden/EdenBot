import discord
from discord.ext import commands
import asyncio
import yt_dlp

class MusicCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot            = bot
        self.queues         = {}      # guild_id -> list of URLs
        self.currents       = {}      # guild_id -> current URL
        self.skip_votes     = {}      # guild_id -> set(user_id)
        self.skip_threshold = 2

    def get_queue(self, ctx):
        return self.queues.setdefault(ctx.guild.id, [])

    def get_skip_votes(self, ctx):
        return self.skip_votes.setdefault(ctx.guild.id, set())

    async def _ensure_voice(self, ctx) -> discord.VoiceClient | None:
        """Join the author’s voice channel or move there if already connected elsewhere."""
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("❌ You’re not in a voice channel.")
            return None

        vc = ctx.guild.voice_client
        target = ctx.author.voice.channel

        if vc is None:
            try:
                return await target.connect()
            except Exception as e:
                await ctx.send(f"❌ Could not connect: {e}")
                return None

        if vc.channel.id != target.id:
            try:
                return await vc.move_to(target)
            except Exception as e:
                await ctx.send(f"❌ Could not move: {e}")
                return None

        return vc

    @commands.command(name="join")
    async def join(self, ctx):
        """Joins (or moves to) your voice channel."""
        vc = await self._ensure_voice(ctx)
        if vc:
            await ctx.send(f"🎶 Joined **{vc.channel.name}**")

    @commands.command(name="play")
    async def play(self, ctx, *, url: str):
        """Enqueue & play from YouTube (or search)."""
        vc = await self._ensure_voice(ctx)
        if not vc:
            return

        queue = self.get_queue(ctx)
        queue.append(url)
        await ctx.send(f"🎵 Added to queue: {url}")

        if not vc.is_playing():
            await self._play_next(ctx)

    async def _play_next(self, ctx):
        queue = self.get_queue(ctx)
        vc    = ctx.guild.voice_client

        if not vc or not vc.is_connected():
            await ctx.send("❌ Not connected to voice.")
            return

        if not queue:
            # don’t disconnect—just stay idle
            await ctx.send("⏹ Queue empty. Waiting for more tracks.")
            return

        self.get_skip_votes(ctx).clear()
        self.currents[ctx.guild.id] = queue.pop(0)

        ydl_opts = {
            "format": "bestaudio/best",
            "quiet": True,
            "default_search": "auto",
            "noplaylist": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.currents[ctx.guild.id], download=False)
                if "entries" in info:
                    info = info["entries"][0]
                stream_url = info["url"]
                title      = info.get("title", "Unknown")
        except Exception as e:
            await ctx.send(f"❌ yt-dlp error: {e}")
            return

        def _after_play(err):
            if err:
                print(f"[MusicCog] Player error: {err}")
            fut = self._play_next(ctx)
            asyncio.run_coroutine_threadsafe(fut, self.bot.loop)

        try:
            source = discord.FFmpegPCMAudio(
                stream_url,
                before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                options="-vn"
            )
            vc.play(source, after=_after_play)
            await ctx.send(f"▶️ Now playing: **{title}**")
        except Exception as e:
            await ctx.send(f"❌ Playback failed: {e}")

    @commands.command(name="skip")
    async def skip(self, ctx):
        """Vote to skip the current track."""
        votes = self.get_skip_votes(ctx)
        user  = ctx.author.id

        if user in votes:
            return await ctx.send("❌ You’ve already voted to skip.")

        votes.add(user)
        count = len(votes)
        await ctx.send(f"⏭ Skip vote: **{count}/{self.skip_threshold}**")

        if count >= self.skip_threshold:
            await ctx.send("⏩ Skipping song!")
            vc = ctx.guild.voice_client
            if vc and vc.is_playing():
                vc.stop()

    @commands.command(name="setskip")
    async def setskip(self, ctx, threshold: int):
        """Define how many votes are needed to skip."""
        self.skip_threshold = threshold
        await ctx.send(f"✅ Skip threshold set to **{threshold}**")

    @commands.command(name="leave")
    async def leave(self, ctx):
        """Disconnect from voice (but keep your queue)."""
        vc = ctx.guild.voice_client
        if vc:
            await vc.disconnect()
            await ctx.send("👋 Left voice channel.")
        else:
            await ctx.send("❌ I’m not connected to any voice channel.")

async def setup(bot: commands.Bot):
    await bot.add_cog(MusicCog(bot))
    print("[MusicCog] loaded successfully")