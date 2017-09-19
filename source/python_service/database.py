import sqlite3, os


class Database():
    def __init__(self, filename):
        self.db = sqlite3.connect(filename)
        self.c = self.db.cursor()


    def get_tap_pos(self, tap_id):
        self.c.execute("SELECT tap_pos FROM taps WHERE tap_id=?", str(tap_id))
        return self.c.fetchone()[0]

    def get_drinks(self):
        self.c.execute("SELECT drink_id, drink_name FROM drinks")
        return self.c.fetchall()

    def get_drink_detail(self, drink_id):
        self.c.execute("SELECT drink_name, drink_description FROM drinks WHERE  drink_id = ?", str(drink_id))
        return self.c.fetchone();
