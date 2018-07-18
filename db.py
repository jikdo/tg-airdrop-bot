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


def close_db_connection(conn, cursor):
    """
    Closes db connection

    Args:
        conn (obj): Connection object
        cursor (obj): Cursor object

    Returns:
        -
    """
    conn.close()
    cursor.close()


# Create bounty table
def create_table(connect_db):
    """
    Create sql table to host bounty information

    Args:
    connect_db - connect db function
    """
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS participants
    (
        participant_id SERIAL PRIMARY KEY,
        date_joined VARCHAR(255) NOT NULL,
        telegram_id INTEGER NOT NULL,
        chat_id INTEGER NOT NULL,
        referral_code VARCHAR(255) NOT NULL,
        wallet_address VARCHAR(255) NOT NULL,
        telegram_username VARCHAR(255) NOT NULL,
        twitter_username VARCHAR(255) NOT NULL,
        facebook_profile_link VARCHAR(355) NOT NULL,
        telegram_channel_reward INTEGER NOT NULL,
        telegram_group_reward INTEGER NOT NULL,
        twitter_reward INTEGER NOT NULL,
        facebook_reward INTEGER NOT NULL,
        referral_reward INTEGER NOT NULL,
        referred_no INTEGER NOT NULL
    )
    """)
    conn.commit()
    close_db_connection(conn, cursor)


def add_youtube_column(connect_db):
    """
    add share bounty colum
    
    params:
    connect_db - connect db function
    """
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
    ALTER TABLE participants
    ADD COLUMN IF NOT EXISTS youtube_name VARCHAR(255)
    """)

    cursor.close()
    conn.commit()
    conn.close()



def get_user_rewards(connect_db, telegram_id):
    """
    Get rewards of a user

    Args:
        connect_db (func): connect_db function
        telegram_id (str): Telegram ID of user

    Returns:
        tuple: (telegram_channel, telegram_group, twitter, facebook, referrals, total)

        or

        None: if no user reward was found

    Raises:
        pyscopg2.Error: When there is error with dealing with the database
    """

    # get rewards
    try:
        # connect to database
        conn, cursor = connect_db()

        cursor.execute("""
        SELECT telegram_channel, telegram_group, twitter, facebook, referrals)
        FROM participants
        WHERE telegram_id=%s
        """,
        (telegram_id,)
        )


        if cursor.fetchone()[0]:
            telegram_channel, telegram_group, twitter, facebook, referrals = cursor.fetchone()[0]
            total = telegram_channel + telegram_group + twitter + facebook + referrals
            
            close_db_connection(conn, cursor)
            return (telegram_channel, telegram_group, twitter, facebook, referrals, total)
        else:
            close_db_connection(conn, cursor)
            return None
    except psycopg2.Error as e:
        print(e.pgerror)


def is_participant(connect_db, telegram_id):
    """
    Checks if user is already a participant

    Args:
        telegram_id (int): Telegram ID of participant

    Returns:
        bool: Returns True if user is a participant else False
    """

    try:
        conn, cursor = connect_db()
        cursor.execute("""
        SELECT * FROM participants WHERE telegram_id=%s
        """,
        (telegram_id,))

        participant = cursor.fetchone()

        if participant:
            return True
        else:
            return False
    except psycopg2.Error as e:
        print(e.pgerror)


def get_total_rewards(connect_db):
    """
    

def add_new_participant(connect_db, **kargs):
    pass