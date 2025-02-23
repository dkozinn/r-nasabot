#!/usr/bin/python3

""" Define the NasaDB class """

import sqlite3


class NasaDB:
    """database functions for nasabot"""

    dbname = "posts.db"

    def __init__(self, dbdir):
        """open database, pass in full path to database"""

        self.connection = sqlite3.connect(dbdir + "/" + self.dbname)
        self.cursor = self.connection.cursor()

    def __del__(self):
        self.connection.close()

    def insert(self, sub_id, rank, timestamp=0):
        """Insert submission ID and rank into DB"""
        self.cursor.execute("INSERT INTO posts VALUES (?, ?, ?)", (sub_id, rank, timestamp))
        self.connection.commit()

    def update(self, sub_id, rank, timestamp=0):
        """Update the rank for the submission"""
        self.cursor.execute(
            "UPDATE posts SET rank=?, ts=? WHERE submission=?", (rank, timestamp, sub_id)
        )
        self.connection.commit()

    def get_rank(self, sub_id):
        """Get the current rank for the submission or return None if it doesn't exist"""
        result = self.cursor.execute(
            "SELECT rank FROM posts WHERE submission=?", (sub_id,)
        ).fetchone()
        if result is not None:
            return result[0]
        return None


# Code below to be used for debug testing

# with open("posts.sql") as file:
#     script = file.read()

# con = sqlite3.connect("/tmp/posts.db")
# with con:
#     con.executescript(script)

# x = NasaDB("/tmp")
# #x.executescript(script)

# x.update("abd", 999)
# x.insert("abc", 240)

# print(x.get_rank("abc"))    #expect 240
# print(x.get_rank("zzz"))    #expect None
