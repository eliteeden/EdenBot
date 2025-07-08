# from __future__ import annotations
# I don't think future works in cogs

import discord
from discord.ext import commands
from typing import Callable, Coroutine, Generator, Iterator, Optional, overload

from cogs.economy import EconomyCog # TypeDef only
from constants import ROLES, CHANNELS

type ShopItem = "ShopCog.Shop.ShopItem"  # TypeDef for type hinting

# Hey, the counter for how long I've wasted trying to remove @staticmethod is back
hours_wasted = 7

class ShopCog(commands.Cog):
    """The shop is here because economy got too large lmao"""

    class Shop:
        class ShopItem:
            @classmethod
            def __decorator__(cls, name: str, price: int, *required_roles: int):
                """Creates a shop item.
                Args:
                    name (str): The name of the item.
                    price (int): The price of the item in Eden Coins.
                    *required_roles (optional, int): The role IDs required to purchase the item. Having any listed role is enough to buy the item.
                """
                def decorator(func: Callable[[commands.Bot, discord.Interaction], Coroutine[None, None, bool]]) -> ShopItem:
                    item = cls(
                        *required_roles,
                        name=name,
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
                self.required_roles: tuple[int, ...] = tuple()
                self.excluded_roles: tuple[int, ...] = tuple()

            def purchasable(self, bot: commands.Bot, member: discord.Member) -> bool:
                """Checks if the item is purchasable by the member."""
                member_roles = [r.id for r in member.roles]
                if not any(role in member_roles for role in self.required_roles):
                    return False
                if any(role in member_roles for role in self.excluded_roles):
                    return False
                member_balance: int = bot.cogs["EconomyCog"].get(member.name) # type: ignore
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
                return self.__getattribute__(val).value
            elif isinstance(val, int):
                i = 0
                for item in self:
                    if i == val:
                        return item.value # type: ignore
                    i += 1
                raise IndexError(f"Shop item index {val} out of range.")
        # Length
        def __len__(self) -> int:
            """Returns the number of shop items."""
            items = [getattr(self, item) for item in dir(self) if type(getattr(self, item)).__name__ is "ShopItem"]
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
                func.required_roles = roles
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
                func.excluded_roles = roles
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

    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    class ShopButtons(discord.ui.View):
        def __init__(self, bot: commands.Bot, item: ShopItem):
            super().__init__(timeout=None)
            self.item = item
            self.bot = bot
            self.shop: "ShopCog" = bot.get_cog("ShopCog") # type: ignore
            self.economy: EconomyCog = self.bot.get_cog("EconomyCog") # type: ignore
            if "ShopItem" not in item.__class__.__name__:
                raise TypeError(f"item must be an instance of ShopItem (got: {item.__class__.__name__})")
        def _parse_page(self, page: str) -> int:
            """Parses the page number from the footer text."""
            # Input string:
            # "Page 1/5 - Use the buttons below to navigate."
            return int(page.split("/")[0].split(" ")[-1])  # Get the first number before the slash

        @discord.ui.button(label="◀️", style=discord.ButtonStyle.secondary)
        async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            embed, view = await self.shop.generate_shop_page(interaction.user, page=self._parse_page(interaction.message.embeds[0].footer.text) - 1)  # type: ignore
            if not interaction.message or not interaction.message.embeds:
                return await interaction.response.send_message("Unable to find the shop dialogue, try making a new one.", ephemeral=True)
            await interaction.message.edit(embed=embed, view=view)
        @discord.ui.button(label=f"Buy", style=discord.ButtonStyle.green)
        async def buy_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            button.disabled = True
            await interaction.response.defer()  # defer the response to avoid timeout
            if not self.economy:
                await interaction.response.send_message("Economy cog not found. Please try again later.", ephemeral=True)
                return False
            if not self.item.purchasable(self.bot, interaction.user): # type: ignore
                await interaction.response.send_message(
                    f"You no longer are able to purchase this item." # Would be disabled otherwise
                )
                return False
            if interaction.user.id == self.bot.user.id: # type: ignore
                await interaction.response.send_message("You cannot purchase items for the bot.", ephemeral=True)
                return False
            # Remove coins
            self.economy.set(interaction.user.name, self.economy.get(interaction.user.name) - self.item.price)
            # run the on_buy function
            success = not (await self.item.on_buy(self.bot, interaction) == False) # Returning None is the same as True
            if not success:
                # The on_buy function should inform the user.
                self.economy.set(interaction.user.name, self.economy.get(interaction.user.name) + self.item.price)
                return False
            return True
        @discord.ui.button(label="▶️", style=discord.ButtonStyle.secondary)
        async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            if not interaction.message or not interaction.message.embeds:
                return await interaction.response.send_message(
                    "Unable to find the shop dialogue. Try opening a new one.", ephemeral=True
                )

            # Parse the current page number from the footer
            current_page = self._parse_page(interaction.message.embeds[0].footer.text or "Page 1/1 - Use the buttons below to navigate.")
            next_page = current_page + 1

            # Generate the next shop page
            embed, view = await self.shop.generate_shop_page(interaction.user, page=next_page)  # type: ignore

            # Edit the original message with the new embed and view
            await interaction.response.edit_message(embed=embed, view=view)
    async def generate_shop_page(self, user: discord.Member, page: int = 0) -> tuple[discord.Embed, discord.ui.View]:
        """Generates an embed for the shop page."""
        embed = discord.Embed(
            title="Eden Shop",
            description="Welcome to the Eden Shop! Here are the items you can purchase:",
            color=discord.Color.green()
        )
        shop = self.Shop()
        items: list["ShopItem"] = [item for item in shop if item.purchasable(self.bot, user)]
        embed.set_footer(text=f"Page {page + 1}/{len(items)} - Use the buttons below to navigate.")
        if not items:
            embed.description = "There are no items available for purchase at the moment."
            return embed, discord.ui.View()  # No items, return empty view
        
        item = items[page]
        
        embed.add_field(
            name=item.name,
            value=f"Cost: {item.price} coins\n",
        )

        buttons = self.ShopButtons(self.bot, items[page])
        if page <= 0:
            buttons.back_button.disabled = True
        if page >= len(items) - 1:
            buttons.next_button.disabled = True
        return embed, buttons

    @commands.command(name="shop")
    async def shop(self, ctx: commands.Context, page: int = 0):
        """Displays the shop items."""
        embed, view = await self.generate_shop_page(ctx.author, page) # type: ignore
        await ctx.send(embed=embed, view=view)

async def setup(bot: commands.Bot):
    """Function to load the cog."""
    await bot.add_cog(ShopCog(bot))
    print("ShopCog has been (re-)loaded.")
