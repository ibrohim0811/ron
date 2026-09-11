import asyncio
import os
from logging.config import fileConfig

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

# Model va Base'ni import qilamiz
from core.database import Base
import models  # Modellar autogenerate uchun yuklanishi shart

load_dotenv()

# Alembic Config
config = context.config

# .env dagi DATABASE_URL ni alembic.ini dagi url o'rniga o'rnatamiz
database_url = os.getenv("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

# Logging sozlamalari
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Autogenerate ishlashi uchun target_metadata ni belgilaymiz
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Offline rejimda migratsiyani ishga tushirish."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Asinxron engine yaratish va Neon DB uchun migratsiyani bajarish."""
    
    # Neon uchun connect_args
    connect_args = {}
    url = config.get_main_option("sqlalchemy.url")
    if url and "neon.tech" in url:
        import ssl
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        connect_args["ssl"] = ctx

    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args=connect_args
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Online rejimda (Asyncio orqali) migratsiyani ishga tushirish."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()