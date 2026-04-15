import sqlite3
import os
db_path = 'backend/banho_tosa.db'
print(f'DB exists: {os.path.exists(db_path)}')
print(f'DB size: {os.path.getsize(db_path) if os.path.exists(db_path) else 0}')
if os.path.exists(db_path):
    try:
        conn = sqlite3.connect(db_path, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print('Tables:', tables)
        conn.close()
    except Exception as e:
        print('Error:', e)
