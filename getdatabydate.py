import sqlite3


class GetDataByDate:
    def __init__(self, database, table, date):
        self.date = date
        self.database = database
        self.table = table

        self.conn = sqlite3.connect(self.database)
        self.cursor = self.conn.cursor()
        self.cursor.execute(
            f"SELECT * FROM {self.table} WHERE date = ?", (self.date,))
        self.data = self.cursor.fetchall()
        self.conn.close()
        return self.data
