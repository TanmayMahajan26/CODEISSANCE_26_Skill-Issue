import sqlite3

def check_db():
    conn = sqlite3.connect('nexus360.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print("Database Tables and Row Counts:")
    for table in tables:
        table_name = table[0]
        cursor.execute(f"SELECT count(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"{table_name}: {count} rows")

if __name__ == '__main__':
    check_db()
