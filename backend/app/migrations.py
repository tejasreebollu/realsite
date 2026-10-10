"""Idempotent compatibility upgrade for existing local demo databases."""
from sqlalchemy import inspect, text


def migrate(engine):
    with engine.begin() as connection:
        columns = {c["name"] for c in inspect(connection).get_columns("users")}
        if "role" not in columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'user'"))
        # Every public account can buy and sell; administrators remain separate.
        connection.execute(text("UPDATE users SET role = 'user' WHERE role IN ('buyer', 'seller')"))
        if connection.dialect.name == "postgresql":
            connection.execute(text("ALTER TABLE users ALTER COLUMN role SET DEFAULT 'user'"))
        if "demo" not in columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN demo BOOLEAN NOT NULL DEFAULT false"))
        user_additions = {
            "active": "BOOLEAN NOT NULL DEFAULT true", "phone": "VARCHAR(20) NOT NULL DEFAULT ''",
            "city": "VARCHAR(100) NOT NULL DEFAULT ''", "bio": "TEXT NOT NULL DEFAULT ''",
            "avatar_url": "VARCHAR(250) NOT NULL DEFAULT ''",
        }
        for name, definition in user_additions.items():
            if name not in columns:
                connection.execute(text(f"ALTER TABLE users ADD COLUMN {name} {definition}"))
        columns = {c["name"] for c in inspect(connection).get_columns("properties")}
        if "seed_key" not in columns:
            connection.execute(text("ALTER TABLE properties ADD COLUMN seed_key VARCHAR(120)"))
        connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_properties_seed_key ON properties (seed_key)"))
        additions = {
            "features": "JSON",
            "previous_price": "INTEGER",
            "area_unit": "VARCHAR(10) NOT NULL DEFAULT 'sqft'",
            "area_value": "FLOAT",
            "plot_use": "VARCHAR(20) NOT NULL DEFAULT ''",
            "plot_facing": "VARCHAR(20) NOT NULL DEFAULT ''",
            "road_width_ft": "INTEGER",
            "plot_approval": "VARCHAR(100) NOT NULL DEFAULT ''",
            "deposit": "INTEGER NOT NULL DEFAULT 0",
            "furnishing": "VARCHAR(20) NOT NULL DEFAULT 'Unfurnished'",
            "available_from": "VARCHAR(10)",
        }
        for name, definition in additions.items():
            if name not in columns:
                connection.execute(text(f"ALTER TABLE properties ADD COLUMN {name} {definition}"))
