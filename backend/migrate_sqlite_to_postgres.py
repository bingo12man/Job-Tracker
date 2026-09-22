import os

from dotenv import load_dotenv
from sqlalchemy import (
    MetaData,
    create_engine,
    select,
    text,
)

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is missing from .env"
    )

if DATABASE_URL.startswith("sqlite"):
    raise RuntimeError(
        "DATABASE_URL must point to PostgreSQL/Neon"
    )


# ----------------------------
# SOURCE: OLD SQLITE DATABASE
# ----------------------------

sqlite_engine = create_engine(
    "sqlite:///./jobs.db"
)

sqlite_metadata = MetaData()
sqlite_metadata.reflect(
    bind=sqlite_engine
)


# ----------------------------
# DESTINATION: NEON POSTGRES
# ----------------------------

postgres_engine = create_engine(
    DATABASE_URL
)

postgres_metadata = MetaData()
postgres_metadata.reflect(
    bind=postgres_engine
)


TABLE_ORDER = [
    "companies",
    "jobs",
    "applications",
]


def migrate_table(table_name):
    source_table = (
        sqlite_metadata.tables.get(
            table_name
        )
    )

    target_table = (
        postgres_metadata.tables.get(
            table_name
        )
    )

    if source_table is None:
        print(
            f"Skipping {table_name}: "
            "not found in SQLite"
        )
        return 0

    if target_table is None:
        print(
            f"Skipping {table_name}: "
            "not found in PostgreSQL"
        )
        return 0

    with sqlite_engine.connect() as source_conn:
        rows = (
            source_conn
            .execute(
                select(source_table)
            )
            .mappings()
            .all()
        )

    if not rows:
        print(
            f"{table_name}: 0 rows"
        )
        return 0

    # Only copy columns that exist
    # in both databases.
    target_columns = {
        column.name
        for column in target_table.columns
    }

    cleaned_rows = []

    for row in rows:
        cleaned_rows.append({
            key: value
            for key, value in dict(row).items()
            if key in target_columns
        })

    with postgres_engine.begin() as target_conn:
        target_conn.execute(
            target_table.insert(),
            cleaned_rows,
        )

    print(
        f"{table_name}: "
        f"{len(cleaned_rows)} rows migrated"
    )

    return len(cleaned_rows)


def reset_sequence(table_name):
    with postgres_engine.begin() as conn:
        conn.execute(
            text(
                f"""
                SELECT setval(
                    pg_get_serial_sequence(
                        '{table_name}',
                        'id'
                    ),
                    COALESCE(
                        (
                            SELECT MAX(id)
                            FROM {table_name}
                        ),
                        1
                    ),
                    true
                )
                """
            )
        )


def main():
    print(
        "\nSQLite → Neon migration\n"
    )

    totals = {}

    for table_name in TABLE_ORDER:
        totals[table_name] = (
            migrate_table(
                table_name
            )
        )

    print(
        "\nResetting PostgreSQL sequences..."
    )

    for table_name in TABLE_ORDER:
        if (
            table_name
            in postgres_metadata.tables
        ):
            reset_sequence(
                table_name
            )

    print("\nMigration complete.\n")

    for table_name, count in totals.items():
        print(
            f"{table_name}: {count}"
        )


if __name__ == "__main__":
    main()