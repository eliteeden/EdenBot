import discord
from discord.ext import commands

class UnintroducedRemover(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.channel_id = 963820477585981500  # Replace with your channel ID
        self.role_id = 1065945165874876487     # Replace with your role ID
        self.max_nick_length = 32              # Discord's nickname length limit

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if message.channel.id == self.channel_id and "➸Nickname:" in message.content:
            guild = message.guild
            member = message.author
            role = guild.get_role(self.role_id)

            # Search for "➸Nickname:" line only
            try:
                name_line = next((line for line in message.content.splitlines() if "➸Nickname:" in line), None)
                if name_line:
                    extracted = name_line.split("➸Nickname:", 1)[1].strip()
                    new_name = extracted if len(extracted) <= self.max_nick_length else member.name

                    await member.edit(nick=new_name)
                    await message.channel.send(f"{member.mention}'s nickname updated to `{new_name}`.")
                else:
                    await message.channel.send(f"No valid '➸Nickname:' line found in {member.mention}'s message.")

            except Exception as e:
                await message.channel.send(f"Could not update nickname for {member.mention}. Error: `{e}`")

            if role in member.roles:
                await member.remove_roles(role)
                await message.channel.send(f"Role removed from {member.display_name}.")

# Setup function to add the Cog
async def setup(bot: commands.Bot):
    await bot.add_cog(UnintroducedRemover(bot))
    print("IntroCog has been loaded.")