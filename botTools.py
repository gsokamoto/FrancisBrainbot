import sqlite3
from Event import Event

def sql_set_event(message_id, description, title, date, time, location, locationurl):
    conn = sqlite3.connect("events.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO events (message_id, title, descr, date, time, location, location_url) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (message_id, description, title, date, time, location, locationurl))
    conn.commit()
    conn.close()

def sql_update_event(message_id, description, title, date, time, location, locationurl):
    conn = sqlite3.connect("events.db")
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE events "
        "SET title = ?, descr = ?, date = ?, time = ?, location = ?, location_url = ? "
        "WHERE message_id = ?",
        (description, title, date, time, location, locationurl, message_id))
    conn.commit()
    conn.close()

def sql_get_event(message_id):
    conn = sqlite3.connect("events.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT message_id, title, descr, date, time, location, location_url "
        "FROM events "
        "WHERE message_id = ?",
        (message_id,))
    db_query = cursor.fetchall()
    conn.close()
    return db_query

def sql_update_add_attendee(message_id, user_id, host_flag=0, tentative_flag=0):
    conn = sqlite3.connect("events.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO attendees (message_id, user_id, host_flag, tentative_flag) "
        "VALUES (?, ?, ?, ?)",
        (message_id, user_id, host_flag, tentative_flag))
    conn.commit()
    conn.close()

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

def sql_get_attendees_list(message_id):
    db_query = sql_get_attendees(message_id)
    attendees = []
    if db_query:
        for attendee in db_query:
            attendees.append(attendee[0])
    return attendees

def sql_remove_attendee(message_id, user_id):
    conn = sqlite3.connect("events.db")
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM attendees "
        "WHERE message_id = ? AND user_id = ? AND host_flag = 0",
        (message_id, user_id))
    conn.commit()
    conn.close()

def regenerate_embed(interaction, curr_event, db_query, new_attendee=None):
    # CHANGE THIS TO PULL FROM ATTENDEES TABLE INSTEAD
    # if new_attendee is None:
    #     attendees = db_query[0][7]
    # if new_attendee:
    #      sql_update_add_attendee(new_attendee, )
        # attendee_id_string = db_query[0][7] + ',' + new_attendee
        # sql_update_event_attendee(new_attendee, new_attendee)
        # attendee_id_list = attendee_id_string.split(',')
        # attendee_name_list = botTools.id_to_display_name_list(interaction, attendee_id_list)
    attendees = sql_get_attendees_list(db_query[0][0])

    return curr_event.generate_event_embed(interaction,
        message_id=db_query[0][0], title=db_query[0][1], description=db_query[0][2], date=db_query[0][3],
        time=db_query[0][4], location=db_query[0][5], locationurl=db_query[0][6], attendees=attendees)

def generate_event(db_query):
    return Event(message_id=db_query[0][0], title=db_query[0][1], description=db_query[0][2], date=db_query[0][3], time=db_query[0][4], location=db_query[0][5], locationurl=db_query[0][6])

