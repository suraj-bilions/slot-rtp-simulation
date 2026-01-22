# db.py
import psycopg2
import json
import os
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

def store_spin_db(spin_id, grid, total_bet, total_win, is_free_spin=False):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO slot_spins
        (spin_id, grid, total_bet, total_win, is_free_spin)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (spin_id) DO NOTHING
        """,
        (
            str(spin_id),
            json.dumps(grid),
            total_bet,
            total_win,
            is_free_spin
        )
    )

    conn.commit()
    cur.close()
    conn.close()
