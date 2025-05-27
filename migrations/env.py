from alembic import context
from sqlalchemy import engine_from_config, pool
from models.whisper import AsyncBase
import os

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
        target_metadata=AsyncBase.metadata
    )
    with context.begin_transaction():
        context.run_migrations()