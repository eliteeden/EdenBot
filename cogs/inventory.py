import json
from typing import Optional
import discord
from discord.ext import commands

from constants import ROLES

class InventoryCog(commands.Cog):
    """Cog for managing user inventories."""
    INVENTORY_FILE = "inventories.json"
    type strint = str
    """Alias for str, used for member IDs"""
    type MemberLike = discord.User | discord.Member | int | str | strint
    """Any Member-like object, such as a User, Member, int (ID), or str (ID)"""
    type Item = str
    """The stringified ID of an item"""
    type ItemAmount = dict[Item, int]
    """A mapping of a user's items to amounts"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.inventories: dict["InventoryCog.strint", InventoryCog.ItemAmount] = self.__load_inventories()
    def __save_inventories(self):
        """Save the inventories to a file."""
        with open(self.INVENTORY_FILE, 'w') as f:
            json.dump(self.inventories, f, indent=4)
    def __load_inventories(self) -> dict["InventoryCog.strint", "InventoryCog.ItemAmount"]:
        """Load the inventories from a file."""
        try:
            with open(self.INVENTORY_FILE, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            print("Error decoding JSON from inventory file. Starting with an empty inventory.")
            return {}
    def get_id(self, member: MemberLike) -> strint:
        if member is None or member == "users":
            return "0"
        if isinstance(member, (discord.User, discord.Member)):
            return str(member.id)
        elif isinstance(member, int):
            return str(member)
        elif isinstance(member, str):
            member = member.lower()
            if member.startswith("<@") and member.endswith(">"):
                return member[2:-1]
            else:
                try: 
                    return str(int(member))  # If it's a string that can be converted to an int
                except ValueError:
                    for m in self.bot.get_all_members():
                        if member == m.name.lower() or member == m.display_name.lower():
                            return str(m.id)
        raise ValueError(f"Invalid member type (got: {member} of type {type(member)})")
    def get_inventory(self, user: MemberLike) -> ItemAmount:
        """Get the inventory for a user."""
        user_id = self.get_id(user)
        if user_id not in self.inventories:
            self.inventories[user_id] = {}
        return self.inventories[user_id]
    def add_item(self, user: MemberLike, item: Item, amount: int = 1) -> int:
        """Add an item to a user's inventory."""
        inventory = self.get_inventory(user)
        if item not in inventory:
            inventory[item] = 0
        inventory[item] += amount
        return inventory[item]
    def remove_item(self, user: discord.Member, item: Item, amount: int = 1) -> int:
        """Remove an item from a user's inventory."""
        inventory = self.get_inventory(user)
        if item not in inventory:
            raise ValueError(f"Item {item} not found in inventory.")
        if inventory[item] < amount:
            raise ValueError(f"Not enough {item} in inventory to remove {amount}. Current amount: {inventory[item]}")
        inventory[item] -= amount
        if inventory[item] == 0:
            del inventory[item]
        return inventory.get(item, 0)
    def has_item(self, user: discord.Member, item: Item, amount: int = 1) -> bool:
        """Check if a user has a certain amount of an item."""
        inventory = self.get_inventory(user)
        return inventory.get(item, 0) >= amount
    @commands.command(name='debuginventory', aliases=['debuginv', 'dinv'])
    @commands.has_any_role(ROLES.TOTALLY_MOD)
    async def debug_inventory(self, ctx: commands.Context, member: MemberLike = 'self'):
        """Debug command to show a user's inventory."""
        if member == 'self':
            member = ctx.author
        user_id = self.get_id(member)
        inventory = self.get_inventory(user_id)
        if not inventory:
            await ctx.send(f"{member.name if isinstance(member, discord.Member) else member} has an empty inventory.")
            return
        items = "\n".join(f"{item}: {amount}" for item, amount in inventory.items())
        await ctx.send(f"Inventory for {member}:\n{items}")
    @commands.command(name='additem', aliases=['addinv'])
    @commands.has_any_role(ROLES.TOTALLY_MOD)
    async def additem(self, ctx: commands.Context, member: MemberLike = 'self', amount: int = 1, *, item: Item):
        """Add an item to a user's inventory."""
        if member == 'self':
            member = ctx.author
        amount = self.add_item(member, item, amount) # type: ignore
        await ctx.send(f"Added {amount:,} of {item} to {member}'s inventory.\nThey now have {amount:,} of {item}.")
    @commands.command(name='removeitem', aliases=['removeinv'])
    @commands.has_any_role(ROLES.TOTALLY_MOD)
    async def removeitem(self, ctx: commands.Context, member: MemberLike = 'self', amount: int = 1, *, item: Item):
        """Remove an item from a user's inventory."""
        if member == 'self':
            member = ctx.author.name
        elif isinstance(member, discord.Member):
            member = member.name
        try:
            amount = self.remove_item(member, item, amount) # type: ignore
            await ctx.send(f"Removed {amount} of {item} from {member}'s inventory.\nThey now have {amount} of {item}.")
        except ValueError as e:
            await ctx.send(f"{member} does not have enough of {item} in their inventory to remove {amount}.\n{str(e)}")
    # Inventory Embed
    @commands.command(name='inventory', aliases=['inv'])
    async def inventory(self, ctx: commands.Context, member: Optional[discord.Member] = None): # type: ignore
        """Show a user's inventory."""
        if member is None:
            member: discord.Member = ctx.author # type: ignore
        inventory = self.get_inventory(member)
        if not inventory:
            await ctx.send(f"{member.name} has an empty inventory.")
            return
        embed = discord.Embed(title=f"{member.name}'s Inventory", color=discord.Color.blue())
        for item, amount in inventory.items():
            embed.add_field(name=item, value=f"Amount: {amount:,}", inline=False)
        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    """Function to load the cog."""
    await bot.add_cog(InventoryCog(bot))
    print("InventoryCog has been (re-)loaded.")