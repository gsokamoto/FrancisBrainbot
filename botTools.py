import sqlite3
from Event import Event

# description: adds new event into events table
# parameters: message_id (str): event/message id,
#             description (str): event description,
#             title (str): event title,
#             date (str): event date,
#             time (str): event time,
#             location (str): event location,
#             locationurl (str): event location url
def sql_set_event(message_id, description, title, date, time, location, locationurl):
    conn = sqlite3.connect("events.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO events (message_id, title, descr, date, time, location, location_url) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (message_id, description, title, date, time, location, locationurl))
    conn.commit()
    conn.close()

# description: updates existing event in events table
# parameters: message_id (str): existing event/message id,
#             description (str): new event description,
#             title (str): new event title,
#             date (str): new event date,
#             time (str): new event time,
#             location (str): new event location,
#             locationurl (str): new event location url
#             completed_flag (int): new completed flag value
def sql_update_event(message_id, description, title, date, time, location, locationurl, completed_flag):
    conn = sqlite3.connect("events.db")
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE events "
        "SET title = ?, descr = ?, date = ?, time = ?, location = ?, location_url = ?, completed_flag = ? "
        "WHERE message_id = ?",
        (description, title, date, time, location, locationurl, message_id, completed_flag))
    conn.commit()
    conn.close()

# description: gets fields of existing event
# parameters: message_id (str): existing event/message id,
# return: tuple
def sql_get_event(message_id):
    conn = sqlite3.connect("events.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT message_id, title, descr, date, time, location, location_url, completed_flag "
        "FROM events "
        "WHERE message_id = ?",
        (message_id,))
    db_query = cursor.fetchall()
    conn.close()
    return db_query

# description: adds new attendee of event to attendees table
# parameters: message_id (str): event/message id,
#             user_id (str): user_id of new attendee,
#             host_flag (int): 0 if not creator of event, 1 if creator of event,
#             tentative_flag (int): 0 if attendee is going, 1 if attendee is tentatively going,
def sql_update_add_attendee(message_id, user_id, host_flag=0, tentative_flag=0):
    conn = sqlite3.connect("events.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO attendees (message_id, user_id, host_flag, tentative_flag) "
        "VALUES (?, ?, ?, ?)",
        (message_id, user_id, host_flag, tentative_flag))
    conn.commit()
    conn.close()

# description: updates existing attendee of event in attendees table to tentative
# parameters: message_id (str): existing event/message id,
#             user_id (str): user_id of existing attendee,
def sql_update_attendee_to_tentative(message_id, user_id):
    conn = sqlite3.connect("events.db")
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE attendees "
        "SET tentative_flag = 1 "
        "WHERE message_id = ? AND user_id = ?",
        (message_id, user_id))
    conn.commit()
    conn.close()

# description: updates existing attendee of event in attendees table to going
# parameters: message_id (str): existing event/message id,
#             user_id (str): user_id of existing attendee,
def sql_update_attendee_to_going(message_id, user_id):
    conn = sqlite3.connect("events.db")
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE attendees "
        "SET tentative_flag = 0 "
        "WHERE message_id = ? AND user_id = ?",
        (message_id, user_id))
    conn.commit()
    conn.close()

# description: updates existing event to compmleted in events table
# parameters: message_id (str): existing event/message id,
def sql_update_complete_event(message_id):
    conn = sqlite3.connect("events.db")
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE events "
        "SET completed_flag = 1 "
        "WHERE message_id = ?",
        (message_id,))
    conn.commit()
    conn.close()

# description: gets all attendees of specified event as tuple
# parameters: message_id (str): existing event/message id,
# return: tuple
def sql_get_attendees(message_id):
    conn = sqlite3.connect("events.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id, host_flag, tentative_flag "
        "FROM attendees "
        "WHERE message_id = ? "
        "ORDER BY host_flag DESC, tentative_flag ASC",
        (message_id,))
    db_query = cursor.fetchall()
    conn.close()
    return db_query

# description: gets all attendees of specified event as list
# parameters: message_id (str): existing event/message id,
# return: list
def sql_get_attendees_list(message_id):
    db_query = sql_get_attendees(message_id)
    attendees = []
    if db_query:
        for attendee in db_query:
            attendees.append(attendee[0])
    return attendees

# description: removes attendee from specified event in attendees table
# parameters: message_id (str): existing event/message id,
#             user_id (str): user_id of existing attendee,
def sql_remove_attendee(message_id, user_id):
    conn = sqlite3.connect("events.db")
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM attendees "
        "WHERE message_id = ? AND user_id = ? AND host_flag = 0",
        (message_id, user_id))
    conn.commit()
    conn.close()

# description: gets the host of the current event
# parameters: message_id (str): existing event/message id,
#             user_id (str): user_id of existing attendee,
# return str
def sql_get_host(message_id):
    conn = sqlite3.connect("events.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id "
        "FROM attendees "
        "WHERE message_id = ? AND host_flag = 1",
        (message_id,))
    db_query = cursor.fetchall()
    conn.close()
    return db_query[0][0]

# description: generates new embed using sql query to replace new values
# parameters: interaction (discord.interaction): current discord interaction
#             curr_event (Event): event before new edits,
#             db_query (tuple): sql query with all the new values to be used,
# return: embed
def regenerate_embed(interaction, curr_event, db_query):
    attendees = sql_get_attendees_list(db_query[0][0])

    return curr_event.generate_event_embed(interaction,
        message_id=db_query[0][0], title=db_query[0][1], description=db_query[0][2], date=db_query[0][3],
        time=db_query[0][4], location=db_query[0][5], locationurl=db_query[0][6], attendees=attendees)

# description: generates new event using sql query
# parameters: db_query (tuple): sql query with all the values to be used for event,
# return: Event
def generate_event(db_query):
    return Event(message_id=db_query[0][0], title=db_query[0][1], description=db_query[0][2], date=db_query[0][3], time=db_query[0][4], location=db_query[0][5], locationurl=db_query[0][6])

