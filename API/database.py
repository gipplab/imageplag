import ratiohash
import sqlite3
import os
import pandas as pd
import imagehash
import img_util
import ocr


class DBHandler(object):

    def __init__(self, database_path):
        self.database_path = database_path

        # connect to database, create if not exists
        self.db = sqlite3.connect(self.database_path)
        self.db.text_factory = str
        self.cursor = self.db.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS
        hashes(id TEXT, parent TEXT, phash TEXT, rhash TEXT, text TEXT,
        is_bar INTEGER, is_pure INTEGER, UNIQUE(id))''')

        # load db into pandas
        self.df = pd.read_sql_query("SELECT * from hashes", self.db)

    # the DBHandler will response for each action with an information string
    # the final result should always begin with: "Success" / "Duplicate" / "Error"
    # return should look like: "<response type>: <message>"
    def add_entry(self, id, parent, phash, rhash, text, is_bar, is_pure):

        # test, if id exists
        for row in self.cursor.execute("SELECT * FROM hashes WHERE id=?", (id, )):
            print("ID already exists!")
            return "Duplicate: ID already exists!"

        try:
            self.cursor.execute('''INSERT OR REPLACE INTO
                            hashes(id, parent, phash, rhash, text, is_bar,
                            is_pure)
                            VALUES(?,?,?,?,?,?,?)''',
                           [id,
                            parent,
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
            return "Error: " + er.message

        return "Success: Image added to database."

    def reload_db(self):
        # reload db into pandas
        self.df = pd.read_sql_query("SELECT * from hashes", self.db)

    def eval_phash(self, phash, df=None, thresh=0.01):
        if df is None:
            df = self.df.copy(deep=False)

        # drop unused columns
        df = df.loc[:, ["id", "parent", "phash"]]

        # add distance column to dataframe
        df['dist'] = ""

        phash = imagehash.hex_to_hash(phash)
        for index, row in df.iterrows():
            h2 = imagehash.hex_to_hash(row['phash'])
            dist = h2 - phash
            row.dist = dist
        df = df.sort_values(['dist'])

        match = img_util.eval_distances(df.dist)

        if match[1] < thresh:
            print('phash: No suspicious matches found!')
            return pd.DataFrame()
        else:
            df = df.head(match[0])
            df['score'] = match[1]
            df = df.loc[:, ['id', 'parent', 'score']]

        print('phash: Suspicious matches found!')

        return df

    def eval_rhash(self, rhash, df=None, thresh=0.01):
        if df is None:
            df = self.df.copy(deep=False)

        # drop unused columns
        df = df.loc[:, ["id", "parent", "rhash"]]

        # add distance column to dataframe
        df['dist'] = ""

        for index, row in df.iterrows():
            dist = ratiohash.distance(rhash, row['rhash'])
            row.dist = dist
        df = df.sort_values(['dist'])

        match = img_util.eval_distances(df.dist)

        if match[1] < thresh:
            print('rhash: No suspicious matches found!')
            return pd.DataFrame()
        else:
            df = df.head(match[0])
            df['score'] = match[1]
            df = df.loc[:, ['id', 'parent', 'score']]

        print('rhash: Suspicious matches found!')

        return df

    def eval_text(self, text, df=None, thresh=0.01):
        if df is None:
            df = self.df.copy(deep=False)

        # drop unused columns
        df = df.loc[:, ["id", "parent", "text"]]

        # add distance column to dataframe
        df['dist'] = ""

        for index, row in df.iterrows():
            dist = ocr.distance(text, row['text'])
            row.dist = dist
        df = df.sort_values(['dist'])

        match = img_util.eval_distances(df.dist, threshold=2.0)

        if match[1] < thresh:
            print('text: No suspicious matches found!')
            return pd.DataFrame()
        else:
            df = df.head(match[0])
            df['score'] = match[1]
            df = df.loc[:, ['id', 'parent', 'score']]

        print('text: Suspicious matches found!')

        return df
