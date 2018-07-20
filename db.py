import os
from urllib.parse import urlparse
from datetime import date

import psycopg2
import shortuuid

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
                dbname='ak_test_db',
                user='postgres',
                host='localhost',
                password='#AmOakO64$',
                port='5432'
            )
            return conn, conn.cursor()
        except psycopg2.Error as e:
            print(e.pgerror)
       


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
    conn, cursor = connect_db()
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


def add_new_participant(connect_db, telegram_id, chat_id, telegram_username):
    """
    Adds a new participant to the bounty

    Args:
        connect_db (func): Connect db function
        telegram_id (int): Telegram ID of user
        chat_id (int): Telegram Chat ID of bot-user converstation
    """

    try:
        conn, cursor = connect_db()
        cursor.execute("""
                INSERT INTO
                participants
                (date_joined,
                telegram_id,
                chat_id,
                referral_code,
                wallet_address,
                telegram_username,
                twitter_username,
                facebook_profile_link,
                telegram_channel_reward,
                telegram_group_reward,
                twitter_reward,
                facebook_reward,
                referral_reward,
                referred_no)
                VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (date.today(),
                    telegram_id,
                    chat_id,
                    shortuuid.uuid(),
                    'n/a',
                    telegram_username,
                    'n/a',
                    'n/a',
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,))
        conn.commit()
        close_db_connection(conn, cursor)
    except psycopg2.Error as e:
        print(e.pgerror)


# rewards query

def get_total_rewards(connect_db):
    """
    Returns total reward allocated to participants

    Args:
        connect_db (func): Connect db function

    Returns:
        int: Total rewards allocated
    """

    conn, cursor = connect_db()

    try:
        cursor.execute("""
        SELECT
        SUM( telegram_channel_reward + twitter_reward)
        FROM participants
        """)
        
        total = cursor.fetchone()[0]
        print(total)
        close_db_connection(conn, cursor) 
        
        return total
    except psycopg2.Error as e:
        print(e.pgerror)


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
        SELECT telegram_channel_reward, telegram_group_reward, twitter_reward, facebook_reward, referral_reward
        FROM participants
        WHERE telegram_id=%s
        """,
        (telegram_id,)
        )


        telegram_channel, telegram_group, twitter, facebook, referrals = cursor.fetchone()
        total = telegram_channel + telegram_group + twitter + facebook + referrals
            
        close_db_connection(conn, cursor)
        return (telegram_channel, telegram_group, twitter, facebook, referrals, total)
    except psycopg2.Error as e:
        print(e.pgerror)


def get_user_referral_reward_and_referred_no(connect_db, referral_code):
    """
    Returns the referral_reward and number of people a user has referred

    Args:
        referral_code (str): Referral code of user

    Returns:
        tuple: (referral_reward, referred_no)
    """
    conn, cursor = connect_db()

    try:
        cursor.execute("""
        SELECT referral_reward, referred_no
        FROM particpants
        WHERE referral_code=%s
        """, (referral_code,))
        results = cursor.fetchone()
        close_db_connection(conn, cursor)
        
        return results
    except psycopg2.Error as e:
        print(e.pgerror)


def get_user_referred_no(connect_db, telegram_id):
    """
    Returns number of people a user has referred

    Args:
        connect_db (func): Connect DB function
        telegram_id (int): Telegram ID of user

    Returns:
        int: total number of people referred by user
    """
    conn, cursor = connect_db()

    try:
        # get total referred
        cursor.execute("""
        SELECT referred_no
        FROM participants
        WHERE telegram_id=%s
        """, (telegram_id,))
        referred_no = cursor.fetchone()[0]

        if referred_no is None:
            referred_no = 0
        
        close_db_connection(conn, cursor)
        return referred_no

    except psycopg2.Error as e:
        print(e.pgerror)


def update_user_referral_reward_and_referred_no(connect_db, referral_code, points):
    """
    Increases referral reward (by points per referred)
    and referred number (by 1)

    Args:
        connect_db (func): Connect DB function
        referral_code (str): Referral code of user
        points (int): Amount to reward
    """

    conn, cursor = connect_db()

    try:
       cursor.execute("""
        UPDATE participants SET referral_reward=%s, referred_no=%s WHERE referral_code=%s
        """, (
            referral_reward + points,
            referred_no + 1,
            referral_code)
            )
       conn.commit()
       close_db_connection(conn, cursor)
    except psycopg2.Error as e:
        print(e.pgerror)


def get_user_referral_code(connect_db, telegram_id):
    """
    Returns the referral code of a user

    Args:
        connect_db (func): Connect DB function
        telegram_id (int): Telegram ID of user

    Returns:
        str: Referral code of user
    """
    try:
        cursor.execute("""
        SELECT referral_code
        FROM participants
        WHERE telegram_id=%s
        """, (telegram_id,))
        referral_code = cursor.fetchone()[0]

        if referral_code:
            return referral_code
        else:
            return None
    except psycopg2.Error as e:
        print(e.pgerror)

