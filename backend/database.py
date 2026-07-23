from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import get_settings

settings = get_settings()

is_sqlite = settings.DATABASE_URL.startswith("sqlite")
connect_args = {"check_same_thread": False} if is_sqlite else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True if not is_sqlite else False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all tables and apply any missing column migrations. Call on startup."""
    from models.user import User          # noqa
    from models.scan import Scan          # noqa
    from models.post_result import PostResult  # noqa
    Base.metadata.create_all(bind=engine)
    _migrate_schema()


def _migrate_schema():
    """
    Lightweight forward-only migration: adds any columns that exist in the ORM
    models but are missing from the live database tables. Safe for SQLite and PostgreSQL.
    """
    from sqlalchemy import text, inspect

    inspector = inspect(engine)

    migrations = {
        "scans": {
            "report_hash": "VARCHAR(64)",
            "pdf_hash":    "VARCHAR(64)",
        },
    }

    with engine.connect() as conn:
        for table, columns in migrations.items():
            if inspector.has_table(table):
                existing = {col["name"] for col in inspector.get_columns(table)}
                for col_name, col_type in columns.items():
                    if col_name not in existing:
                        if is_sqlite:
                            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}"))
                        else:
                            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col_name} {col_type}"))
        conn.commit()
