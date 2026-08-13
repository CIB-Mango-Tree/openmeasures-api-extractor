from alembic import context
from sqlalchemy import engine_from_config, pool

# Metadata is only needed for `alembic revision --autogenerate`, which is a development-time
# activity run from the repo. The frozen application only ever runs `upgrade`/`stamp`, and
# importing the models there would couple migrations to the current model definitions.
try:
    from src.db.models.base import Base

    target_metadata = Base.metadata

except ImportError:
    target_metadata = None

config = context.config


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    # The application passes its own connection so migrations run on the same engine (and the
    # same SQLite file handle with its PRAGMAs) rather than opening a second one.
    connection = config.attributes.get("connection", None)

    if connection is not None:
        # render_as_batch matters on SQLite, which cannot ALTER most things in place; batch mode
        # rebuilds the table instead.
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )

        with context.begin_transaction():
            context.run_migrations()

        return

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as conn:
        context.configure(
            connection=conn, target_metadata=target_metadata, render_as_batch=True
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()

else:
    run_migrations_online()
