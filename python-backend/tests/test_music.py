import tempfile
import unittest
from unittest.mock import patch

from sqlalchemy import BigInteger, create_engine, inspect, text
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker

from database import Base
from models import Music, User
from schema_migrations import migrate_music_ownership
from services import music_service


@compiles(BigInteger, "sqlite")
def compile_big_integer_as_sqlite_integer(type_, compiler, **kw):
    return "INTEGER"


class MusicOwnershipTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(
            bind=self.engine,
            tables=[User.__table__, Music.__table__],
        )
        self.db = sessionmaker(bind=self.engine)()
        self.db.add_all([
            User(id=1, username="alice", password="hashed", user_type=1),
            User(id=2, username="bob", password="hashed", user_type=1),
            Music(id=11, user_id=1, title="Alice song", artist="A", url="/a.mp3"),
            Music(id=22, user_id=2, title="Bob song", artist="B", url="/b.mp3"),
        ])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_list_returns_only_current_users_music(self):
        tracks = music_service.get_list(self.db, user_id=1)

        self.assertEqual([track["id"] for track in tracks], [11])
        self.assertEqual(tracks[0]["title"], "Alice song")

    def test_user_cannot_update_another_users_music(self):
        changed = music_service.update(
            self.db,
            user_id=1,
            mid=22,
            data={"title": "Stolen"},
        )

        self.assertFalse(changed)
        self.db.expire_all()
        self.assertEqual(self.db.get(Music, 22).title, "Bob song")

    def test_user_cannot_delete_another_users_music(self):
        deleted = music_service.delete(self.db, user_id=1, mid=22)

        self.assertFalse(deleted)
        self.db.expire_all()
        self.assertIsNotNone(self.db.get(Music, 22))

    def test_upload_assigns_music_to_current_user(self):
        with tempfile.TemporaryDirectory() as music_dir:
            with patch.object(music_service, "MUSIC_DIR", music_dir):
                result = music_service.upload_and_create(
                    self.db,
                    file_content=b"audio",
                    filename="Artist - Song.mp3",
                    title="Song",
                    artist="Artist",
                    user_id=1,
                )

        alice_tracks = music_service.get_list(self.db, user_id=1)
        bob_tracks = music_service.get_list(self.db, user_id=2)
        self.assertIn(result["id"], [track["id"] for track in alice_tracks])
        self.assertNotIn(result["id"], [track["id"] for track in bob_tracks])
        self.assertEqual(self.db.get(Music, result["id"]).user_id, 1)

    def test_upload_rejects_unsupported_file_types(self):
        with self.assertRaisesRegex(ValueError, "不支持的音频格式"):
            music_service.upload_and_create(
                self.db,
                file_content=b"not audio",
                filename="notes.txt",
                title="Notes",
                artist="",
                user_id=1,
            )

    def test_sort_orders_are_normalized_from_one_without_changing_relative_order(self):
        self.db.get(Music, 11).sort_order = 9
        self.db.add_all([
            Music(id=12, user_id=1, title="Alice second", artist="A", url="/a2.mp3", sort_order=9),
            Music(id=13, user_id=1, title="Alice third", artist="A", url="/a3.mp3", sort_order=9),
        ])
        self.db.commit()

        changed = music_service.normalize_sort_orders(self.db, user_id=1)
        tracks = music_service.get_list(self.db, user_id=1)

        self.assertTrue(changed)
        self.assertEqual([track["id"] for track in tracks], [13, 12, 11])
        self.assertEqual([track["sort_order"] for track in tracks], [1, 2, 3])


class MusicMigrationTest(unittest.TestCase):
    def test_legacy_music_is_assigned_to_admin_without_data_loss(self):
        engine = create_engine("sqlite:///:memory:")
        with engine.begin() as connection:
            connection.execute(
                text('CREATE TABLE "user" (id INTEGER PRIMARY KEY, user_type INTEGER NOT NULL)')
            )
            connection.execute(
                text("CREATE TABLE music (id INTEGER PRIMARY KEY, title TEXT NOT NULL, url TEXT NOT NULL, sort_order INTEGER)")
            )
            connection.execute(
                text('INSERT INTO "user" (id, user_type) VALUES (7, 2), (8, 1)')
            )
            connection.execute(
                text("INSERT INTO music (id, title, url, sort_order) VALUES (1, 'Legacy', '/legacy.mp3', 999), (2, 'Legacy 2', '/legacy2.mp3', 999)")
            )

        migrate_music_ownership(engine)
        migrate_music_ownership(engine)

        columns = {column["name"] for column in inspect(engine).get_columns("music")}
        indexes = {index["name"] for index in inspect(engine).get_indexes("music")}
        with engine.connect() as connection:
            owner_id = connection.execute(
                text("SELECT user_id FROM music WHERE id = 1")
            ).scalar_one()
            title = connection.execute(
                text("SELECT title FROM music WHERE id = 1")
            ).scalar_one()
            sort_orders = connection.execute(
                text("SELECT id, sort_order FROM music ORDER BY sort_order")
            ).all()

        self.assertIn("user_id", columns)
        self.assertIn("ix_music_user_id", indexes)
        self.assertEqual(owner_id, 7)
        self.assertEqual(title, "Legacy")
        self.assertEqual([row.sort_order for row in sort_orders], [1, 2])
        engine.dispose()


if __name__ == "__main__":
    unittest.main()
