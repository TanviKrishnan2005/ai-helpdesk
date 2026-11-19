
from pathlib import Path

from sqlalchemy import MetaData, create_engine, select, text

from app.database import engine as target_engine


# Local SQLite database
SQLITE_PATH = Path(__file__).resolve().parent / "helpdesk.db"

source_engine = create_engine(
    f"sqlite:///{SQLITE_PATH.as_posix()}"
)

TABLES = [
    "users",
    "tickets",
    "conversations",
    "messages",
]


def migrate():
    if not SQLITE_PATH.exists():
        raise FileNotFoundError(
            f"SQLite database not found: {SQLITE_PATH}"
        )

    if target_engine.dialect.name != "postgresql":
        raise RuntimeError(
            "DATABASE_URL is not pointing to PostgreSQL."
        )

    source_metadata = MetaData()
    target_metadata = MetaData()

    source_metadata.reflect(bind=source_engine)

    # Explicitly reflect the Supabase public schema.
    target_metadata.reflect(
        bind=target_engine,
        schema="public"
    )

    print("Checking database tables...")

    for name in TABLES:
        if name not in source_metadata.tables:
            raise RuntimeError(
                f"SQLite table missing: {name}"
            )

        target_key = f"public.{name}"

        if target_key not in target_metadata.tables:
            raise RuntimeError(
                f"PostgreSQL table missing: {name}"
            )

    print("All four tables found.")

    migrated_counts = {}

    # One transaction: all records migrate or none do.
    with source_engine.connect() as source:
        with target_engine.begin() as target:

            # Prevent accidental duplicate migration.
            for name in TABLES:
                table = target_metadata.tables[
                    f"public.{name}"
                ]

                existing = target.execute(
                    select(table.c.id).limit(1)
                ).first()

                if existing is not None:
                    raise RuntimeError(
                        f"PostgreSQL table '{name}' is not empty. "
                        "Migration cancelled to prevent duplicates."
                    )

            print("Destination tables are empty.")
            print("Starting migration...\n")

            for name in TABLES:
                source_table = source_metadata.tables[name]

                target_table = target_metadata.tables[
                    f"public.{name}"
                ]

                rows = source.execute(
                    select(source_table)
                ).mappings().all()

                records = [
                    dict(row) for row in rows
                ]

                if records:
                    target.execute(
                        target_table.insert(),
                        records
                    )

                migrated_counts[name] = len(records)

                print(
                    f"{name}: {len(records)} records copied"
                )

            # Reset PostgreSQL ID sequences.
            for name in TABLES:
                target.execute(
                    text("""
                        SELECT setval(
                            pg_get_serial_sequence(
                                :table_name,
                                'id'
                            ),
                            COALESCE(
                                (SELECT MAX(id)
                                 FROM public.users),
                                1
                            ),
                            EXISTS (
                                SELECT 1
                                FROM public.users
                            )
                        )
                    """) if name == "users" else text("""
                        SELECT setval(
                            pg_get_serial_sequence(
                                :table_name,
                                'id'
                            ),
                            COALESCE(
                                (SELECT MAX(id)
                                 FROM public.""" + name + """),
                                1
                            ),
                            EXISTS (
                                SELECT 1
                                FROM public.""" + name + """
                            )
                        )
                    """),
                    {"table_name": f"public.{name}"}
                )

    print("\nMigration completed successfully!")
    print("\nMigration summary:")

    for name, count in migrated_counts.items():
        print(f"{name}: {count}")

    print(
        "\nTotal records migrated:",
        sum(migrated_counts.values())
    )


if __name__ == "__main__":
    try:
        migrate()

    except Exception as error:
        print("\nMIGRATION FAILED:")
        print(error)
        raise

    finally:
        source_engine.dispose()
        target_engine.dispose()
