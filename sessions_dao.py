import sqlite3


DB_PATH = "db/guild.db"

SESSION_QUERY = """
    SELECT sessions.id AS session_id, sessions.quest_id, sessions.day,
           sessions.start_time, sessions.location, quests.title,
           quests.duration_minutes, quests.quest_type, quests.difficulty,
           quests.description, quests.image_filename
    FROM sessions
    JOIN quests ON quests.id = sessions.quest_id
"""


# returns sessions using the selected filters
def list_sessions(filters):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    sql = SESSION_QUERY + " WHERE 1 = 1"
    values = []

    if "day" in filters:
        sql += " AND sessions.day = ?"
        values.append(filters["day"])
    if "quest_type" in filters:
        sql += " AND quests.quest_type = ?"
        values.append(filters["quest_type"])
    if "difficulty" in filters:
        sql += " AND quests.difficulty = ?"
        values.append(filters["difficulty"])

    sql += " ORDER BY sessions.day, sessions.start_time"
    cursor.execute(sql, values)
    sessions = cursor.fetchall()
    cursor.close()
    conn.close()
    return sessions


# finds one session with its quest information
def get_session(session_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(SESSION_QUERY + " WHERE sessions.id = ?", (session_id,))
    session = cursor.fetchone()
    cursor.close()
    conn.close()
    return session


# returns all sessions connected to one quest
def list_sessions_for_quest(quest_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        SESSION_QUERY + " WHERE sessions.quest_id = ? ORDER BY sessions.day, sessions.start_time",
        (quest_id,),
    )
    sessions = cursor.fetchall()
    cursor.close()
    conn.close()
    return sessions


# returns sessions using one location on one day
def list_sessions_by_day_location(day, location):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT sessions.id AS session_id, sessions.day, sessions.start_time,
               sessions.location, quests.duration_minutes
        FROM sessions
        JOIN quests ON quests.id = sessions.quest_id
        WHERE sessions.day = ? AND sessions.location = ?
        """,
        (day, location),
    )
    sessions = cursor.fetchall()
    cursor.close()
    conn.close()
    return sessions


# creates a new quest session
def create_session(quest_id, day, start_time, location):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO sessions(quest_id, day, start_time, location) VALUES (?, ?, ?, ?)",
        (quest_id, day, start_time, location),
    )
    conn.commit()
    cursor.close()
    conn.close()


# updates a quest session
def update_session(session_id, day, start_time, location):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE sessions SET day = ?, start_time = ?, location = ? WHERE id = ?",
        (day, start_time, location, session_id),
    )
    conn.commit()
    cursor.close()
    conn.close()


# deletes a quest session
def delete_session(session_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    conn.commit()
    cursor.close()
    conn.close()
