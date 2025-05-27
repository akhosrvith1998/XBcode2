from alembic import context
from sqlalchemy import engine_from_config, pool
from models.whisper import Base
import os
from dotenv import load_dotenv

load_dotenv()
config = context.config
config.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL"))
connectable = engine_from_config(
    config.get_section(config.config_ini_section),
    prefix="sqlalchemy.",
    poolclass=pool.NullPool,
)

with connectable.connect() as connection:
    context.configure(
        connection=connection,
        target_metadata=Base.metadata
    )
    with context.begin():
        context.run_migrations()