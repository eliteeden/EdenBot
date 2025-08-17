import discord
from discord.ext import commands


class UnintroducedRemover(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.channel_id = 963820477585981500  # Replace with your channel ID
        self.role_id = 1065945165874876487  # Replace with your role ID
        self.max_nick_length = 32  # Discord's nickname length limit

    @commands.Cog.listener()
async def on_message(self, message):
    valid_triggers = ["➸Nickname:", "Name:", "➸Nickname"]

    if message.author.bot:
        return

    if message.channel.id == self.channel_id and any(trigger in message.content for trigger in valid_triggers):
        guild = message.guild
        member = message.author
        role = guild.get_role(self.role_id)

        try:
            # Find the first line containing a valid trigger
            name_line = next(
                (line for line in message.content.splitlines() if any(trigger in line for trigger in valid_triggers)),
                None
            )

            new_name = member.name  # Default fallback

            if name_line:
                for trigger in valid_triggers:
                    if trigger in name_line:
                        extracted = name_line.split(trigger, 1)[1].strip()
                        if len(extracted) <= self.max_nick_length:
                            new_name = extracted
                        break

                await member.edit(nick=new_name)
                await message.channel.send(
                    f"{member.mention}'s nickname updated to `{new_name}`."
                )
            else:
                await message.channel.send(
                    f"No valid nickname line found in {member.mention}'s message."
                )

        except Exception as e:
            await message.channel.send(
                f"Could not update nickname for {member.mention}. Error: `{type(e).__name__}: {e}`"
            )

        if role in member.roles:
            await member.remove_roles(role)
            await message.channel.send(f"Role removed from {member.display_name}.")

# Setup function to add the Cog
async def setup(bot: commands.Bot):
    await bot.add_cog(UnintroducedRemover(bot))
    print("IntroCog has been loaded.")
