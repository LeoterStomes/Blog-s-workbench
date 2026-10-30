from sqlalchemy import inspect, text


def migrate_music_ownership(engine):
    """Add ownership to legacy music rows without deleting any user data."""
    inspector = inspect(engine)
    if "music" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("music")}
    with engine.begin() as connection:
        if "user_id" not in columns:
            connection.execute(text("ALTER TABLE music ADD COLUMN user_id BIGINT"))

        quoted_user = engine.dialect.identifier_preparer.quote("user")
        owner_id = connection.execute(
            text(f"SELECT id FROM {quoted_user} WHERE user_type = 2 ORDER BY id LIMIT 1")
        ).scalar()
        if owner_id is None:
            owner_id = connection.execute(
                text(f"SELECT id FROM {quoted_user} ORDER BY id LIMIT 1")
            ).scalar()
        if owner_id is not None:
            connection.execute(
                text("UPDATE music SET user_id = :owner_id WHERE user_id IS NULL"),
                {"owner_id": owner_id},
            )

        rows = connection.execute(
            text(
                "SELECT id, user_id, sort_order FROM music "
                "WHERE user_id IS NOT NULL "
                "ORDER BY user_id ASC, sort_order ASC, id DESC"
            )
        ).all()
        positions = {}
        for row in rows:
            positions[row.user_id] = positions.get(row.user_id, 0) + 1
            position = positions[row.user_id]
            if row.sort_order != position:
                connection.execute(
                    text("UPDATE music SET sort_order = :position WHERE id = :music_id"),
                    {"position": position, "music_id": row.id},
                )

    inspector = inspect(engine)
    indexes = {index["name"] for index in inspector.get_indexes("music")}
    if "ix_music_user_id" not in indexes:
        with engine.begin() as connection:
            connection.execute(
                text("CREATE INDEX ix_music_user_id ON music (user_id)")
            )
