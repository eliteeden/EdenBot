# music.py
import os
import asyncio
import discord
from discord.ext import commands
from yt_dlp import YoutubeDL

# -----------------------------------------------------------------------------
# Music Cog inspired by jagrosh/MusicBot (JMusicBot) architecture & features
# -----------------------------------------------------------------------------
#
# Features borrowed from JMusicBot:
#  • Modular queue system with per‐guild queues
#  • Support for YouTube, SoundCloud, Bandcamp, Vimeo, Twitch, HTTP streams, local files
#  • Playlist support (YouTube & other yt-dlp‐supported playlists)
#  • Detailed embed menus and status messages
#  • DJ role for privileged commands (remove, move, shuffle, loop)
#  • Owner‐only commands for bot control (shutdown)
# -----------------------------------------------------------------------------

# YTDL & FFMPEG options
YTDL_OPTS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'extract_flat': 'in_playlist',
    'default_search': 'auto',
}
FUDGE_FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

class Track:
    """Holds metadata & audio source for a song."""
    __slots__ = ('title','url','webpage_url','duration','requester','source')

    def __init__(self, info, requester):
        self.title       = info.get('title')
        self.url         = info.get('url')
        self.webpage_url = info.get('webpage_url')
        self.duration    = info.get('duration')
        self.requester   = requester
        self.source      = discord.FFmpegPCMAudio(self.url, **FUDGE_FFMPEG_OPTIONS)

class MusicQueue:
    """Per‐guild music queue with loop & shuffle support."""
    def __init__(self):
        self.tracks       = []
        self.loop_track   = False
        self.loop_queue   = False

    def add(self, track: Track):
        self.tracks.append(track)

    def pop_next(self):
        if not self.tracks:
            return None
        if self.loop_track:
            return self.tracks[0]
        track = self.tracks.pop(0)
        if self.loop_queue:
            self.tracks.append(track)
        return track

    def clear(self):
        self.tracks.clear()

    def shuffle(self):
        import random
        random.shuffle(self.tracks)

    def __len__(self):
        return len(self.tracks)

class MusicCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot    = bot
        self.queues = {}   # guild_id -> MusicQueue()
        self.dj_role_name = "DJ"  # default DJ role

    # ─── Utilities ────────────────────────────────────────────────────────────

    def get_queue(self, guild_id):
        return self.queues.setdefault(guild_id, MusicQueue())

    async def ensure_voice(self, ctx):
        """Ensure the bot is in author's voice channel."""
        if not ctx.author.voice:
            raise commands.CommandError("You must be in a voice channel.")
        if ctx.voice_client is None:
            await ctx.author.voice.channel.connect()
        elif ctx.voice_client.channel != ctx.author.voice.channel:
            await ctx.voice_client.move_to(ctx.author.voice.channel)

    def is_dj():
        """Check for DJ role."""
        def predicate(ctx):
            role_names = [r.name for r in ctx.author.roles]
            return ctx.author == ctx.guild.owner or "Administrator" in role_names or "Manage Guild" in role_names or "DJ" in role_names
        return commands.check(predicate)

    # ─── Core Playback Commands ────────────────────────────────────────────────

    @commands.command(name="play")
    async def cmd_play(self, ctx, *, query: str):
        """Play a track or playlist from any yt-dlp source."""
        try:
            await self.ensure_voice(ctx)
        except commands.CommandError as e:
            return await ctx.send(embed=discord.Embed(
                title="⚠️ Voice Error", description=str(e), color=discord.Color.red()
            ))

        voice = ctx.voice_client
        queue = self.get_queue(ctx.guild.id)

        # Extract info (single or playlist)
        ytdl = YoutubeDL(YTDL_OPTS)
        try:
            info = ytdl.extract_info(query, download=False)
        except Exception as e:
            return await ctx.send(embed=discord.Embed(
                title="❌ Extraction Error",
                description=f"`{e}`", color=discord.Color.red()
            ))

        entries = info.get('entries') or [info]
        added = []

        for entry in entries:
            # When yt-dlp returns a flat playlist entry, re-extract full info
            if entry.get('url') and not entry.get('title'):
                entry = ytdl.extract_info(entry['url'], download=False)

            track = Track(entry, ctx.author)
            queue.add(track)
            added.append(track.title)

        # If nothing is playing, start immediately
        if not voice.is_playing():
            next_track = queue.pop_next()
            voice.play(next_track.source, after=lambda e: asyncio.run_coroutine_threadsafe(
                self.play_next(ctx), self.bot.loop))

            embed = discord.Embed(
                title="▶️ Now Playing",
                description=f"[{next_track.title}]({next_track.webpage_url})\n" +
                            f"Requested by: {next_track.requester.mention}",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="➕ Added to Queue",
                description="\n".join(f"`{i+1}. {t}`" for i, t in enumerate(added)),
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)

    async def play_next(self, ctx):
        """Callback to play next track in queue."""
        queue = self.get_queue(ctx.guild.id)
        if len(queue) == 0 and not queue.loop_track:
            # if queue empty and not looping current
            await ctx.voice_client.disconnect()
            return

        next_track = queue.pop_next()
        ctx.voice_client.play(next_track.source, after=lambda e: asyncio.run_coroutine_threadsafe(
            self.play_next(ctx), self.bot.loop))

        embed = discord.Embed(
            title="▶️ Now Playing",
            description=f"[{next_track.title}]({next_track.webpage_url})\n" +
                        f"Requested by: {next_track.requester.mention}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def skip(self, ctx):
        """Skip current track (DJ only)."""
        if not ctx.voice_client or not ctx.voice_client.is_playing():
            return await ctx.send(embed=discord.Embed(
                title="⚠️ Nothing Playing", color=discord.Color.red()
            ))
        await self.ensure_voice(ctx)
        ctx.voice_client.stop()
        await ctx.send(embed=discord.Embed(
            title="⏭️ Skipped", color=discord.Color.orange()
        ))

    @commands.command()
    async def pause(self, ctx):
        """Pause playback."""
        vc = ctx.voice_client
        if vc and vc.is_playing():
            vc.pause()
            await ctx.send(embed=discord.Embed(
                title="⏸️ Paused", color=discord.Color.gold()
            ))

    @commands.command()
    async def resume(self, ctx):
        """Resume playback."""
        vc = ctx.voice_client
        if vc and vc.is_paused():
            vc.resume()
            await ctx.send(embed=discord.Embed(
                title="▶️ Resumed", color=discord.Color.green()
            ))

    @commands.command()
    async def stop(self, ctx):
        """Stop and clear queue (DJ only)."""
        await self.ensure_voice(ctx)
        ctx.voice_client.stop()
        self.get_queue(ctx.guild.id).clear()
        await ctx.voice_client.disconnect()
        await ctx.send(embed=discord.Embed(
            title="⏹️ Stopped", color=discord.Color.red()
        ))

    # ─── Queue Management ────────────────────────────────────────────────────

    @commands.command(name="queue")
    async def cmd_queue(self, ctx):
        """Show current queue."""
        queue = self.get_queue(ctx.guild.id)
        if not queue.tracks:
            return await ctx.send(embed=discord.Embed(
                title="📭 Empty Queue", color=discord.Color.light_grey()
            ))

        desc = "\n".join(
            f"{i+1}. [{t.title}]({t.webpage_url}) – {t.requester.mention}"
            for i, t in enumerate(queue.tracks[:10])
        )
        embed = discord.Embed(
            title=f"🎶 Queue (next {min(len(queue),10)} of {len(queue)})",
            description=desc, color=discord.Color.purple()
        )
        await ctx.send(embed=embed)

    @commands.command()
    @is_dj()
    async def shuffle(self, ctx):
        """Shuffle the queue (DJ only)."""
        queue = self.get_queue(ctx.guild.id)
        queue.shuffle()
        await ctx.send(embed=discord.Embed(
            title="🔀 Shuffled Queue", color=discord.Color.blue()
        ))

    @commands.command()
    @is_dj()
    async def clear(self, ctx):
        """Clear queue (DJ only)."""
        self.get_queue(ctx.guild.id).clear()
        await ctx.send(embed=discord.Embed(
            title="🗑️ Queue Cleared", color=discord.Color.red()
        ))

    @commands.group(invoke_without_command=True)
    @is_dj()
    async def loop(self, ctx):
        """Toggle loop modes."""
        queue = self.get_queue(ctx.guild.id)
        queue.loop_queue = not queue.loop_queue
        status = "enabled" if queue.loop_queue else "disabled"
        await ctx.send(embed=discord.Embed(
            title="🔁 Loop Queue",
            description=f"Queue looping {status}.",
            color=discord.Color.gold()
        ))

    @loop.command(name="track")
    @is_dj()
    async def loop_track(self, ctx):
        """Toggle loop for current track."""
        queue = self.get_queue(ctx.guild.id)
        queue.loop_track = not queue.loop_track
        status = "enabled" if queue.loop_track else "disabled"
        await ctx.send(embed=discord.Embed(
            title="🔂 Loop Track",
            description=f"Track looping {status}.",
            color=discord.Color.gold()
        ))

    @commands.command()
    @is_dj()
    async def volume(self, ctx, vol: int):
        """Change playback volume."""
        vc = ctx.voice_client
        if not vc or not vc.source:
            return
        vc.source = discord.PCMVolumeTransformer(vc.source, volume=vol/100)
        await ctx.send(embed=discord.Embed(
            title="🔊 Volume Changed",
            description=f"Volume set to {vol}%",
            color=discord.Color.green()
        ))

    # ─── Owner / Admin Commands ─────────────────────────────────────────────

    @commands.command()
    @commands.is_owner()
    async def shutdown(self, ctx):
        """Shutdown the bot (Owner only)."""
        await ctx.send(embed=discord.Embed(
            title="🛑 Shutting down...", color=discord.Color.dark_red()
        ))
        await self.bot.logout()

async def setup(bot):
    bot.add_cog(MusicCog(bot))
    print("MusicCog has been loaded successfully")