import os
from urllib.parse import urlparse
from datetime import date

import psycopg2
import shortuuid

try:
    from local_db import db_config

    def connect_db():
        """
        Connect to Postgres SQL server (DEV)
        """
        print('Connecting to the Postgres db DEV')
        try:
            conn = psycopg2.connect(
                dbname= db_config['dbname'],
                user= db_config['user'],
                host= db_config['host'],
                password=db_config['password'],
                port=db_config['port']
            )
            return conn, conn.cursor()
        except psycopg2.Error as e:
            print(e.pgerror)
except ImportError:
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
        print(telegram_id)

        participant = cursor.fetchone()
        return participant
        close_db_connection(conn, cursor)
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
                email,
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
        FROM participants
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
    try:
        conn, cursor = connect_db()

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
        old_referral_reward (int): Old referral reward

    """

    try:
       conn, cursor = connect_db()

       results = get_user_referral_reward_and_referred_no(connect_db, referral_code)
       old_referral_reward = results[0]
       old_referred_no = results[1]

       cursor.execute("""
        UPDATE participants SET referral_reward=%s, referred_no=%s WHERE referral_code=%s
        """, (
            old_referral_reward + points,
            old_referred_no + 1,
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
        conn, cursor = connect_db()
        cursor.execute("""
        SELECT referral_code
        FROM participants
        WHERE telegram_id=%s
        """, (telegram_id,))
        referral_code = cursor.fetchone()[0]

        if referral_code:
            close_db_connection(conn, cursor)
            return referral_code
        else:
            close_db_connection(conn, cursor)
            return None
    except psycopg2.Error as e:
        print(e.pgerror)


def set_user_task_reward(connect_db, telegram_id, points, task_column=None, task_reward_column=None, entry=None):
    """
    Adds reward to user's telegram group pot

    Args:
        connect_db (func): Connect DB function
        telegram_id (int): Telegram ID of user
        task_column (str): Save task entry here
        task_reward_column (str): Save task points here
        entry (str): Entry to update database
        points (int): Points to reward user
    """
    try:
        conn, cursor = connect_db()
        # update db
        if entry:
            cursor.execute("""
            UPDATE participants
            SET {}=%s, {}=%s
            WHERE telegram_id=%s
            """.format(task_column, task_reward_column),
            (entry, points, telegram_id))
        else:
            cursor.execute("""
            UPDATE participants
            SET {}=%s
            WHERE telegram_id=%s
            """.format(task_reward_column,),
            (points, telegram_id))
        conn.commit()
        close_db_connection(conn, cursor)
    except psycopg2.Error as e:
        print(e.pgerror)


def set_user_wallet_address(wallet_address, telegram_id):
    """ Save user address """
    try:
        conn, cursor = connect_db()

        # save wallet address
        cursor.execute("""
        UPDATE participants
        SET wallet_address=%s
        WHERE telegram_id=%s
        """, (wallet_address, telegram_id))
        conn.commit()
        close_db_connection(conn, cursor)
    except psycopg2.Error as e:
        print(e.pgerror)


