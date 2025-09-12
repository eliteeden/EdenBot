import discord
from discord.ext import commands
import re

from constants import ROLES


class RolesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def createrole(self, ctx, name: str, color: str = None, above_role_id: int = None):
        """
        Create a role with optional color and position.
        Usage:
        - ;createrole RoleName #FF5733 123456789012345678
        - ;createrole RoleName blue
        """
        guild = ctx.guild

        try:
            # Resolve color using ColorCog
            if color is None:
                role_color = discord.Color.default()
            else:
                color = color.strip().lower()
                if not color.startswith("#") and len(color) <= 20:
                    # Assume it's a name, resolve to hex
                    color_cog = ctx.bot.get_cog("ColorCog")
                    if color_cog:
                        hex_code = color_cog.color_to_hex(color)
                        if hex_code and hex_code != "Unknown hex":
                            color = hex_code
                        else:
                            await ctx.send("❌ Couldn't resolve that color name.")
                            return
                    else:
                        await ctx.send("❌ ColorCog is not loaded.")
                        return

                # Strip '#' and convert to discord.Color
                hex_clean = color.lstrip("#")
                try:
                    role_color = discord.Color(int(hex_clean, 16))
                except ValueError:
                    await ctx.send("❌ Invalid hex code.")
                    return

            # Determine position
            if above_role_id is None:
                above_role_id = guild.roles[-1].id

            above_role = guild.get_role(above_role_id)
            if not above_role:
                return await ctx.send("❌ Role with that ID not found.")

            new_position = above_role.position + 1

            # Create and move role
            new_role = await guild.create_role(
                name=name, color=role_color, reason=f"Created by {ctx.author}"
            )
            await guild.edit_role_positions(positions={new_role: new_position})

            await ctx.send(
                f"✅ Created role **{new_role.name}** above **{above_role.name}** with color `{color}`."
            )

        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to manage or move roles.")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Failed to create or move role: {e}") 
    @commands.command(name="reorderrole", aliases=["reorder", "moverole", "raiserole", "raise"])
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def reorderrole(self, ctx, role: discord.Role, second_role: discord.Role):
        """
        Reorder a role to be above another role.
        Usage:
          - ;reorderrole @Role1 @Role2
        """
        guild = ctx.guild
        me = guild.me

        if role.id == guild.id:
            return await ctx.send("You cannot reorder the @everyone role.")
        if second_role.id == guild.id:
            return await ctx.send("You cannot reorder the @everyone role.")

        if role.managed or second_role.managed:
            return await ctx.send("Managed roles cannot be reordered.")

        if (
            role.position >= me.top_role.position
            or second_role.position >= me.top_role.position
        ):
            return await ctx.send(
                "I cannot reorder roles that are above or equal to my top role."
            )

        try:
            # Reorder the roles
            await guild.edit_role_positions(positions={role: second_role.position + 1})
            await ctx.send(f"✅ Moved **{role.name}** above **{second_role.name}**.")
        except discord.Forbidden:
            await ctx.send("I don't have permission to manage roles.")
        except discord.HTTPException as e:
            await ctx.send(f"Failed to reorder roles: {e}")

    @commands.command(name="add_role", aliases=["addrole", "giverole", "assign"])
    @commands.has_any_role(ROLES.MODERATOR, ROLES.PRESIDENT)
    async def add_role(self, ctx, member: discord.Member, role: discord.Role):
        """
        Add a role to a member.
        Usage:
          - ;add_role @Member @Role
        """
        if role in member.roles:
            await ctx.send(f"{member.mention} already has the role {role.name}.")

        else:
            try:
                await member.add_roles(
                    role, reason=f"Role added by {ctx.author} ({ctx.author.id})"
                )
                await ctx.send(f"✅ Added role **{role.name}** to {member.mention}.")
            except discord.Forbidden:
                await ctx.send("I don't have permission to add that role.")
            except discord.HTTPException as e:
                await ctx.send(f"Failed to add role: {e}")

    @commands.command(name="bulk_add_role", aliases=["massrole", "addroles", "bulkassign", "bulkadd"])
    @commands.has_any_role(ROLES.MODERATOR, ROLES.PRESIDENT)
    async def bulk_add_role(self, ctx, role: discord.Role, *args):
        async with ctx.typing():
            """
            Add a role to multiple members using mentions or user IDs.
            Usage:
            - ;bulk_add_role @Role @User1 @User2 ...
            - ;bulk_add_role @Role 123456789012345678 987654321098765432 ...
            """
            if not args:
                await ctx.send("❌ You must provide at least one member (mention or ID).")
                return

            success = []
            already_has = []
            failed = []

            for arg in args:
                try:
                    # Try to resolve as mention or ID
                    member = await commands.MemberConverter().convert(ctx, arg)
                except commands.BadArgument:
                    failed.append((arg, "User not found"))
                    continue

                if role in member.roles:
                    already_has.append(member)
                    continue

                try:
                    await member.add_roles(
                        role, reason=f"Bulk role added by {ctx.author} ({ctx.author.id})"
                    )
                    success.append(member)
                except discord.Forbidden:
                    failed.append((member.mention, "Missing permissions"))
                except discord.HTTPException as e:
                    failed.append((member.mention, f"HTTP error: {e}"))

            # Build response
            response = []

            if success:
                response.append(f"✅ Added **{role.name}** to: " + ", ".join(m.mention for m in success))
            if already_has:
                response.append(f"ℹ️ Already had **{role.name}**: " + ", ".join(m.mention for m in already_has))
            if failed:
                response.append("❌ Failed to add role to:")
                for m, reason in failed:
                    response.append(f"  - {m}: {reason}")

            await ctx.send("\n".join(response))             

    @commands.command(name="bulk_remove_role", aliases=["massremoverole", "removeroles", "bulkremove"])
    @commands.has_any_role(ROLES.MODERATOR, ROLES.PRESIDENT)
    async def bulk_remove_role(self, ctx, role: discord.Role, *args):
        async with ctx.typing():
            """
            Remove a role from multiple members using mentions or user IDs.
            Usage:
            - ;bulk_remove_role @Role @User1 @User2 ...
            - ;bulk_remove_role @Role 123456789012345678 987654321098765432 ...
            """
            if not args:
                await ctx.send("❌ You must provide at least one member (mention or ID).")
                return

            removed = []
            not_has_role = []
            failed = []

            for arg in args:
                try:
                    member = await commands.MemberConverter().convert(ctx, arg)
                except commands.BadArgument:
                    failed.append((arg, "User not found"))
                    continue

                if role not in member.roles:
                    not_has_role.append(member)
                    continue

                try:
                    await member.remove_roles(
                        role, reason=f"Bulk role removed by {ctx.author} ({ctx.author.id})"
                    )
                    removed.append(member)
                except discord.Forbidden:
                    failed.append((member.mention, "Missing permissions"))
                except discord.HTTPException as e:
                    failed.append((member.mention, f"HTTP error: {e}"))

            # Build response
            response = []

            if removed:
                response.append(f"✅ Removed **{role.name}** from: " + ", ".join(m.mention for m in removed))
            if not_has_role:
                response.append(f"ℹ️ Didn't have **{role.name}**: " + ", ".join(m.mention for m in not_has_role))
            if failed:
                response.append("❌ Failed to remove role from:")
                for m, reason in failed:
                    response.append(f"  - {m}: {reason}")

            await ctx.send("\n".join(response))   

    @commands.command(name="remove_role", aliases=["removerole", "unassign"])
    @commands.has_any_role(ROLES.MODERATOR, ROLES.PRESIDENT)
    async def remove_role(self, ctx, member: discord.Member, role: discord.Role):
        """
        Remove a role from a member.
        Usage:
          - ;remove_role @Member @Role
        """
        if role not in member.roles:
            await ctx.send(f"{member.mention} does not have the role {role.name}.")
        else:
            try:
                await member.remove_roles(
                    role, reason=f"Role removed by {ctx.author} ({ctx.author.id})"
                )
                await ctx.send(
                    f"✅ Removed role **{role.name}** from {member.mention}."
                )
            except discord.Forbidden:
                await ctx.send("I don't have permission to remove that role.")
            except discord.HTTPException as e:
                await ctx.send(f"Failed to remove role: {e}")

    @commands.command(
        name="delete_roles", aliases=["deleteroles", "delroles", "delrole"]
    )
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def delete_roles(self, ctx, *, query: str):
        """
        Delete roles by exact name (case-insensitive) or a specific role by ID/mention.
        Usage:
          - ;delete_roles Moderators
          - ;delete_roles 123456789012345678
          - ;delete_roles @Moderators
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
                return await ctx.send(
                    f"`{target.name}` is managed by an integration and cannot be deleted."
                )
            if target.position >= me.top_role.position:
                return await ctx.send(
                    f"My top role is not high enough to delete `{target.name}`."
                )

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
            # Nothing deletable! report the reasons
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
            msg_lines.append(
                f"Deleted {len(deleted)} role(s): "
                + ", ".join(f"`{r.name}` ({r.id})" for r in deleted)
            )
        if skipped:
            msg_lines.append(
                f"Skipped {len(skipped)} role(s): "
                + ", ".join(f"`{r.name}` ({r.id}) — {why}" for r, why in skipped)
            )

        await ctx.send("\n".join(msg_lines) if msg_lines else "Nothing to report.")

    @commands.command(name="changerolecolor", aliases=["setrolecolor", "rolecolor", "hexrole", "prettify"])
    @commands.has_permissions(manage_roles=True)
    async def changerolecolor(self, ctx, role: discord.Role, color: str):
        """
        Change the color of an existing role.
        Usage:
        - ;changerolecolor @Role #FF5733
        - ;changerolecolor @Role blue
        """
        try:
            # Resolve color using ColorCog
            color = color.strip().lower()
            if not color.startswith("#") and len(color) <= 20:
                # Assume it's a name, resolve to hex
                color_cog = ctx.bot.get_cog("ColorCog")
                if color_cog:
                    hex_code = color_cog.color_to_hex(color)
                    if hex_code and hex_code != "Unknown hex":
                        color = hex_code
                    else:
                        await ctx.send("❌ Couldn't resolve that color name.")
                        return
                else:
                    await ctx.send("❌ ColorCog is not loaded.")
                    return

            # Convert hex to discord.Color
            hex_clean = color.lstrip("#")
            try:
                new_color = discord.Color(int(hex_clean, 16))
            except ValueError:
                await ctx.send("❌ Invalid hex code.")
                return

            # Apply the color change
            await role.edit(color=new_color, reason=f"Color changed by {ctx.author}")
            await ctx.send(f"✅ Changed color of **{role.name}** to `{color}`.")

        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to edit that role.")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Failed to change role color: {e}")

    @commands.command(name="oneoff", aliases=["acr"])
    @commands.has_permissions(manage_roles=True)
    async def assign_roles(self, ctx):
        guild = ctx.guild

        # Replace these with your actual role IDs
        ROLE_A_ID = 997361025772965918
        ROLE_1_ID = 995017153168289884
        ROLE_2_ID = 995017251319185469
        ROLE_3_ID = 995017400602865725
        TARGET_ROLE_ID = 1408704187700609056

        # Fetch role objects by ID
        role_a = guild.get_role(ROLE_A_ID)
        role_1 = guild.get_role(ROLE_1_ID)
        role_2 = guild.get_role(ROLE_2_ID)
        role_3 = guild.get_role(ROLE_3_ID)
        target_role = guild.get_role(TARGET_ROLE_ID)

        if not all([role_a, role_1, role_2, role_3, target_role]):
            await ctx.send("One or more roles not found. Check the role IDs.")
            return

        count = 0
        for member in guild.members:
            if role_a in member.roles and any(r in member.roles for r in [role_1, role_2, role_3]):
                if target_role not in member.roles:
                    try:
                        await member.add_roles(target_role)
                        count += 1
                    except discord.Forbidden:
                        await ctx.send(f"Missing permissions to assign role to {member.display_name}")
                    except discord.HTTPException as e:
                        await ctx.send(f"Failed to assign role to {member.display_name}: {e}")

        await ctx.send(f"✅ Assigned '{target_role.name}' to {count} members.")


#This cog was made because we are lazy as fuck
async def setup(bot: commands.Bot):
    """Load the RolesCog cog."""
    await bot.add_cog(RolesCog(bot))
    print("RolesCog has been loaded successfully.")
