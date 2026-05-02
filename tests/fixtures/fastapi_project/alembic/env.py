from __future__ import annotations

from alembic import context

target_metadata = None


def run_migrations_online() -> None:

    connectable = context.config.attributes.get("connection")

    with connectable.connect() as connection:

        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():

            context.run_migrations()
