import os
from urllib.parse import urlparse

import psycopg2

# DB config
if os.environ["STAGE"] == "LIVE":
    url = urlparse(os.environ['DATABASE_URL'])
    dbname = url.path[1:]
    user = url.username
    password = url.password
    host = url.hostname
    port = url.port

    def connect_db():
        """
        Connect to Postgres SQL server (LIVE)
        """
        print('Connecting to Postgres db LIVE')
        try:
            conn = psycopg2.connect(
                dbname=dbname,
                user=user,
                password=password,
                host=host,
                port=port,
            )
            print('Connection to Postgres db successful')
        except psycopg2.Error as e:
            print(e.pgerror)
        return conn
else:
    def connect_db():
        """
        Connect to Postgres SQL server (DEV)
        """
        print('Connecting to the Postgres db DEV')
        try:
            conn = psycopg2.connect(
                dbname='',
                user='',
                host='',
                password='',
                port=''
            )
        except psycopg2.Error as e:
            print(e.pgerror)
        return conn


# Create bounty table
def create_table(connect_db):
    """
    Create sql table to host bounty information

    params:
    connect_db - connect db function
    """
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS participants
    (
        participant_id SERIAL PRIMARY KEYm
        date_joined VARCHAR(255) NOT NULL,
        telegram_id INTEGER NOT NULL,
        telegram_username VARCHAR(255) NOT NULL,
        chat_id INTEGER NOT NULL,
        ref_code VARCHAR(255) NOT NULL,
        twitter_username VARCHAR(255) NOT NULL,
        eth_address VARCHAR(255) NOT NULL,
        gains INTEGER NOT NULL
    )
    """)
    cursor.close()
    conn.commit()
    conn.close()
