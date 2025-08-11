
import discord
from discord.ext import commands
import re

class RolesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    # Has the phone error am i right?
    async def createrole(self, ctx, name: str, color: discord.Color=None, above_role_id: int=None):
        guild = ctx.guild
        try:
            if color is None:
                color = discord.Color.default()
            if above_role_id is None:
                above_role_id = guild.roles[-1].id

            # Get the role to place the new role above
            above_role = guild.get_role(above_role_id)
            if not above_role:
                return await ctx.send("Role with that ID not found.")

            # Calculate new position
            new_position = above_role.position + 1

            # Create the role
            new_role = await guild.create_role(name=name, color=color, reason=f"Created by {ctx.author}")

            # Move the role to the desired position
            await ctx.guild.edit_role_positions(positions={new_role:new_position})

            await ctx.send(f"✅ Created role **{new_role.name}** above **{above_role.name}**.")
        except discord.Forbidden:
            await ctx.send("I don't have permission to manage roles or move that role.")
        except discord.HTTPException as e:
            await ctx.send(f"Failed to create or move role: {e}")


    @commands.command(name="delete_roles", aliases=["deleteroles", "delroles", 'delrole'])
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def delete_roles(self, ctx, *, query: str):
        """
        Delete roles by exact name (case-insensitive) or a specific role by ID/mention.
        Usage:
          - !delete_roles Moderators
          - !delete_roles 123456789012345678
          - !delete_roles @Moderators
        """
        guild = ctx.guild
        me = guild.me
        reason = f"Requested by {ctx.author} ({ctx.author.id}) via delete_roles"

        # Try to interpret as role mention or ID first
        role_id = None
        q = query.strip()

        mention_match = re.fullmatch(r"<@&(\d+)>", q)
        if mention_match:
            role_id = int(mention_match.group(1))
        elif q.isdigit():
            # Only treat as ID if it actually resolves to a role
            maybe_role = guild.get_role(int(q))
            if maybe_role:
                role_id = maybe_role.id

        deleted = []
        skipped = []

        if role_id is not None:
            # Delete the single resolved role
            target = guild.get_role(role_id)
            if not target:
                return await ctx.send("No role found with that ID.")
            # Skip checks
            if target.id == guild.id:
                return await ctx.send("You cannot delete the @everyone role.")
            if target.managed:
                return await ctx.send(f"`{target.name}` is managed by an integration and cannot be deleted.")
            if target.position >= me.top_role.position:
                return await ctx.send(f"My top role is not high enough to delete `{target.name}`.")

            try:
                await target.delete(reason=reason)
                return await ctx.send(f"Deleted role `{target.name}` ({target.id}).")
            except discord.Forbidden:
                return await ctx.send("I don't have permission to delete that role.")
            except discord.HTTPException as e:
                return await ctx.send(f"Failed to delete role: {e}")

        # Otherwise: treat as name (case-insensitive exact match), delete all matches
        matches = [r for r in guild.roles if r.name.lower() == q.lower()]

        if not matches:
            return await ctx.send("No roles found with that name.")

        # Filter out roles we can't/shouldn't delete, keeping track of why
        def can_delete(role: discord.Role) -> bool:
            if role.id == guild.id:
                skipped.append((role, "@everyone cannot be deleted"))
                return False
            if role.managed:
                skipped.append((role, "managed by integration"))
                return False
            if role.position >= me.top_role.position:
                skipped.append((role, "above or equal to my top role"))
                return False
            return True

        to_delete = [r for r in matches if can_delete(r)]

        if not to_delete:
            # Nothing deletable; report the reasons
            lines = [f"Found {len(matches)} matching role(s), but none can be deleted:"]
            for role, why in skipped:
                lines.append(f"- `{role.name}` ({role.id}): {why}")
            return await ctx.send("\n".join(lines))

        # Delete roles sequentially
        for role in to_delete:
            try:
                await role.delete(reason=reason)
                deleted.append(role)
            except discord.Forbidden:
                skipped.append((role, "permission denied"))
            except discord.HTTPException as e:
                skipped.append((role, f"HTTP error: {e}"))

        # Build a concise report
        msg_lines = []
        if deleted:
            msg_lines.append(f"Deleted {len(deleted)} role(s): " +
                             ", ".join(f"`{r.name}` ({r.id})" for r in deleted))
        if skipped:
            msg_lines.append(f"Skipped {len(skipped)} role(s): " +
                             ", ".join(f"`{r.name}` ({r.id}) — {why}" for r, why in skipped))

        await ctx.send("\n".join(msg_lines) if msg_lines else "Nothing to report.")


async def setup(bot):
    """Load the RolesCog cog."""
    await bot.add_cog(RolesCog(bot))
    print("RolesCog has been loaded successfully.")