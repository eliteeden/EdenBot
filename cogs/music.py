# cogs/music.py

import os
import discord
import asyncio
import yt_dlp
from discord.ext import commands
from dotenv import load_dotenv

MY_GUILD = discord.Object(id=963743538212900904)

ytdl_opts = {
    "format": "bestaudio/best",
    "quiet": True,
    "default_search": "auto",
    "noplaylist": True,
}
ffmpeg_opts = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}
ytdl = yt_dlp.YoutubeDL(ytdl_opts)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data  = data
        self.title = data.get("title")

    @classmethod
    async def from_url(cls, url: str, *, loop=None, stream=True):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(
            None, lambda: ytdl.extract_info(url, download=not stream)
        )
        if "entries" in data:
            data = data["entries"][0]
        filename = data["url"] if stream else ytdl.prepare_filename(data)
        source   = discord.FFmpegPCMAudio(filename, **ffmpeg_opts)
        return cls(source, data=data)

class MusicCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_client: discord.VoiceClient | None = None

    async def _connect(self, interaction: discord.Interaction) -> discord.VoiceClient | None:
        """Helper: connect to the user's VC, or return existing."""
        channel = getattr(interaction.user.voice, "channel", None)
        if not channel:
            await interaction.response.send_message(
                "You must be in a voice channel.", ephemeral=True
            )
            return None

        if self.voice_client and self.voice_client.is_connected():
            return self.voice_client

        try:
            vc = await channel.connect()
            self.voice_client = vc
            return vc
        except Exception as e:
            await interaction.response.send_message(f"❌ Could not join: {e}")
            return None

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.tree.copy_global_to(guild=MY_GUILD)
        await self.bot.tree.sync(guild=MY_GUILD)

    @commands.command(name="join", description="Join your voice channel")
    @commands.guilds(MY_GUILD)
    async def join(self, interaction: discord.Interaction):
        vc = await self._connect(interaction)
        if vc:
            await interaction.response.send_message(f"🎶 Joined {vc.channel.name}")

    @commands.command(
        name="play",
        description="Stream audio from YouTube (URL or search term)",
    )
    @commands.describe(url="YouTube link or search keywords")
    @commands.guilds(MY_GUILD)
    async def play(self, interaction: discord.Interaction, url: str):
        # 1) Connect or early‐exit
        vc = await self._connect(interaction)
        if not vc:
            return

        # 2) Acknowledge long op
        await interaction.response.defer()

        # 3) Fetch stream
        try:
            source = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
        except Exception as e:
            return await interaction.followup.send(f"❌ Failed to load audio: {e}")

        # 4) Play & report
        vc.play(source, after=lambda err: print(f"Player error: {err}") if err else None)
        await interaction.followup.send(f"▶️ Now playing **{source.title}**")

    @commands.command(name="leave", description="Disconnect from voice")
    @commands.guilds(MY_GUILD)
    async def leave(self, interaction: discord.Interaction):
        if self.voice_client and self.voice_client.is_connected():
            await self.voice_client.disconnect()
            self.voice_client = None
            await interaction.response.send_message("👋 Left the voice channel.")
        else:
            await interaction.response.send_message(
                "I’m not connected to any voice channel.", ephemeral=True
            )

async def setup(bot: commands.Bot):
    await bot.add_cog(MusicCog(bot))