"""
Alembic environment configuration.

This module is invoked by the Alembic command line interface and contains
the logic for running migrations.
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from alembic import context

# this is the Alembic Config object, which provides the values of the
# [alembic] section of the .ini file as Python dictionary for use here.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata

# Import models to make them available to Alembic
from app.models import Base

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    """
    Run the migration using the given connection.

    Args:
        connection: The database connection to use for migrations
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    In that case we need to create an AsyncEngine
    and associate a connection with the context.
    """
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = configuration["sqlalchemy.url"].replace(
        "postgresql+psycopg", "postgresql+asyncpg"
    )

    connectable = create_async_engine(
        configuration["sqlalchemy.url"],
        poolclass=None,  # Use NullPool for migrations
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """

    if context.is_offline_mode():
        run_migrations_offline()
    else:
        asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
