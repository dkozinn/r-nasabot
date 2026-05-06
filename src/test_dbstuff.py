import os
import sqlite3

import pytest

from dbstuff import NasaDB


@pytest.fixture
def db():
    with open("posts.sql") as file:
        script = file.read()

    con = sqlite3.connect("/tmp/posts.db")
    with con:
        con.executescript(script)

    yield NasaDB("/tmp")
    con.close()
    os.remove("/tmp/posts.db")


# Test NasaDB insert method
def test_insert(db: NasaDB):
    db.insert("abc", 240)
    assert db.get_rank("abc") == 240


# Test NasaDB update method
def test_update(db: NasaDB):
    db.insert("abc", 240)
    db.update("abc", 999)
    assert db.get_rank("abc") == 999


# Test NasaDB get_rank method
def test_get_rank(db: NasaDB):
    db.insert("abc", 240)
    assert db.get_rank("abc") == 240
    assert db.get_rank("zzz") is None


# Test NasaDB initialization and deletion
def test_init_and_del(db: NasaDB):
    assert isinstance(db.connection, sqlite3.Connection)
    assert isinstance(db.cursor, sqlite3.Cursor)
    del db
    # Ensure connection is closed
    with pytest.raises(UnboundLocalError):
        db.cursor.execute("SELECT 1")


# Run the tests
if __name__ == "__main__":
    pytest.main()
