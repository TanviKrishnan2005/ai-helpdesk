
import sqlite3
from pathlib import Path

# Matches the database path used by the backend
DATABASE_PATH = Path(__file__).resolve().parent / "helpdesk.db"


def migrate_database():
    if not DATABASE_PATH.exists():
        print(f"Database not found: {DATABASE_PATH}")
        print("Start the backend once to create the database, then rerun.")
        return

    connection = sqlite3.connect(DATABASE_PATH)

    try:
        cursor = connection.cursor()

        cursor.execute("PRAGMA table_info(tickets)")
        columns = [column[1] for column in cursor.fetchall()]

        if "user_id" not in columns:
            cursor.execute(
                "ALTER TABLE tickets ADD COLUMN user_id INTEGER "
                "REFERENCES users(id)"
            )
            print("Added user_id column to tickets.")
        else:
            print("user_id column already exists.")

        connection.commit()
        print("Database migration completed successfully.")

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    migrate_database()
