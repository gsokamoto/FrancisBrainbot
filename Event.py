import discord
from datetime import datetime
import calendar
from pytz import timezone
import sqlite3


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

        self.message = None
        self.embed = None

        super().__init__()


    # description: generates the event embed
    # parameters: client(client): discord client object being used,
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

        event_datetime = self.__format_datetime(date, time)
        event_relative_datetime = calendar.timegm(event_datetime.utctimetuple())
        event_time = event_datetime.strftime("%I:%M %p %Z")
        event_date = event_datetime.strftime("%m/%d/%y")
        event_count = len(attendees)

        attendee_display_names = await self.__ids_to_display_names(curr_interaction)

        self.embed.add_field(name="Date:", value=event_date, inline=True)
        self.embed.add_field(name="Time:", value=event_time, inline=True)
        self.embed.add_field(name="Countdown:", value=f"<t:{event_relative_datetime}:R>", inline=True)
        if locationurl == "":
            self.embed.add_field(name="Location:", value=f"{location}")
        else:
            self.embed.add_field(name="Location:", value=f"[{location}]({locationurl})")
        # self.embed.add_field(name="Location:", value=f"[{self.locationurl}]({self.location})")
        # self.embed.add_field(name=f"[Location:] ({self.locationurl})", value=self.location, inline=True)
        self.embed.add_field(name=f"Attendees: ({event_count})", value="\n".join(attendee_display_names), inline=False)
        # self.embed.add_field(name="Event ID:", value=self.message_id, inline=True)
        self.embed.set_footer(text="Event ID: " + str(message_id))
        if completed_flag == 1:
            self.embed.title = self.__crossout_embed(self.embed.title)
            self.embed.description = self.__crossout_embed(self.embed.description)
            for idx, field in enumerate(self.embed.fields):
                self.embed.set_field_at(index=idx, name=field.name, value=self.__crossout_embed(field.value))

        # tank_emoji = botTools.generate_emoji(client, "tank")
        # self.embed.add_field(name=f"{tank_emoji} TANK({len(self.tank_list)})", value="\n".join(self.tank_list), inline=True)
        # dps_emoji = botTools.generate_emoji(client, "dps")
        # self.embed.add_field(name=f"{dps_emoji} DPS({len(self.dps_list)})", value="\n".join(self.dps_list), inline=True)
        # healer_emoji = botTools.generate_emoji(client, "healer")
        # self.embed.add_field(name=f"{healer_emoji} HEALER({len(self.healer_list)})", value="\n".join(self.healer_list), inline=True)

        return self.embed

    # def generate_event_embed(self, message_id, title, description, date, time, location, locationurl):
    #     self.embed = discord.Embed(
    #         title=self.title,
    #         description=self.description,
    #         color=discord.Color.green(),
    #     )
    #
    #     self.title = title
    #     self.description = description
    #     self.date = date
    #     self.time = time
    #     self.location = location
    #     self.locationurl = locationurl
    #
    #     event_datetime = self.__format_datetime()
    #     event_relative_datetime = calendar.timegm(event_datetime.utctimetuple())
    #     event_time = event_datetime.strftime("%I:%M %p %Z")
    #     event_date = event_datetime.strftime("%m/%d/%y")
    #     event_count = len(self.attendees)
    #
    #     self.embed.add_field(name="Date:", value=event_date, inline=True)
    #     self.embed.add_field(name="Time:", value=event_time, inline=True)
    #     self.embed.add_field(name="Countdown:", value=f"<t:{event_relative_datetime}:R>", inline=True)
    #
    #     self.embed.add_field(name="Location:", value=self.location, inline=True)
    #     self.embed.add_field(name=f"Attendees: ({event_count})", value="\n".join(self.attendees), inline=False)
    #     self.embed.set_footer(text="Event ID: " + str(message_id))
    #
    #     # tank_emoji = botTools.generate_emoji(client, "tank")
    #     # self.embed.add_field(name=f"{tank_emoji} TANK({len(self.tank_list)})", value="\n".join(self.tank_list), inline=True)
    #     # dps_emoji = botTools.generate_emoji(client, "dps")
    #     # self.embed.add_field(name=f"{dps_emoji} DPS({len(self.dps_list)})", value="\n".join(self.dps_list), inline=True)
    #     # healer_emoji = botTools.generate_emoji(client, "healer")
    #     # self.embed.add_field(name=f"{healer_emoji} HEALER({len(self.healer_list)})", value="\n".join(self.healer_list), inline=True)
    #
    #     return self.embed

    # description: adds annotations to embed that marks the raid as completed
    # parameters: client(client): discord client object being used,
    #             parse_link(str): post parse link for player reference
    # return: embed
    def completed_raid(self, parse_link=None):
        if self.embed is not None:
            self.embed.title = self.title + "(Completed)"
            if parse_link is not None:
                self.embed.add_field(name="PARSES", value=f"[click here to see this raid's parses]({parse_link})", inline=False)
        return self.embed



    # description: removes user from the raid list
    # parameters: display_name(str): display name of user
    # return: none

    def remove_from_raid(self, display_name):
        self.attendees.remove(display_name)

    def add_to_event(self, display_name):
        # self.tank_list = [x for x in self.tank_list if display_name not in x]
        # self.dps_list = [x for x in self.dps_list if display_name not in x]
        # self.healer_list = [x for x in self.healer_list if display_name not in x]
        # for member in self.members_list:
        #     if member.display_name is display_name:
        #         self.members_list.remove(member)
        self.attendees.append(display_name)

    def __crossout_embed(self, embed_text):
        # self.tank_list = [x for x in self.tank_list if display_name not in x]
        # self.dps_list = [x for x in self.dps_list if display_name not in x]
        # self.healer_list = [x for x in self.healer_list if display_name not in x]
        # for member in self.members_list:
        #     if member.display_name is display_name:
        #         self.members_list.remove(member)
        return "~~" + embed_text + "~~"

    def __format_datetime(self, date, time):
        # date formatting
        date_split = date.strip().split("/")
        event_month = date_split[0].strip().zfill(2)
        event_day = date_split[1].strip().zfill(2)
        event_year = datetime.now().year
        if len(date_split) == 3:
            event_year = date_split[2]
            if len(event_year) == 2:
                event_year = "20" + event_year
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

        # convert to datetime
        event_datetime = event_date_input + " " + event_time_input
        event_datetime = datetime.strptime(event_datetime, "%m/%d/%Y %I:%M %p").astimezone(timezone('US/Pacific'))

        return event_datetime

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

