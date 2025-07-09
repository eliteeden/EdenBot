# from __future__ import annotations
# I don't think future works in cogs

import discord
from discord.ext import commands
from typing import Callable, Coroutine, Generator, Iterator, Optional, overload

from cogs.economy import EconomyCog # TypeDef only
from constants import ROLES, CHANNELS

type ShopItem = "ShopCog.Shop.ShopItem"  # TypeDef for type hinting

# Hey, the counter for how long I've wasted trying to remove @staticmethod is back
hours_wasted = 8

class ShopCog(commands.Cog):
    """The shop is here because economy got too large lmao"""

    class Shop:
        class ShopItem:
            @classmethod
            def __decorator__(cls, name: str, price: int, description: str = ""):
                """Creates a shop item.
                Args:
                    name (str): The name of the item.
                    price (int): The price of the item in Eden Coins.
                    description (str, optional): A description of the item.
                """
                def decorator(func: Callable[[commands.Bot, discord.Interaction], Coroutine[None, None, bool]]) -> ShopItem:
                    item = cls(
                        name=name,
                        description=description or func.__doc__ or "No description available.",
                        price=price,
                        on_buy=func,
                    )
                    return item
                return decorator

            """Represents an item in the shop."""
            def __init__(
                    self, 
                    name: str,
                    price: int,
                    description: str,
                    on_buy: Callable[[commands.Bot, discord.Interaction], Coroutine[None, None, bool]],
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
                self.description = description
                self.required_roles: list[int] = []
                self.excluded_roles: list[int] = []

            def purchasable(self, bot: commands.Bot, member: discord.Member) -> bool:
                """Checks if the item is purchasable by the member."""
                for role in self.excluded_roles:
                    if member.get_role(role) is not None:
                        return False
                for role in self.required_roles:
                    if member.get_role(role) is None:
                        return False
                member_balance: int = bot.cogs["EconomyCog"].get(member) # type: ignore
                return member_balance >= self.price
            def __hash__(self) -> int:
                return hash((self.name, self.price, tuple(self.required_roles), self.on_buy))
            def __str__(self) -> str:
                return f"{self.name} - {self.price} Eden Coins"
            def __repr__(self) -> str:
                return f"ShopItem(name={self.name}, price={self.price}, required_roles={self.required_roles})"

        """Enum for shop items."""
        @overload
        def __getitem__(self, name: str, /) -> ShopItem:
            """Get a shop item by its name."""
            ...
        @overload
        def __getitem__(self, index: int, /) -> ShopItem:
            """Get a shop item by its index."""
            ...
        def __getitem__(self, val: str | int, /) -> ShopItem:
            if isinstance(val, str):
                return self.__getattribute__(val)
            elif isinstance(val, int):
                i = 0
                for item in self:
                    if i == val:
                        return item
                    i += 1
                raise IndexError(f"Shop item index {val} out of range.")
        # Length
        def __len__(self) -> int:
            """Returns the number of shop items."""
            items = [getattr(self, item) for item in dir(self) if isinstance(getattr(self, item), self.ShopItem)]
            return len(items)
        # Iteration
        def __iter__(self) -> Iterator[ShopItem]:
            """Iterates over the shop items."""
            items = [getattr(self, item) for item in dir(self) if isinstance(getattr(self, item), self.ShopItem)]
            return iter(items)
        # Decorators
        @staticmethod
        def requires_roles(*roles: int):
            """Decorator to require specific roles for a command.
            A user must have at least one of the specified roles to use the command.
            When used with `excludes_roles`, the user must meet both conditions.
            Args:
                *roles (int): The role IDs required to use the command.
            """
            def decorator(func: ShopItem):
                func.required_roles += list(roles)
                return func
            return decorator
        @staticmethod
        def excludes_roles(*roles: int):
            """Decorator to exclude specific roles for a command.
            A user must not have any of the specified roles to use the command.
            When used with `requires_roles`, the user must meet both conditions.
            Args:
                *roles (int): The role IDs that cannot use the command.
            """
            def decorator(func: ShopItem):
                func.excluded_roles += list(roles)
                return func
            return decorator
        shopitem = ShopItem.__decorator__  # Alias for the item decorator


        ############################
        # ADD YOUR SHOP ITEMS HERE #
        ############################

        @requires_roles(ROLES.TOTALLY_MOD)
        @shopitem(name="test", price=100)
        @staticmethod
        async def test_item(bot: commands.Bot, interaction: discord.Interaction):
            """Prints a test message to the bot logs channel."""
            updates_channel: discord.TextChannel = bot.get_channel(CHANNELS.BOT_LOGS) # type: ignore
            await updates_channel.send(f"Test item purchased by {interaction.user.name}")
            return True

        @excludes_roles(ROLES.TALK_PERMS)
        @shopitem(name="talk", price=2_500_000)
        @staticmethod
        async def talk_command_perms(bot: commands.Bot, interaction: discord.Interaction):
            """Gives the user permission to use the /talk command."""
            if not isinstance(interaction.user, discord.Member):
                await interaction.response.send_message("This command can only be run in the eden server.", ephemeral=True)
                return False
            if ROLES.TALK_PERMS not in [role.id for role in interaction.user.roles]:
                await interaction.user.add_roles(discord.Object(id=ROLES.TALK_PERMS))
                return True
            await interaction.response.send_message("You are already able to use the /talk command.", ephemeral=True)
            return False # User already has the role, so they can't buy it again.
        @shopitem(name="Custom Role", price=100_000_000)
        @staticmethod
        async def custom_role(bot: commands.Bot, interaction: discord.Interaction):
            """Good luck, germanic."""
            await interaction.response.send_message(
                "literally how."
            )
            return False # not purchasable yet

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.economy: Callable[[], EconomyCog] =  lambda : bot.get_cog("EconomyCog") # type: ignore
    class ShopButtons(discord.ui.View):
        """The view containing the shop buttons."""
        class ShopButton(discord.ui.Button):
            """A button for a shop item."""
            def __init__(self, item: ShopItem, shop: "ShopCog", user: discord.Member):
                super().__init__(label=item.name, style=discord.ButtonStyle.primary)
                self.item = item
                self.shop = shop
                self.user = user

            async def callback(self, interaction: discord.Interaction):
                self.disabled = True
                await interaction.response.defer()  # defer the response to avoid timeout
                if not self.shop.economy():
                    await interaction.response.send_message("Economy cog not found. Please try again later.", ephemeral=True)
                    return False
                if not self.item.purchasable(self.shop.bot, interaction.user): # type: ignore
                    await interaction.response.send_message(
                        f"You no longer are able to purchase this item." # Would be disabled otherwise
                    )
                    return False
                if interaction.user.id == self.shop.bot.user.id: # type: ignore
                    await interaction.response.send_message("You cannot purchase items for the bot.", ephemeral=True)
                    return False
                # Remove coins
                self.shop.economy().set(interaction.user, self.shop.economy().get(interaction.user) - self.item.price)
                # run the on_buy function
                success = not (await self.item.on_buy(self.shop.bot, interaction) == False) # Returning None is the same as True
                if not success:
                    # The on_buy function should inform the user.
                    self.shop.economy().set(interaction.user, self.shop.economy().get(interaction.user) + self.item.price)
                    return False
                UPDATES_CHANNEL: discord.TextChannel = self.shop.bot.get_channel(CHANNELS.BOT_LOGS) # type: ignore
                await UPDATES_CHANNEL.send(f"{interaction.user.mention} ({interaction.user.name}) has purchased {self.item.name} for {self.item.price:,} Eden Coins.")
                return True
        def __init__(self, shopcog: "ShopCog", user: discord.Member, shop: "ShopCog.Shop", show_all: bool = False):
            self.economy = shopcog.economy
            self.user = user
            self.bot = shopcog.bot
            self.shop = shop
            self.show_all = show_all
            super().__init__(timeout=None)  # Disable timeout for the view
            for i, item in enumerate(self.shop):
                if not item.purchasable(self.bot, user) and not self.show_all:
                    continue
                # Create a button for each item
                self.add_item(self.ShopButton(item, shopcog, user))


    async def generate_shop_page(self, user: discord.Member, show_all: bool = False) -> tuple[discord.Embed, discord.ui.View]:
        """Generates an embed for the shop page."""
        embed = discord.Embed(
            title="Eden Shop",
            description="Welcome to the Eden Shop! Here are the items you can purchase:",
            color=discord.Color.green()
        )
        shop = self.Shop()
        print(f"Generating shop page... ({len(shop)} items)")
        for item in shop:
            print("Iterating over shop item:", item.name)
            if not item.purchasable(self.bot, user) and not show_all:
                continue
            embed.add_field(
                name=f"{item.name} - {item.price:,} Eden Coins",
                value=f"{'' if item.purchasable(self.bot, user) or show_all else '(not purchasable)'}" + item.description,
                inline=False
            )
        view = self.ShopButtons(self, user, shop)

        return embed, view
        

    @commands.command(name="shop")
    async def shop(self, ctx: commands.Context):
        """Displays the shop items."""
        embed, view = await self.generate_shop_page(ctx.author) # type: ignore
        await ctx.send(embed=embed, view=view)
    @commands.command(name="shopall")
    @commands.has_any_role(ROLES.TOTALLY_MOD)
    async def shop_all(self, ctx: commands.Context):
        """Displays all shop items, even those that are not purchasable."""
        embed, view = await self.generate_shop_page(ctx.author, show_all=True) # type: ignore
        await ctx.send(embed=embed, view=view)

async def setup(bot: commands.Bot):
    """Function to load the cog."""
    await bot.add_cog(ShopCog(bot))
    print("ShopCog has been (re-)loaded.")
