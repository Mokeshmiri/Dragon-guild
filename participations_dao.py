import sqlite3


DB_PATH = "db/guild.db"


# counts reserved places grouped by role
def session_role_counts(session_id, excluded_user=None):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    sql = "SELECT role, SUM(places) AS places FROM participations WHERE session_id = ?"
    values = [session_id]
    if excluded_user is not None:
        sql += " AND user_id <> ?"
        values.append(excluded_user)
    sql += " GROUP BY role"
    cursor.execute(sql, values)
    roles = cursor.fetchall()
    cursor.close()
    conn.close()
    return roles


# finds one user's participation in a session
def get_participation_by_user_session(user_id, session_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM participations WHERE user_id = ? AND session_id = ?",
        (user_id, session_id),
    )
    participation = cursor.fetchone()
    cursor.close()
    conn.close()
    return participation


# finds a participation by id
def get_participation(participation_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM participations WHERE id = ?", (participation_id,))
    participation = cursor.fetchone()
    cursor.close()
    conn.close()
    return participation


# creates a participation
def create_participation(user_id, session_id, role, places):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO participations(user_id, session_id, role, places) VALUES (?, ?, ?, ?)",
        (user_id, session_id, role, places),
    )
    conn.commit()
    cursor.close()
    conn.close()


# updates a participation
def update_participation(participation_id, role, places):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE participations SET role = ?, places = ? WHERE id = ?",
        (role, places, participation_id),
    )
    conn.commit()
    cursor.close()
    conn.close()


# deletes a participation
def delete_participation(participation_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM participations WHERE id = ?", (participation_id,))
    conn.commit()
    cursor.close()
    conn.close()


# counts the sessions joined by one user
def count_user_sessions(user_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) AS count FROM participations WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result["count"]


# returns all sessions joined by one user
def list_user_participations(user_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT participations.id AS participation_id,
               participations.role AS selected_role, participations.places,
               sessions.id AS session_id, sessions.day, sessions.start_time,
               sessions.location, quests.title, quests.duration_minutes,
               quests.quest_type, quests.difficulty, quests.image_filename
        FROM participations
        JOIN sessions ON sessions.id = participations.session_id
        JOIN quests ON quests.id = sessions.quest_id
        WHERE participations.user_id = ?
        ORDER BY sessions.day, sessions.start_time
        """,
        (user_id,),
    )
    participations = cursor.fetchall()
    cursor.close()
    conn.close()
    return participations
