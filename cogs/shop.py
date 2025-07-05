from enum import Enum
from typing import Awaitable, Callable, Coroutine, Optional, Self
from discord.ext import commands
import discord

from constants import ROLES

# idk if these will get reloaded or not, but they're not supposed to be used in other files
# so they're outside of the cog

# Sorry
# -Henry (jul 4, 2025)

def requires_roles(*roles: int):
    """Decorator to require specific roles for a command."""
    def decorator(func: ShopCog.ShopItem):
        func.required_roles = roles
        return func
    return decorator
def shopitem(name: str, price: int, *required_roles: int):
    """Decorator to create a shop item."""
    def decorator(func: Callable[[ShopCog.Shop, commands.Context], Coroutine]):
        item = ShopCog.ShopItem(
            *required_roles,
            name=name,
            price=price,
            on_buy=func,
        )
        return item
    return decorator

class ShopCog(commands.Cog):
    """The shop is here because economy got too large lmao"""

    class ShopItem:
        def __init__(
                self, 
                name: str,
                price: int,
                on_buy: Callable[["ShopCog.Shop", commands.Context], Awaitable] | Coroutine,
                *required_roles: Optional[int]
            ) -> None:
            """Initializes a shop item.
            Args:
                bot (commands.Bot): The bot instance.
                name (str): The name of the item.
                price (int): The price of the item in Eden Coins.
                on_buy (commands.Command | Coroutine): The command or coroutine to execute when the item is purchased.
                required_roles (optional: int): The role IDs required to purchase the item. Having any listed role is enough to buy the item.
            """
            self.name = name
            self.price = price
            self.on_buy = on_buy
            self.required_roles = required_roles if required_roles else []

        def purchasable(self, bot: commands.Bot, member: discord.Member) -> bool:
            """Checks if the item is purchasable by the member."""
            member_roles = [r.id for r in member.roles]
            if not any(role in member_roles for role in self.required_roles):
                return False
            member_balance: int = bot.cogs["EconomyCog"].get(member.name) # type: ignore
            return member_balance >= self.price
        def __hash__(self) -> int:
            return hash((self.name, self.price, tuple(self.required_roles), self.on_buy))
        def __str__(self) -> str:
            return f"{self.name} - {self.price} Eden Coins"
        def __repr__(self) -> str:
            return f"ShopItem(name={self.name}, price={self.price}, required_roles={self.required_roles})"

    class Shop(Enum):
        """Enum for shop items."""
        def __init__(self, bot: commands.Bot):
            self.bot = bot
        
        ############################
        # ADD YOUR SHOP ITEMS HERE #
        ############################

        @requires_roles(ROLES.TOTALLY_MOD)
        @shopitem(name="test", price=100)
        async def test_item(self, ctx: commands.Context):
            print(f"Test item purchased by {ctx.author.name}")

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="shop")
    async def shop(self, ctx):
        """Displays the shop items."""
        embed = discord.Embed(
            title="Eden Shop",
            description="Welcome to the Eden Shop! Here are the items you can purchase:",
            color=discord.Color.green()
        )
        
        for item in self.Shop:
            embed.add_field(name=item.value.replace("_", " ").title(), value=item.value, inline=False)
        
        embed.set_footer(text="Use ;buy <item_name> to purchase an item.")
        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    """Function to load the cog."""
    await bot.add_cog(ShopCog(bot))
    print("ShopCog has been (re-)loaded.")