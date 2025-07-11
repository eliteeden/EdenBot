# from __future__ import annotations
# I don't think future works in cogs

import discord
from discord.ext import commands
from typing import Callable, Coroutine, Generator, Iterator, Optional, overload

from cogs.economy import EconomyCog # TypeDef only
from cogs.inventory import InventoryCog # TypeDef only
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
                return True
                # member_balance: int = bot.cogs["EconomyCog"].get(member) # type: ignore
                # return member_balance >= self.price
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
        @requires_roles(ROLES.TOTALLY_MOD)
        @shopitem(name="test2", price=200)
        @staticmethod
        async def test2_item(bot: commands.Bot, interaction: discord.Interaction):
            """Prints a test message to the bot logs channel."""
            updates_channel: discord.TextChannel = bot.get_channel(CHANNELS.BOT_LOGS) # type: ignore
            await updates_channel.send(f"Test2 item purchased by {interaction.user.name}")
            return True
        @requires_roles(ROLES.TOTALLY_MOD)
        @shopitem(name="test3", price=300)
        @staticmethod
        async def test3_item(bot: commands.Bot, interaction: discord.Interaction):
            """Prints a test message to the bot logs channel."""
            updates_channel: discord.TextChannel = bot.get_channel(CHANNELS.BOT_LOGS) # type: ignore
            await updates_channel.send(f"Test3 item purchased by {interaction.user.name}")
            return True
        
        # That should be one page

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
        @shopitem(name="Lock", price=500_000)
        @staticmethod
        async def lock(bot: commands.Bot, interaction: discord.Interaction):
            """Makes stealing from you much harder. (Breaks after someone steals from you successfully)"""
            inventory: InventoryCog = bot.get_cog("InventoryCog") # type: ignore
            if inventory.get_inventory(interaction.user).get("Lock", 0) >= 5:
                await interaction.response.send_message(
                    "I think five locks is enough for now.",
                    ephemeral=True
                )
                return False
            inventory.add_item(interaction.user, "Lock", 1) # type: ignore
            await interaction.response.send_message(
                "You bought a lock!"
            )
            return True # Item added to inventory
        @shopitem(name="Butterfly", price=50_000)
        @staticmethod
        async def butterfly(bot: commands.Bot, interaction: discord.Interaction):
            """A cute butterfly. Eden's mascot"""
            inventory: InventoryCog = bot.get_cog("InventoryCog") # type: ignore
            if inventory.get_inventory(interaction.user).get("Butterfly", 0) >= 5:
                await interaction.response.send_message(
                    "That's too much love, hun.",
                    ephemeral=True
                )
                return False
            inventory.add_item(interaction.user, "Butterfly", 1) # type: ignore
            await interaction.response.send_message(
                "You bought a pristine butterfly!"
            )
            return True # Item added to inventory


    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.economy: Callable[[], EconomyCog] =  lambda : bot.get_cog("EconomyCog") # type: ignore
    class ShopButtons(discord.ui.View):
        """The view containing the shop buttons."""
        class BackButton(discord.ui.Button):
            """A button to go back to the previous page."""
            def __init__(self, shop: "ShopCog", user: discord.Member, page: int, disabled: bool, show_all: bool):
                super().__init__(label="◀️", style=discord.ButtonStyle.secondary)
                self.shop = shop
                self.user = user
                self.page = page
                self.disabled = disabled
                self.show_all = show_all
            async def callback(self, interaction: discord.Interaction):
                assert isinstance(interaction.user, discord.Member), "Interaction user must be a Member."
                embed, view = await self.shop.generate_shop_page(self.user, page=self.page - 1, show_all=self.show_all)
                await interaction.response.edit_message(embed=embed, view=view)
                return True
        class NextButton(discord.ui.Button):
            """A button to go to the next page."""
            def __init__(self, shop: "ShopCog", user: discord.Member, disabled: bool, page: int, show_all: bool):
                super().__init__(label="▶️", style=discord.ButtonStyle.secondary)
                self.shop = shop
                self.user = user
                self.page = page
                self.disabled = disabled
                self.show_all = show_all
            async def callback(self, interaction: discord.Interaction):
                assert isinstance(interaction.user, discord.Member), "Interaction user must be a Member."
                embed, view = await self.shop.generate_shop_page(self.user, page=self.page + 1, show_all=self.show_all)
                await interaction.response.edit_message(embed=embed, view=view)
                return True
        class ShopButton(discord.ui.Button):
            """A button for a shop item."""
            def __init__(self, item: ShopItem, shop: "ShopCog", user: discord.Member):
                super().__init__(label=item.name, style=discord.ButtonStyle.primary)
                self.item = item
                self.shop = shop
                self.user = user
                self.disabled = shop.economy().get(user) < item.price
            async def disable(self, interaction: discord.Interaction):
                """Disables the button."""
                self.disabled = True
                await interaction.message.edit(content=interaction.message.content, view=self.view) # type: ignore

                

            async def callback(self, interaction: discord.Interaction):
                assert isinstance(interaction.user, discord.Member), "Interaction user must be a Member."
                # await interaction.response.defer()  # defer the response to avoid timeout
                if not self.shop.economy():
                    await self.disable(interaction)
                    await interaction.response.send_message("Economy cog not found. Please try again later.", ephemeral=True)
                    return False
                if not self.item.purchasable(self.shop.bot, interaction.user):
                    await self.disable(interaction)
                    await interaction.response.send_message(
                        f"You no longer are able to purchase this item." # Would be disabled otherwise
                    )
                    return False
                if self.shop.economy().get(interaction.user) < self.item.price:
                    await self.disable(interaction)
                    await interaction.response.send_message(
                        f"You do not have enough Eden Coins to purchase {self.item.name}.",
                        ephemeral=True
                    )
                    return False
                if interaction.user.id == self.shop.bot.user.id: # type: ignore
                    await self.disable(interaction)
                    await interaction.response.send_message("You cannot purchase items for the bot.", ephemeral=True)
                    return False
                # Remove coins
                # run the on_buy function
                success = await self.item.on_buy(self.shop.bot, interaction)
                if success is False:
                    await self.disable(interaction)
                    return False
                self.shop.economy().sub(interaction.user, self.item.price)
                UPDATES_CHANNEL: discord.TextChannel = self.shop.bot.get_channel(CHANNELS.BOT_LOGS) # type: ignore
                await UPDATES_CHANNEL.send(f"{interaction.user.mention} ({interaction.user.name}) has purchased {self.item.name} for {self.item.price:,} Eden Coins.")
                await interaction.response.send_message(
                    f"You have successfully purchased {self.item.name} for {self.item.price:,} Eden Coins.",
                    ephemeral=True)
                if self.shop.economy().get(interaction.user) < self.item.price:
                    await self.disable(interaction)
                return True
        def __init__(self, shopcog: "ShopCog", user: discord.Member, items: list[ShopItem], page: int, pages: int, show_all: bool):
            super().__init__(timeout=None)
            self.add_item(self.BackButton(shopcog, user, page=page, disabled=page <= 0, show_all=show_all))
            for item in items:
                self.add_item(self.ShopButton(item, shopcog, user))
            self.add_item(self.NextButton(shopcog, user, page=page, disabled=page + 1 >= pages, show_all=show_all))


    async def generate_shop_page(self, user: discord.Member, show_all: bool = False, page: int = 0) -> tuple[discord.Embed, discord.ui.View]:
        """Generates an embed for the shop page."""
        embed = discord.Embed(
            title="Eden Shop",
            description="All items are used automatically when needed.",
            color=discord.Color.blurple() if show_all else discord.Color.green()
        )
        shop = self.Shop()
        print(f"Generating shop page... ({len(shop)} items)")
        buyable_items = [item for item in shop if item.purchasable(self.bot, user) or show_all]
        pages = len(buyable_items) // 3 + 1
        items = buyable_items[page * 3:(page + 1) * 3]
        if not items:
            embed.description = "There are no items available for purchase at the moment."
            return embed, discord.ui.View()
        for item in items:
            embed.add_field(
                name=f"{item.name} - {item.price:,} Eden Coins",
                value=f"{'' if item.purchasable(self.bot, user) or show_all else '(not purchasable)'}" + item.description,
                inline=False
            )
        embed.set_footer(text=f"Page {page + 1} of {pages} | Use the buttons below to navigate.")
        view = self.ShopButtons(self, user, items, page=page, pages=pages, show_all=show_all)

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
