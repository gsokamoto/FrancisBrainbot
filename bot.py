import discord
import pytz

from discord.ext import commands, tasks
from typing import Optional
from discord import app_commands
from dotenv import load_dotenv
from datetime import datetime, timedelta


import botTools
from Event import Event
import os
import sqlite3


def run_discord_bot():
    # global variables
    load_dotenv()
    client = commands.Bot(command_prefix="!", intents=discord.Intents.all())
    events_channel_id = 1018371752709083156
    tz_pacific = pytz.timezone("US/Pacific")

    # contains all persistent buttons to be used in the program
    class PersistentView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)

        @discord.ui.button(label="Attending", style=discord.ButtonStyle.green, emoji="🏃",
                           custom_id='FrancisBrainbot:green')
        async def attending_button_callback(self, interaction: discord.Interaction, button: discord.ui.button):

            db_query = botTools.sql_get_event(message_id=str(interaction.message.id))
            db_query2 = botTools.sql_get_attendees(str(interaction.message.id))
            for attendee in db_query2:
                if attendee[0] == str(interaction.user.id):
                    if attendee[2] == 0 or attendee[1] == 1:
                        await interaction.response.send_message(content="You're already going!",
                                                                ephemeral=True)
                        raise sqlite3.IntegrityError("Error: User is already going. Cannot add duplicates to attendees table")
                    elif attendee[2] == 1:
                        botTools.sql_update_attendee_to_going(interaction.message.id, interaction.user.id)
                        break
            else:
                botTools.sql_update_add_attendee(interaction.message.id, interaction.user.id, 0, 0)

            curr_event = botTools.generate_event(db_query)


            await interaction.message.edit(
                embed=await botTools.regenerate_embed(interaction, curr_event, db_query),
                view=PersistentView())
            await interaction.response.send_message(content="We'll see you there!", ephemeral=True)


        @discord.ui.button(label="Tentative", style=discord.ButtonStyle.blurple, emoji="❓",
                           custom_id='FrancisBrainbot:blurple')
        async def tentative_button_callback(self, interaction: discord.Interaction, button: discord.ui.button):
            db_query = botTools.sql_get_event(message_id=str(interaction.message.id))
            db_query2 = botTools.sql_get_attendees(str(interaction.message.id))
            for attendee in db_query2:
                if attendee[0] == str(interaction.user.id):
                    if attendee[1] == 1:
                        await interaction.response.send_message(content="You have to go! You're the host!",
                                                                ephemeral=True)
                        raise sqlite3.IntegrityError("Error: User is host. Tentative_flag must stay 0")
                    elif attendee[2] == 1:
                        await interaction.response.send_message(content="You're already tentatively going!",
                                                                ephemeral=True)
                        raise sqlite3.IntegrityError("Error: Tentative_flag is already 1")
                    elif attendee[2] == 0:
                        botTools.sql_update_attendee_to_tentative(interaction.message.id, interaction.user.id)
                        break
                botTools.sql_update_add_attendee(interaction.message.id, interaction.user.id, 0, 1)

                curr_event = botTools.generate_event(db_query)


                await interaction.message.edit(
                    embed=await botTools.regenerate_embed(interaction, curr_event, db_query),
                    view=PersistentView())
                await interaction.response.send_message(content="Hoping you'll make it!", ephemeral=True)

        @discord.ui.button(label="Not Going", style=discord.ButtonStyle.red, emoji="👻",
                           custom_id='FrancisBrainbot:red')
        async def not_going_button_callback(self, interaction: discord.Interaction, button: discord.ui.button):
            # get host id to check if user is host
            curr_event_host = botTools.sql_get_host(str(interaction.message.id))
            if curr_event_host == str(interaction.user.id):
                await interaction.response.send_message(content="You have to go! You're the host!",
                                                        ephemeral=True)
                raise sqlite3.IntegrityError("Error: Host cannot be removed from attendee table")
            botTools.sql_remove_attendee(str(interaction.message.id), str(interaction.user.id))

            db_query = botTools.sql_get_event(message_id=interaction.message.id)
            curr_event = botTools.generate_event(db_query)

            await interaction.message.edit(embed=await botTools.regenerate_embed(interaction, curr_event, db_query),
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
        if not upcoming_event_notification.is_running():
            upcoming_event_notification.start()
        synced = await client.tree.sync()
        print(str(len(synced)) + " synced")


    # list of channels that have access to this function
    def is_allowed_channel_hangouts():
        async def predicate(interaction: discord.Interaction):
            if interaction.channel.id not in [events_channel_id]:
                await interaction.response.send_message(content=f"Error: You cannot use this bot in this channel. Try again in {interaction.client.get_channel(1018371752709083156).name}.", ephemeral=True)
                raise InvalidChannelException("Error: The bot was called in an invalid channel")
            else:
                return True
        return app_commands.check(predicate)

    # sends event embed message
    @client.tree.command(name="create_event", description="creates a new embed message for an event")
    # @app_commands.checks.has_any_role("Admin", "Moderator")
    @is_allowed_channel_hangouts()
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
        new_embed = await curr_event.generate_event_embed(interaction)

        if new_embed is str:
            await curr_message.edit(content=f"Error: {new_embed}\nDeleting in 10 seconds", delete_after=10.0)
            raise ValueError
        else:
            await curr_message.edit(embed=new_embed, view=PersistentView())
        botTools.sql_set_event(curr_event.message_id, curr_event.title, curr_event.description, curr_event.date, curr_event.time, curr_event.location, curr_event.locationurl)

        db_query = botTools.sql_get_users()
        for user in db_query[0]:
            curr_user = await interaction.client.fetch_user(int(user))
            await curr_user.send(content=f">>> {interaction.user.display_name} created a new event!!!\n"
                                         f"Check it out here: {curr_message.jump_url}")
        # await curr_message.jump_url


    # edits existing event embed message
    @client.tree.command(name="edit_event", description="edits existing embed message for specified event")
    @is_allowed_channel_hangouts()
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

        db_query = botTools.sql_get_event(message_id)

        if not db_query:
            await interaction.response.send_message(content="Error: Invalid event id", ephemeral=True)
            raise IndexError
        curr_event = botTools.generate_event(db_query)
        new_embed = await curr_event.generate_event_embed(interaction, message_id=message_id, title=title, description=description,
                                date=date, time=time, location=location, locationurl=locationurl, attendees=botTools.sql_get_attendees_list(message_id))
        if new_embed is None:
            await interaction.response.send_message(content=f"Error: Invalid date or time", ephemeral=True)
            raise ValueError
        curr_message = await interaction.channel.fetch_message(int(message_id))
        await curr_message.edit(embed=new_embed)
        botTools.sql_update_event(curr_event.message_id, curr_event.title, curr_event.description, curr_event.date,
                               curr_event.time, curr_event.location, curr_event.locationurl)
        await interaction.response.send_message(content="event " + str(message_id) + " was updated successfully.", ephemeral=True)


    # mark event as completed
    @client.tree.command(name="complete_event", description="marks existing event as completed and no longer becomes interactable")
    @is_allowed_channel_hangouts()
    # @app_commands.checks.has_any_role("Admin", "Moderator")
    @app_commands.describe(message_id="EVENT ID")
    async def complete_event(interaction: discord.Interaction, message_id: str):
        message_id = message_id.strip()
        if not botTools.sql_get_event(message_id=message_id):
            await interaction.response.send_message(content="Error: Invalid event id", ephemeral=True)
            raise IndexError
        curr_message = await interaction.channel.fetch_message(int(message_id))
        botTools.sql_update_complete_event(message_id)
        db_query = botTools.sql_get_event(message_id)
        curr_event = botTools.generate_event(db_query)

        await curr_message.edit(embed= await curr_event.generate_event_embed(interaction, message_id=db_query[0][0], title=db_query[0][1], description=db_query[0][2],
                                date=db_query[0][3], time=db_query[0][4], location=db_query[0][5], locationurl=db_query[0][6], completed_flag=db_query[0][7], attendees=botTools.sql_get_attendees_list(message_id)),
                                view=None)
        await interaction.response.send_message(content="event " + str(message_id) + " was completed successfully.",
                                                ephemeral=True)

    # delete event message and from db
    @client.tree.command(name="delete_event", description="marks existing event as completed and no longer becomes interactable")
    @is_allowed_channel_hangouts()
    @app_commands.checks.has_any_role("Not Weird", "Broke Boy", "Stinky Smell Boy", "Saturn's Onion Rings", "Battlepass")
    @app_commands.describe(message_id="EVENT ID")
    async def delete_event(interaction: discord.Interaction, message_id: str):
        message_id = message_id.strip()
        if not botTools.sql_get_event(message_id=message_id):
            await interaction.response.send_message(content="Error: Invalid event id", ephemeral=True)
            raise IndexError
        curr_message = await interaction.channel.fetch_message(int(message_id))
        botTools.sql_remove_event(message_id)
        await curr_message.delete()
        await interaction.response.send_message(content="event " + str(message_id) + " was successfully deleted.",
                                                ephemeral=True)

    # enable notifications
    @client.tree.command(name="enable_notifications",
                         description="get DM notifications from FrancisBrainbot")
    # @is_allowed_channel_hangouts()
    # @app_commands.checks.has_any_role("Admin", "Moderator")
    async def enable_notifications(interaction: discord.Interaction):
        if str(interaction.user.id) in botTools.sql_get_users():
            await interaction.response.send_message(content="Error: You have already signed up.", ephemeral=True)
            raise IndexError
        botTools.sql_add_user(str(interaction.user.id))
        await interaction.response.send_message(content="You've successfully signed up.",
                                                ephemeral=True)
    # disable notifications
    @client.tree.command(name="disable_notifications",
                         description="no longer receive DOM notifications from FrancisBrainbot")
    # @is_allowed_channel_hangouts()
    # @app_commands.checks.has_any_role("Admin", "Moderator")
    async def disable_notifications(interaction: discord.Interaction):
        if str(interaction.user.id) not in botTools.sql_get_users():
            await interaction.response.send_message(content="Error: You were not signed up to begin with.", ephemeral=True)
            raise IndexError
        botTools.sql_remove_user(str(interaction.user.id))
        await interaction.response.send_message(content="You've successfully been removed.",
                                                ephemeral=True)

    # send notification if event is coming up through DM
    @tasks.loop(hours=24.0)
    async def upcoming_event_notification():
        users_list = [query for query in botTools.sql_get_users()[0]]
        event_list = []
        for query in botTools.sql_get_upcoming_events():
            event_list.append(botTools.generate_event_with_list(query))
        for event in event_list:
            now_aware = datetime.now(tz=tz_pacific)
            notification_datetime = event.datetime - timedelta(days=1)
            complete_event_reminder_datetime = event.datetime + timedelta(days=1)
            if notification_datetime <= now_aware <= event.datetime:
                intersecting_users = list(set(botTools.sql_get_attendees_list(event.message_id)).intersection(set(users_list)))
                if intersecting_users:
                    for user in intersecting_users:
                        curr_user = await client.fetch_user(int(user))
                        curr_channel = client.get_channel(events_channel_id)
                        curr_message = await curr_channel.fetch_message(int(event.message_id))
                        await curr_user.send(content=f">>> Don't forget about {event.title} at {event.get_formatted_datetime()}.\nMore details here: {curr_message.jump_url}")
            elif now_aware >= complete_event_reminder_datetime:
                curr_user = await client.fetch_user(botTools.sql_get_host(int(event.message_id)))
                curr_channel = client.get_channel(events_channel_id)
                curr_message = await curr_channel.fetch_message(int(event.message_id))
                await curr_user.send(content=f">>> Don't forget about to mark the following event as completed: {curr_message.jump_url}\n"
                                             f"Copy and paste `/complete_event message_id:{event.message_id}` into the following channel: {curr_channel.mention}")

    # custom exceptions
    class InvalidChannelException(Exception):
        pass

    client.run(os.environ['DISCORD_TOKEN'])