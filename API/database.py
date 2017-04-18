
import sqlite3
import os
import pandas as pd
import imagehash
import img_util


class DBHandler(object):

    def __init__(self, database_path):
        self.database_path = database_path

        # connect to database, create if not exists
        self.db = sqlite3.connect(self.database_path)
        self.db.text_factory = str
        self.cursor = self.db.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS
        hashes(id TEXT, phash TEXT, rhash TEXT, text TEXT,
        is_bar INTEGER, is_pure INTEGER, UNIQUE(id))''')

        # load db into pandas
        self.df = pd.read_sql_query("SELECT * from hashes", self.db)

    def add_entry(self, id, phash, rhash, text, is_bar, is_pure):

        # test, if id exists
        for row in self.cursor.execute("SELECT * FROM hashes WHERE id=?", (id, )):
            print("ID already exists!")
            return "Fail - ID already exists!"

        try:
            self.cursor.execute('''INSERT OR REPLACE INTO
                            hashes(id, phash, rhash, text, is_bar,
                            is_pure)
                            VALUES(?,?,?,?,?,?)''',
                           [id,
                            phash,
                            rhash,
                            text,
                            is_bar,
                            is_pure])
            self.db.commit()
        except KeyboardInterrupt:
            raise
        except sqlite3.Error as er:
            print 'Error:', er.message
            return "Fail - Error:" + er.message

        return "Success - Image added to database."

    def reload_db(self):
        # reload db into pandas
        self.df = pd.read_sql_query("SELECT * from hashes", self.db)


    def eval_phash(self, phash):
        df = self.df.copy(deep=False)

        # drop unused columns
        df = df.loc[:, ["id", "phash"]]

        # add distance column to dataframe
        df['dist'] = ""

        phash = imagehash.hex_to_hash(phash)
        for index, row in df.iterrows():
            h2 = imagehash.hex_to_hash(row['phash'])
            dist = h2 - phash
            row.dist = dist
        df = df.sort_values(['dist'])

        match = img_util.eval_distances(df.dist)

        if match[1] < 0.5:
            print('No suspicious matches found!')
            return pd.DataFrame()
        else:
            df = df.head(match[0])
            df['score'] = match[1]
            df = df.loc[:, ['id', 'score']]

        print('Suspicious matches found!')
        print(df)

        return df


