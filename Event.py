import discord
import calendar
import sqlite3

from urllib.parse import urlparse
from pytz import timezone
from datetime import datetime


class Event:
    def __init__(self, message_id, title, description, date, time, location, locationurl="", attendees=[], completed_flag=0):
        self.message_id = message_id
        self.title = title
        self.description = description
        self.date = date
        self.time = time
        self.attendees = attendees
        self.location = location
        self.locationurl = locationurl
        self.completed_flag = completed_flag

        self.datetime = self.__format_datetime(date, time)
        self.embed = None

        super().__init__()


    # description: generates the event embed
    # parameters: curr_interaction (discord.interaction): the current discord interaction,
    #             message_id (str): new message id,
    #             title (str): new title,
    #             description (str): new description,
    #             date (str): new date,
    #             time (str): new time,
    #             location (str): new location,
    #             locationurl (str): new location URL,
    #             attendees (list): list of attendees as discord.user_id (str),
    #             completed_flag (int): new completed flag
    # return: embed
    async def generate_event_embed(self, curr_interaction, message_id=None, title=None, description=None, date=None, time=None, location=None, locationurl=None, attendees=None, completed_flag=None):
        if message_id is None:
            message_id = self.message_id
        else:
            self.message_id = message_id
        if title is None:
            title = self.title
        else:
            self.title = title
        if description is None:
            description = self.description
        else:
            self.description = description
        if date is None:
            date = self.date
        else:
            self.date = date
        if time is None:
            time = self.time
        else:
            self.time = time
        if location is None:
            location = self.location
        else:
            self.location = location
        if locationurl is None:
            locationurl = self.locationurl
        else:
            self.locationurl = locationurl
        if attendees is None:
            attendees = self.attendees
        else:
            self.attendees = attendees
        if completed_flag is None:
            completed_flag = self.completed_flag
        else:
            self.completed_flag = completed_flag


        description = description.replace("\\n", "\n")

        self.embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.green(),
        )

        if self.datetime is None:
            return None
        event_relative_datetime = calendar.timegm(self.datetime.utctimetuple())
        event_time = self.datetime.strftime("%I:%M %p %Z")
        event_date = self.datetime.strftime("%m/%d/%y")
        event_count = len(attendees)

        attendee_display_names = await self.__ids_to_display_names(curr_interaction)
        if not self.is_valid_url(locationurl):
            locationurl = ""

        self.embed.add_field(name="Date:", value=event_date, inline=True)
        self.embed.add_field(name="Time:", value=event_time, inline=True)
        self.embed.add_field(name="Countdown:", value=f"<t:{event_relative_datetime}:R>", inline=True)
        if locationurl == "":
            self.embed.add_field(name="Location:", value=f"{location}")
        else:
            self.embed.add_field(name="Location:", value=f"[{location}]({locationurl})")
        self.embed.add_field(name=f"Attendees: ({event_count})", value="\n".join(attendee_display_names), inline=False)
        self.embed.set_footer(text="Event ID: " + str(message_id))
        if completed_flag == 1:
            self.embed.title = self.__crossout_embed(self.embed.title)
            self.embed.description = self.__crossout_embed(self.embed.description)
            for idx, field in enumerate(self.embed.fields):
                self.embed.set_field_at(index=idx, name=field.name, value=self.__crossout_embed(field.value))

        return self.embed

    # description: adds cross out discord annotation
    # parameters: embed_text(str): the string to be modified,
    # return: str
    def __crossout_embed(self, embed_text):
        return "~~" + embed_text + "~~"

    # description: formats the date and time input to be used as datetime
    # parameters: date(str): the date as a string,
    #             time(str): the time as a string
    # return: datetime
    def __format_datetime(self, date, time):
        # validating date formatting
        if "/" not in date:
            return None
        date_split = date.strip().split("/")
        event_month = date_split[0].strip().zfill(2)
        event_day = date_split[1].strip().zfill(2)
        event_year = datetime.now().year
        if len(date_split) == 3:
            event_year = date_split[2]
            if len(event_year) == 2:
                event_year = "20" + event_year

        # validating datetime value type
        try:
            # validating month and day
            if not (1 <= int(event_month) <= 12 or 1 <= int(event_day) <= 31):
                return None
            event_date_input = event_month + "/" + event_day + "/" + str(event_year)

            # time formatting
            if ":" in time:
                time_split = time.strip().split(":", 1)
                event_hour = time_split[0].strip().zfill(2)
                event_minute = time_split[1][:-2].strip().zfill(2)
                event_meridiem = time_split[1][-2:].strip()
            else:
                event_hour = time.upper().replace("AM","").replace("PM","").strip().zfill(2) #time.strip()[1][:-2].strip().zfill(2)
                event_minute = "00"
                event_meridiem = time.strip()[-2:]

            if event_meridiem.upper() != "PM":
                event_meridiem = "AM"
            event_time_input = event_hour + ":" + event_minute + " " + event_meridiem

            # validating time
            if not (1 <= int(event_hour) <= 12 or 0 <= int(event_minute) <= 59):
                return None

            # convert to datetime
            event_datetime = event_date_input + " " + event_time_input

            event_datetime = datetime.strptime(event_datetime, "%m/%d/%Y %I:%M %p").astimezone(timezone('US/Pacific'))
        except ValueError:
            return None

        return event_datetime

    # description: converts tuple of attendees into a list with icons to be displayed on embed
    # parameters: curr_interaction(discord.interaction): the current discord interaction,
    # return: list
    async def __ids_to_display_names(self, curr_interaction):
        attendee_name_list = []
        for attendee_id in self.attendees:
            if attendee_id:
                member = await curr_interaction.guild.fetch_member(int(attendee_id))

                # add icons if necessary
                conn = sqlite3.connect("events.db")
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT host_flag, tentative_flag "
                    "FROM attendees "
                    "WHERE message_id = ? AND user_id = ?",
                    (self.message_id, attendee_id))
                db_query = cursor.fetchall()
                conn.close()
                curr_display_name = member.display_name
                if db_query and db_query[0][0] == 1:
                    curr_display_name = member.display_name + " (👑)"
                elif db_query and db_query[0][1] == 1:
                    curr_display_name = member.display_name + " (❓)"

                if member.display_name not in attendee_name_list:
                    attendee_name_list.append(curr_display_name)
        return attendee_name_list

    # description: validates URL
    # parameters: url (str): the url to be validated
    # return: bool
    def is_valid_url(self, url):
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False

    # description: validates URL
    # parameters: url (str): the url to be validated
    # return: bool
    def get_formatted_datetime(self):
        if datetime is not None:
            return self.datetime.strftime("%m/%d/%y %I:%M %p %Z")
        else:
            return None