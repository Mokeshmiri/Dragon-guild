import sqlite3


DB_PATH = "db/guild.db"


# returns all quests
def list_quests():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM quests ORDER BY title")
    quests = cursor.fetchall()
    cursor.close()
    conn.close()
    return quests


# finds one quest by id
def get_quest(quest_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM quests WHERE id = ?", (quest_id,))
    quest = cursor.fetchone()
    cursor.close()
    conn.close()
    return quest


# creates a new quest
def create_quest(title, duration, quest_type, difficulty, description, image):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO quests(title, duration_minutes, quest_type, difficulty, description, image_filename)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (title, duration, quest_type, difficulty, description, image),
    )
    quest_id = cursor.lastrowid
    conn.commit()
    cursor.close()
    conn.close()
    return quest_id
