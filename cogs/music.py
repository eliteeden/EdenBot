Happy
.hapiy
In voice

Cootshk

 — Yesterday at 20:14
happy is typing…
Happy

 — Yesterday at 20:14
so many ppl are gonna be accepted lowk
Cootshk

 — Yesterday at 20:14
oh god
Happy

 — Yesterday at 20:15
yeah
which is why i was so strict in the requirements
i dont want any deadweight
no offense
Cootshk

 — Yesterday at 20:36
help
Image
Happy

 — Yesterday at 20:36
wha
pfft
it's one channel you don't even have access to
Cootshk

 — Yesterday at 20:37
remove my access?
wait
idk
if you remove my role can I see eden again
https://support.discord.com/hc/en-us/articles/1500005389362-Age-restricted-Server-Designation appeal the server?
I see the ping but can’t view it
Happy

 — Yesterday at 20:41
how about now
Cootshk

 — Yesterday at 20:51
Forwarded
Image
i think discord is broken
Happy

 — Yesterday at 20:51
what is dxxxxxxy studio
Cootshk

 — Yesterday at 20:52
support server for https://github.com/prometheusreengineering that I work on
GitHub
Prometheus Reengineering
Prometheus Reengineering has 3 repositories available. Follow their code on GitHub.
Prometheus Reengineering
Happy

 — Yesterday at 20:52
why is it age restricted
Cootshk

 — Yesterday at 20:53
might be it?
Image
Cootshk

 — Yesterday at 20:53
idfk
Happy

 — Yesterday at 20:53
yeah
the channel is already private
and we removed the age restrcition
maybe it'll be fine by tmrw
Cootshk

 — Yesterday at 20:54
can you put the age restriction back i think its because i previously had access to the channel
Cootshk

 — 21:22
I see a ping from you in eden but I can’t read it
Happy

 — 21:22
Image
Cootshk

 — 21:23
bruh
pi crash
is the bot ;pinging
Happy

 — 21:26
yes
Cootshk

 — 21:26
uhm
I really should make a command to reload ttyd
Happy

 — 21:27
you really should
add it to your backlog
Cootshk

 — 21:28
It’s rebooting, give it 2-3 business minutes
Happy

 — 22:12
Forwarded
import discord
from discord.ext import commands
import asyncio
import yt_dlp

class MusicCog(commands.Cog):
Expand
music.py
6 KB

・❥・elite eden | ʚїɞ | 🎃💀  •  22:12
so the bot keeps leaving and rejoining
for context i did 
pip install yt_dlp

sudo apt install ffmpeg

pip install {something}Nacl
Cootshk

 — 22:20
ytdlp is apt not pip
Happy

 — 22:21
ohh
is there anything else im missing
COOTSHK
what am i missing
Cootshk

 — 22:58
once I get to my laptop I’ll check
﻿
Cootshk
cootshk
Please @ in replies

 
 
 
 
 
 
 
When you deliberately distort and selectively present the truth, you lie.

If you take away what a person owns, you control what that person can do.

Rest in peace, Charlie Kirk.
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