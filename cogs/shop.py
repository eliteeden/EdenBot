import discord
from discord.ext import commands
from enum import Enum
from typing import Callable, Coroutine, Optional, overload

from constants import ROLES, CHANNELS

# idk if these will get reloaded or not, but they're not supposed to be used in other files
# so they're outside of the cog

# If you try and find a better way, update this counter
hours_wasted = 1.5

# Sorry
# -Henry (jul 4, 2025)

def requires_roles(*roles: int):
    """Decorator to require specific roles for a command.
    This is the same as adding the roles into the `shopitem` decorator.
    Args:
        *roles (int): The role IDs required to use the command.
    """
    def decorator(func: ShopCog.ShopItem):
        func.required_roles = roles
        return func
    return decorator
def shopitem(name: str, price: int, *required_roles: int):
    """Creates a shop item.
    Args:
        name (str): The name of the item.
        price (int): The price of the item in Eden Coins.
        *required_roles (optional, int): The role IDs required to purchase the item. Having any listed role is enough to buy the item.
    """
    def decorator(func: Callable[[ShopCog.Shop, commands.Bot, discord.Interaction], Coroutine[None, None, None]]) -> ShopCog.ShopItem:
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
        """Represents an item in the shop."""
        def __init__(
                self, 
                name: str,
                price: int,
                on_buy: Callable[["ShopCog.Shop", commands.Bot, discord.Interaction], Coroutine[None, None, None]],
                *required_roles: Optional[int]
            ) -> None:
            """Initializes a shop item. This should be created using the `shopitem` decorator.
            Args:
                bot (commands.Bot): The bot instance.
                name (str): The name of the item.
                price (int): The price of the item in Eden Coins.
                on_buy (commands.Command | Coroutine): The command or coroutine to execute when the item is purchased. This function should take three arguments: the shop, the bot, and the context.
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
        @overload
        def __getitem__(self, name: str, /) -> "ShopCog.ShopItem":
            """Get a shop item by its name."""
            ...
        @overload
        def __getitem__(self, index: int, /) -> "ShopCog.ShopItem":
            """Get a shop item by its index."""
            ...
        def __getitem__(self, val: str | int, /) -> "ShopCog.ShopItem":
            if isinstance(val, str):
                return self.__getattribute__(val).value
            elif isinstance(val, int):
                i = 0
                for item in self:
                    if i == val:
                        return item.value # type: ignore
                    i += 1
                raise IndexError(f"Shop item index {val} out of range.")

        ############################
        # ADD YOUR SHOP ITEMS HERE #
        ############################

        @requires_roles(ROLES.TOTALLY_MOD)
        @shopitem(name="test", price=100)
        async def test_item(self, bot: commands.Bot, ctx: discord.Interaction):
            updates_channel: discord.TextChannel = bot.get_channel(CHANNELS.BOT_LOGS) # type: ignore
            await updates_channel.send(f"Test item purchased by {ctx.user.name}")

    def __init__(self, bot):
        self.bot = bot
    
    class ShopButtons(discord.ui.View):
        def __init__(self, bot: commands.Bot, item: "ShopCog.ShopItem"):
            super().__init__(timeout=None)
            self.item = item
            self.bot = bot
            if not isinstance(item, ShopCog.ShopItem):
                raise TypeError("item must be an instance of ShopCog.ShopItem")

        @discord.ui.button(label="◀️", style=discord.ButtonStyle.secondary, custom_id="back-btn")
        async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            pass
        @discord.ui.button(label=f"Buy", style=discord.ButtonStyle.green, custom_id="buy-btn")
        async def buy_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.item.on_buy(self.bot, interaction) # TODO: fix this (what should I pass for `self`)
        @discord.ui.button(label="▶️", style=discord.ButtonStyle.secondary, custom_id="next-btn")
        async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            pass
    
    @commands.command(name="shop")
    async def shop(self, ctx):
        """Displays the shop items."""
        embed = discord.Embed(
            title="Eden Shop",
            description="Welcome to the Eden Shop! Here are the items you can purchase:",
            color=discord.Color.green()
        )
        selected: ShopCog.ShopItem = None # type: ignore
        for item in self.Shop:
            print(item.name, item.value)
            selected = item.value

        await ctx.send(embed=embed, view=self.ShopButtons(bot=self.bot, item=selected))

async def setup(bot: commands.Bot):
    """Function to load the cog."""
    return # Still WIP
    await bot.add_cog(ShopCog(bot))
    print("ShopCog has been (re-)loaded.")