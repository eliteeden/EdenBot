# from __future__ import annotations
# I don't think future works in cogs

import math
import discord
from discord.ext import commands
from typing import Callable, Coroutine, Iterator, Optional, overload, TYPE_CHECKING

if TYPE_CHECKING:
    from cogs.economy import EconomyCog
    from cogs.inventory import InventoryCog
from constants import ROLES, CHANNELS

type ShopItem = "ShopCog.Shop.ShopItem" # TypeDef for type hinting

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
                    description (str, optional): A description of the item. Defaults to the function's docstring or "No description available.".
                """

                def decorator(
                    func: Callable[
                        [commands.Bot, discord.Interaction], Coroutine[None, None, bool]
                    ],
                ) -> ShopItem:
                    item = cls(
                        name=name,
                        description=(
                            description or func.__doc__ or "No description available."
                        ).strip(),
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
                on_buy: Callable[
                    [commands.Bot, discord.Interaction], Coroutine[None, None, bool]
                ],
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
                self.items: list[tuple[str, int, Optional[int], str, str, bool]] = []
                # [(item_name, amount, maximum_items, buy_message, maximum_message, hide_on_maximum)]

            def purchasable(self, bot: commands.Bot, member: discord.Member) -> bool:
                """Checks if the item is purchasable by the member."""
                for role in self.excluded_roles:
                    if member.get_role(role) is not None:
                        return False
                for role in self.required_roles:
                    if member.get_role(role) is None:
                        return False
                for (
                    item,
                    amount,
                    maximum_items,
                    buy_message,
                    maximum_message,
                    hide_on_maximum,
                ) in self.items:
                    if bot.get_cog("InventoryCog").get_item(member, item) >= (maximum_items or float("inf")) and hide_on_maximum: # type: ignore
                        # If the user has the maximum amount of the item, they can't buy it again
                        return False
                return True
                # member_balance: int = bot.cogs["EconomyCog"].get(member) # type: ignore
                # return member_balance >= self.price

            def __hash__(self) -> int:
                return hash(
                    (self.name, self.price, tuple(self.required_roles), self.on_buy)
                )

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
            items = [
                getattr(self, item)
                for item in dir(self)
                if isinstance(getattr(self, item), self.ShopItem)
            ]
            return len(items)

        # Iteration
        def __iter__(self) -> Iterator[ShopItem]:
            """Iterates over the shop items."""
            items = [
                getattr(self, item)
                for item in dir(self)
                if isinstance(getattr(self, item), self.ShopItem)
            ]
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

        @staticmethod
        def gives_item(
            item_name: str,
            amount: int = 1,
            /,
            maximum_items: Optional[int] = None,
            *,
            buy_message: str = "",
            maximum_message: str = "",
            hide_on_maximum: bool = False,
        ):
            """Decorator to give an item to the user when they purchase the shop item.
            If the function returns True, the item is given to the user.
            Args:
                item_name (str): The name of the item to give.
                amount (int, optional): The amount of the item to give. Defaults to 1.
                maximum_items (int, optional): The maximum number of items that can be given. Defaults to None, meaning no limit.
                buy_message (str, optional): The message to send when the item is purchased. Defaults to "You have purchased {item_name}.".
                maximum_message (str, optional): The message to send when the user already has the maximum amount of the item. Defaults to "You already have the maximum amount of {item_name}."
            """
            if buy_message == "":
                buy_message = f"You have purchased {item_name}."
            if maximum_message == "":
                maximum_message = f"You already have the maximum amount of {item_name}."

            def decorator(func: ShopItem):
                func.items += [
                    (
                        item_name,
                        amount,
                        maximum_items,
                        buy_message,
                        maximum_message,
                        hide_on_maximum,
                    )
                ]
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
            await updates_channel.send(
                f"Test item purchased by {interaction.user.name}"
            )
            return True

        @requires_roles(ROLES.TOTALLY_MOD)
        @shopitem(name="test2", price=200)
        @staticmethod
        async def test2_item(bot: commands.Bot, interaction: discord.Interaction):
            """Prints a test message to the bot logs channel."""
            updates_channel: discord.TextChannel = bot.get_channel(CHANNELS.BOT_LOGS) # type: ignore
            await updates_channel.send(
                f"Test2 item purchased by {interaction.user.name}"
            )
            return True

        @requires_roles(ROLES.TOTALLY_MOD)
        @shopitem(name="test3", price=300)
        @staticmethod
        async def test3_item(bot: commands.Bot, interaction: discord.Interaction):
            """Prints a test message to the bot logs channel."""
            updates_channel: discord.TextChannel = bot.get_channel(CHANNELS.BOT_LOGS) # type: ignore
            await updates_channel.send(
                f"Test3 item purchased by {interaction.user.name}"
            )
            return True

        # That should be one page

        @gives_item(
            "Talk Command Permissions",
            1,
            maximum_items=1,
            buy_message="You can now use the /talk command.",
            maximum_message="You already have the /talk command permissions.",
            hide_on_maximum=True,
        )
        @shopitem(name="talk", price=250_000)
        @staticmethod
        async def talk_command_perms(
            bot: commands.Bot, interaction: discord.Interaction
        ):
            """
            Allows you to use the /talk command.
            (note: You may have to add the Eden Bot as a user-installed app to use it in capital.)
            """
            return True

        @gives_item(
            "Lock",
            1,
            maximum_items=5,
            buy_message="",
            maximum_message="I think five locks is enough for now.",
        )
        @shopitem(name="Lock", price=50_000)
        @staticmethod
        async def lock(bot: commands.Bot, interaction: discord.Interaction):
            """
            Makes stealing from you much harder.
            Breaks after someone steals from you successfully.
            Max: 5
            """
            return True

        @gives_item(
            "Lockpick",
            1,
            maximum_items=2,
            buy_message="Use it wisely, okay?",
            maximum_message="Woah there, you aren't De Santa",
        )
        @shopitem(name="Lockpick", price=100_000)
        @staticmethod
        async def lockpick(bot: commands.Bot, interaction: discord.Interaction):
            """
            Significantly increases the chance of stealing from someone with a lock.
            Breaks after one use, ignored if target doesn't have a lock.
            Max: 2
            """
            return True

        @gives_item(
            "Butterfly",
            1,
            maximum_items=5,
            buy_message="You bought a pristine butterfly!",
            maximum_message="That's too much love, hun.",
        )
        @shopitem(name="Butterfly", price=50_000)
        @staticmethod
        async def butterfly(bot: commands.Bot, interaction: discord.Interaction):
            """
            A cute butterfly. Eden's mascot
            Max: 5
            """
            return True

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.economy: Callable[[], EconomyCog] = lambda: bot.get_cog("EconomyCog") # type: ignore
        self.inventory: Callable[[], InventoryCog] = lambda: bot.get_cog("InventoryCog") # type: ignore

    class ShopButtons(discord.ui.View):
        """The view containing the shop buttons."""

        class BackButton(discord.ui.Button):
            """A button to go back to the previous page."""

            def __init__(
                self,
                shop: "ShopCog",
                user: discord.Member,
                page: int,
                disabled: bool,
                show_all: bool,
            ):
                super().__init__(label="◀️", style=discord.ButtonStyle.secondary)
                self.shop = shop
                self.user = user
                self.page = page
                self.disabled = disabled
                self.show_all = show_all

            async def callback(self, interaction: discord.Interaction):
                assert isinstance(
                    interaction.user, discord.Member
                ), "Interaction user must be a Member."
                embed, view = await self.shop.generate_shop_page(
                    self.user, page=self.page - 1, show_all=self.show_all
                )
                await interaction.response.edit_message(embed=embed, view=view)
                return True

        class NextButton(discord.ui.Button):
            """A button to go to the next page."""

            def __init__(
                self,
                shop: "ShopCog",
                user: discord.Member,
                disabled: bool,
                page: int,
                show_all: bool,
            ):
                super().__init__(label="▶️", style=discord.ButtonStyle.secondary)
                self.shop = shop
                self.user = user
                self.page = page
                self.disabled = disabled
                self.show_all = show_all

            async def callback(self, interaction: discord.Interaction):
                assert isinstance(
                    interaction.user, discord.Member
                ), "Interaction user must be a Member."
                embed, view = await self.shop.generate_shop_page(
                    self.user, page=self.page + 1, show_all=self.show_all
                )
                await interaction.response.edit_message(embed=embed, view=view)
                return True

        class ShopButton(discord.ui.Button):
            """A button for a shop item."""

            def __init__(
                self,
                item: ShopItem,
                shop: "ShopCog",
                user: discord.Member,
                disabled: bool,
            ):
                super().__init__(label=item.name, style=discord.ButtonStyle.primary)
                self.item = item
                self.shop = shop
                self.user = user
                self.disabled = disabled or shop.economy().get(user) < item.price

            async def disable(self, interaction: discord.Interaction):
                """Disables the button."""
                self.disabled = True
                await interaction.message.edit(content=interaction.message.content, view=self.view) # type: ignore

            async def callback(self, interaction: discord.Interaction):
                assert isinstance(
                    interaction.user, discord.Member
                ), "Interaction user must be a Member."
                # await interaction.response.defer()  # defer the response to avoid timeout
                if not self.shop.economy() or not self.shop.inventory():
                    await self.disable(interaction)
                    await interaction.response.send_message(
                        "Cogs not found. Please try again later.", ephemeral=True
                    )
                    return False
                for (
                    item,
                    amount,
                    maximum_items,
                    buy_message,
                    maximum_message,
                    hide_on_maximum,
                ) in self.item.items:
                    if self.shop.inventory().get_item(interaction.user, item) >= (
                        maximum_items or float("inf")
                    ):
                        # If the user has the maximum amount of the item, they can't buy it again
                        # Theoretically hide_on_maximum will always be false here.
                        await self.disable(interaction)
                        await interaction.response.send_message(
                            maximum_message, ephemeral=True
                        )
                        return False
                if not self.item.purchasable(self.shop.bot, interaction.user):
                    await self.disable(interaction)
                    await interaction.response.send_message(
                        f"You no longer are able to purchase this item.",  # Would be disabled otherwise
                        ephemeral=True,
                    )
                    return False
                if self.shop.economy().get(interaction.user) < self.item.price:
                    await self.disable(interaction)
                    await interaction.response.send_message(
                        f"You do not have enough Eden Coins to purchase {self.item.name}.",
                        ephemeral=True,
                    )
                    return False
                if interaction.user.id == self.shop.bot.user.id: # type: ignore
                    await self.disable(interaction)
                    await interaction.response.send_message(
                        "You cannot purchase items for the bot.", ephemeral=True
                    )
                    return False
                # Remove coins
                # run the on_buy function
                success = await self.item.on_buy(self.shop.bot, interaction)
                if success is False:
                    await self.disable(interaction)
                    return False
                self.shop.economy().sub(interaction.user, self.item.price)
                buy_msg = ""
                for (
                    item,
                    amount,
                    maximum_items,
                    buy_message,
                    maximum_message,
                    hide_on_maximum,
                ) in self.item.items:
                    self.shop.inventory().add_item(interaction.user, item, amount) # type: ignore
                    buy_msg += f"\n{buy_message.format(item_name=item)}"
                # Log the purchase
                UPDATES_CHANNEL: discord.TextChannel = self.shop.bot.get_channel(CHANNELS.BOT_LOGS) # type: ignore
                await UPDATES_CHANNEL.send(
                    f"{interaction.user.mention} ({interaction.user.name}) has purchased {self.item.name} for {self.item.price:,} Eden Coins."
                )
                await interaction.response.send_message(
                    f"You have successfully purchased {self.item.name} for {self.item.price:,} Eden Coins."
                    + buy_msg,
                    ephemeral=True,
                )
                if self.shop.economy().get(interaction.user) < self.item.price:
                    await self.disable(interaction)
                return True

        def __init__(
            self,
            shopcog: "ShopCog",
            user: discord.Member,
            items: list[ShopItem],
            page: int,
            pages: int,
            show_all: bool,
        ):
            super().__init__(timeout=None)
            self.add_item(
                self.BackButton(
                    shopcog, user, page=page, disabled=page <= 0, show_all=show_all
                )
            )
            for item in items:
                self.add_item(self.ShopButton(item, shopcog, user, disabled=show_all))
            self.add_item(
                self.NextButton(
                    shopcog,
                    user,
                    page=page,
                    disabled=page + 1 >= pages,
                    show_all=show_all,
                )
            )

    async def generate_shop_page(
        self, user: discord.Member, show_all: bool = False, page: int = 0
    ) -> tuple[discord.Embed, discord.ui.View]:
        """Generates an embed for the shop page."""
        embed = discord.Embed(
            title="Eden Shop",
            description="All items are used automatically when needed.",
            color=discord.Color.blurple() if show_all else discord.Color.green(),
        )
        shop = self.Shop()
        print(f"Generating shop page... ({len(shop)} items)")
        buyable_items = [
            item for item in shop if item.purchasable(self.bot, user) or show_all
        ]
        pages = math.ceil(len(buyable_items) / 3)
        items = buyable_items[page * 3 : (page + 1) * 3]
        if not items:
            embed.description = (
                "There are no items available for purchase at the moment."
            )
            return embed, discord.ui.View()
        for item in items:
            embed.add_field(
                name=f"{item.name} - {item.price:,} Eden Coins",
                value=f"{'' if item.purchasable(self.bot, user) or show_all else '(not purchasable)'}"
                + item.description,
                inline=False,
            )
        embed.set_footer(
            text=f"Page {page + 1} of {pages} | Use the buttons below to navigate."
        )
        view = self.ShopButtons(
            self, user, items, page=page, pages=pages, show_all=show_all
        )

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
