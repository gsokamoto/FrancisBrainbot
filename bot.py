import discord
from discord.ext import commands
from typing import Optional
from discord import app_commands
from dotenv import load_dotenv
from os import environ

import botTools
from Event import Event
from Specs import Specs
import os
import responses
import sqlite3


def run_discord_bot():
    # global variables
    load_dotenv()
    client = commands.Bot(command_prefix="!", intents=discord.Intents.all())

    # contains all persistent buttons to be used in the program
    class PersistentView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)

        @discord.ui.button(label="Attending", style=discord.ButtonStyle.green, emoji="🏃",
                           custom_id='FrancisBrainbot:green')
        async def attending_button_callback(self, interaction: discord.Interaction, button: discord.ui.button):
            try:
                db_query = botTools.sql_get_event(message_id=str(interaction.message.id))
                db_query2 = botTools.sql_get_attendees(str(interaction.message.id))
                for attendee in db_query2:
                    if attendee[0] == str(interaction.user.id):
                        if attendee[2] == 0:
                            raise sqlite3.IntegrityError()
                        elif attendee[2] == 1:
                            botTools.sql_update_attendee_to_going(interaction.message.id, interaction.user.id)
                            break
                else:
                    botTools.sql_update_add_attendee(interaction.message.id, interaction.user.id, 0, 0)
                # botTools.sql_update_add_attendee(interaction.message.id, interaction.user.id, 0, 1)
                curr_event = botTools.generate_event(db_query)

                # botTools.sql_update_event_attendee(interaction.message.id,curr_event.attendees)
                await interaction.message.edit(
                    embed=await botTools.regenerate_embed(interaction, curr_event, db_query, str(interaction.user.id)),
                    view=PersistentView())
                await interaction.response.send_message(content="We'll see you there!", ephemeral=True)
            except sqlite3.IntegrityError:
                await interaction.response.send_message(content="You're already going!", ephemeral=True)


        @discord.ui.button(label="Tentative", style=discord.ButtonStyle.blurple, emoji="❓",
                           custom_id='FrancisBrainbot:blurple')
        async def tentative_button_callback(self, interaction: discord.Interaction, button: discord.ui.button):
            try:
                db_query = botTools.sql_get_event(message_id=str(interaction.message.id))
                db_query2 = botTools.sql_get_attendees(str(interaction.message.id))
                for attendee in db_query2:
                    if attendee[0] == str(interaction.user.id):
                        if attendee[2] == 1:
                            raise sqlite3.IntegrityError()
                        elif attendee[2] == 0:
                            botTools.sql_update_attendee_to_tentative(interaction.message.id, interaction.user.id)
                            break
                else:
                    botTools.sql_update_add_attendee(interaction.message.id, interaction.user.id, 0, 1)
                # botTools.sql_update_add_attendee(interaction.message.id, interaction.user.id, 0, 1)
                curr_event = botTools.generate_event(db_query)


                await interaction.message.edit(
                    embed=await botTools.regenerate_embed(interaction, curr_event, db_query, str(interaction.user.id)),
                    view=PersistentView())
                await interaction.response.send_message(content="Hoping you'll make it!", ephemeral=True)
            except sqlite3.IntegrityError:
                await interaction.response.send_message(content="You're already tentatively going!", ephemeral=True)

        @discord.ui.button(label="Not Going", style=discord.ButtonStyle.red, emoji="👻",
                           custom_id='FrancisBrainbot:red')
        async def not_going_button_callback(self, interaction: discord.Interaction, button: discord.ui.button):
            # db_query = botTools.sql_get_event(message_id=interaction.message.id)
            # curr_event = botTools.generate_event(db_query)
            # curr_event.add_to_event(interaction.user.id)
            botTools.sql_remove_attendee(str(interaction.message.id), str(interaction.user.id))


            # convert attendee_id list back to attendee_display_name list
            # attendee_id_string = db_query[0][7]
            # attendee_id_list = attendee_id_string.split(',')
            # attendee_name_list = []
            # for attendee_id in attendee_id_list:
            #     if attendee_id:
            #         member = await interaction.guild.fetch_member(int(attendee_id))
            #         if str(member.id) == attendee_id:
            #             attendee_id_list.remove(attendee_id)
            #         elif member.display_name not in attendee_name_list:
            #             attendee_name_list.append(member.display_name)
            db_query = botTools.sql_get_event(message_id=interaction.message.id)
            curr_event = botTools.generate_event(db_query)
            # botTools.sql_update_event_attendee(interaction.message.id, ','.join(attendee_id_list))
            # botTools.sql_update_event_attendee(interaction.message.id,curr_event.attendees)
            await interaction.message.edit(embed=await botTools.regenerate_embed(interaction, curr_event, db_query, botTools.sql_get_attendees_list(interaction.message.id)),
                                           view=PersistentView())
            await interaction.response.send_message(content="We'll miss you!", ephemeral=True)

    # class that initializes on startup to ensure old buttons can be used
    class PersistentViewBot(commands.Bot):
        def __init__(self):
            intents = discord.Intents.default()
            intents.message_content = True

            super().__init__(command_prefix=commands.when_mentioned_or('$'), intents=intents)

        async def setup_hook(self) -> None:
            # Register the persistent view for listening here.
            # Note that this does not send the view to any message.
            # In order to do this you need to first send a message with the View, which is shown below.
            # If you have the message_id you can also pass it as a keyword argument, but for this example
            # we don't have one.
            self.add_view(PersistentView())

    client = PersistentViewBot()

    @client.event
    async def on_ready():
        # Setting 'Playing ' status
        await client.change_presence(activity=discord.Game(name=f"League of Legends"))
        synced = await client.tree.sync()
        print(str(len(synced)) + " synced")

    # sends event embed message
    @client.tree.command(name="create_event", description="creates a new embed message for an event")
    # @app_commands.checks.has_any_role("Admin", "Moderator")
    @app_commands.describe(title="Event name/title")
    @app_commands.describe(description="What are we doing?")
    @app_commands.describe(date="M/D Format")
    @app_commands.describe(time="H:M AM/PM Format")
    @app_commands.describe(location="Where are we holding the event?")
    @app_commands.describe(locationurl="Link to the location of the event?")
    async def create_event(interaction: discord.Interaction, title: str, description: str, date: str, time: str, location: str, locationurl: Optional[str] = ""):
        # await interaction.response.send_message(embed=curr_event.generate_event_embed(),view=View())
        await interaction.response.defer()
        # await interaction.followup.send(embed=curr_event.generate_event_embed(),view=View())

        curr_message = await interaction.original_response()
        botTools.sql_update_add_attendee(str(curr_message.id), str(interaction.user.id), 1)
        curr_event = Event(curr_message.id, title, description, date, time, location, locationurl, [str(interaction.user.id)])
        await curr_message.edit(embed=await curr_event.generate_event_embed(interaction), view=PersistentView())
        botTools.sql_set_event(curr_event.message_id, curr_event.title, curr_event.description, curr_event.date, curr_event.time, curr_event.location, curr_event.locationurl)

    # edits existing event embed message
    @client.tree.command(name="edit_event", description="edits existing embed message for specified event")
    # @app_commands.checks.has_any_role("Admin", "Moderator")
    @app_commands.describe(message_id="EVENT ID")
    @app_commands.describe(title="Event name/title")
    @app_commands.describe(description="What are we doing?")
    @app_commands.describe(date="M/D/Y Format")
    @app_commands.describe(time="H:M AM/PM Format")
    @app_commands.describe(location="Where are we holding the event?")
    @app_commands.describe(locationurl="Link to the location of the event?")
    async def edit_event(interaction: discord.Interaction, message_id: str, title: Optional[str] = None, description: Optional[str]= None,
                         date: Optional[str] = None, time: Optional[str] = None, location: Optional[str] = None, locationurl: Optional[str] = None):
        message_id = message_id.strip()
        curr_message = await interaction.channel.fetch_message(int(message_id))
        db_query = botTools.sql_get_event(message_id)
        curr_event = botTools.generate_event(db_query)

        await curr_message.edit(embed= await curr_event.generate_event_embed(interaction, message_id=message_id, title=title, description=description,
                                date=date, time=time, location=location, locationurl=locationurl, attendees=botTools.sql_get_attendees_list(message_id)))
        botTools.sql_update_event(curr_event.message_id, curr_event.title, curr_event.description, curr_event.date,
                               curr_event.time, curr_event.location, curr_event.locationurl)
        await interaction.response.send_message(content="event #" + str(message_id) + " was updated successfully.", ephemeral=True)

    # # mark raid as completed
    # @client.tree.command(name="complete_raid", description="marks existing raid as completed and no longer becomes interactable")
    # # @app_commands.checks.has_any_role("Admin", "Moderator")
    # @app_commands.describe(message_id="RAID ID WITHOUT \"#\"")
    # @app_commands.describe(parse_link = "enter the parse link")
    # async def complete_event(interaction: discord.Interaction, message_id: int, parse_link: str = None):
    #
    #     if message_id in raids_dict:
    #         curr_raid = raids_dict.pop(message_id)
    #         if parse_link is not None and len(parse_link) > 14 and parse_link[0:41].startswith("https://vanilla.warcraftlogs.com/reports/"):
    #             for member in curr_raid.members_list:
    #                 await member.send(content=f"Parse for {curr_raid.title} in Classic WoW SoD on {curr_raid.date} at {curr_raid.time}: {parse_link}")
    #         await curr_raid.message.edit(embed=curr_raid.completed_raid(parse_link), view=None)
    #         await interaction.response.send_message(content="raid #" + str(message_id) + " has been completed successfully.", ephemeral=True)
    #     else:
    #         await interaction.response.send_message(content="Invalid raid_id or link", ephemeral=True)

    # bot.run(os.environ['DISCORD_TOKEN'])
    # client = ViewBot()

    # interactive buttons and drop-down menu
    # class Select(discord.ui.View):
    #     def __init__(self, message_id=None):
    #         self.message_id = message_id
    #         self.curr_spec = None
    #         self.users_usage = []
    #         self.views_list = []
    #
    #         super().__init__()
    #
    #     async def update_embed(self, interaction):
    #         self.users_usage.append(interaction.user.id)

            # await interaction.response.edit_message(embed=raids_dict[self.message_id].generate_raid_embed(client), view=self)
        #
        # def verify(self, interaction):
        #     return interaction.user.id in self.users_usage or self.curr_spec is None
        #
        # async def verify_message(self, interaction):
        #     if interaction.user.id in self.users_usage:
        #         await interaction.response.send_message(content="You have already signed up", ephemeral=True)
        #     elif self.curr_spec is None:
        #         await interaction.response.send_message(content="Please select a spec first", ephemeral=True)

        # @discord.ui.button(label="tanking", style=discord.ButtonStyle.blurple)
        # async def tanking(self, interaction: discord.Interaction, Button: discord.ui.Button):
        #     if self.verify(interaction):
        #         self.verify_message()
        #     else:
        #         raids_dict[self.raid_id].tank_list.append(botTools.generate_emoji(client, specs.getClass(self.curr_spec)) + interaction.user.display_name + botTools.generate_emoji(client, specs.getEmojiCode(self.curr_spec)))
        #         raids_dict[self.raid_id].members_list.append(interaction.user)
        #         self.views_list.append(Button)
        #         await self.update_embed(interaction)
        #
        # @discord.ui.button(label="attending", style=discord.ButtonStyle.blurple)
        # async def attending(self, interaction: discord.Interaction, Button: discord.ui.Button):
        #     if self.verify(interaction):
        #         self.verify_message()
        #     else:
        #         # raids_dict[self.raid_id].dps_list.append(botTools.generate_emoji(client, specs.getClass(self.curr_spec)) + interaction.user.display_name + botTools.generate_emoji(client, specs.getEmojiCode(self.curr_spec)))
        #         # raids_dict[self.raid_id].members_list.append(interaction.user)
        #         self.views_list.append(Button)
        #         await self.update_embed(interaction)
        #
        # @discord.ui.button(label="healing", style=discord.ButtonStyle.blurple)
        # async def healing(self, interaction: discord.Interaction, Button: discord.ui.Button):
        #     if self.verify(interaction):
        #         self.verify_message()
        #     else:
        #         raids_dict[self.raid_id].healer_list.append(botTools.generate_emoji(client, specs.getClass(self.curr_spec)) + interaction.user.display_name + botTools.generate_emoji(client, specs.getEmojiCode(self.curr_spec)))
        #         raids_dict[self.raid_id].members_list.append(interaction.user)
        #         self.views_list.append(Button)
        #         await self.update_embed(interaction)
        #
        #
        # @discord.ui.button(label="bail", style=discord.ButtonStyle.red)
        # async def missing(self, interaction: discord.Interaction, Button: discord.ui.Button):
        #     if interaction.user.id in self.users_usage:
        #         self.users_usage.remove(interaction.user.id)
        #         raids_dict[self.raid_id].remove_from_raid(interaction.user.display_name)
        #         await interaction.response.edit_message(embed=raids_dict[self.raid_id].generate_raid_embed(client), view=self)
        #         self.views_list.append(Button)
        #     else:
        #         await interaction.response.defer()
        #
        # @discord.ui.select(placeholder="select spec", options=spec_list)
        # async def callback(self, interaction: discord.Interaction, select):
        #     self.curr_spec = select.values[0]
        #     self.views_list.append(select)
        #     # await interaction.response.edit_message(view=self)
        #     await interaction.response.defer()

    # #error handlers
    # @create_event.error
    # async def create_event_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    #     await interaction.response.send_message(content=str(error), ephemeral=True)
    client.run(os.environ['DISCORD_TOKEN'])
