#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright(c) 2018
# Kofi Amanfo <expl00ra@protonmail.com>

# This program is the sole property of www.airdropking.io

"""
This module is the engine of a telegram bounty and referral bot
designed to enhance visibilty for ICOs
"""

import logging
import json
from datetime import date
import re
import os

from telegram.ext import (
    Updater,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackQueryHandler,
)

from telegram import (
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
import shortuuid
import psycopg2

from db import (
    connect_db,
    create_table,
    is_participant,
    add_new_participant,
    get_total_rewards,
    get_user_referral_reward_and_referred_no,
    update_user_referral_reward_and_referred_no,
)

from menu import (
    menu_markup,
    menu_relayer
)

# log data
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
    )

# get config
with open(r'config.json', 'r') as file:
    config = json.loads(file.read())

# create table
create_table(connect_db)


updater = Updater(os.environ['TG_ACCESS_TOKEN'])
dispatcher = updater.dispatcher


def start(bot, update, args=None):
    """
    Collect eth address from participant for registration
    """
    telegram_id = update.message.from_user.id
    telegram_username = update.message.from_user.username
    if telegram_username is None:
        telgram_username = 'n/a'
    chat_id = update.message.chat_id

    total = get_total_rewards(connect_db)
    if total is None:
        total = 0

    if total >= config['rewards']['cap']:
        bot.send_message(
            chat_id=update.message.chat_id,
            text="Bounty completed.\nAllocated tokens finished. Visit our community for more info {}".format(config['social']['telegram_group']),
            disable_web_page_preview=True
        )
        print('airdrop shared ::: ' + str(total))
    else:
        if not is_participant(connect_db, telegram_id):
            # add new participant
            add_new_participant(connect_db, telegram_id, chat_id, telegram_username)
            print("new participant added")

            # award referer
            if args:
                referral_code = args[0]
                results = get_user_referral_reward_and_referred(connect_db, referral_code)
                referral_reward = results[0]
                referred_no = results[1]

                # reward referrer
                update_user_referral_reward_and_referred_no(connect_db, referral_code, config['rewards']['referral'])
             
            bot.send_message(
                chat_id=update.message.chat_id,
                text=config['messages']['start_msg'].format(config['ICO_name']),
                disable_web_page_preview=True,
                reply_markup=menu_markup
            )
        else:
            bot.send_message(
                chat_id=update.message.chat_id,
                text="You are already in the campaign",
                reply_markup=menu_markup
                )


# def check_airdrop_count(bot, update):

def ask_eth_address(bot, update):
    """ ask eth address """
    bot.send_message(
        chat_id=update.message.chat_id,
        text='- Enter your ethereum wallet address.\n- MyEtherWallet(MEW) recommended.'
    )
    return "receive_eth_address"


def receive_eth_address(bot, update):
    """ receive eth address """
    conn = connect_db()
    cursor = conn.cursor()

    telegram_id = update.message.from_user.id
    eth_address = update.message.text
    print(eth_address)
    eth_pattern = re.compile(r'^0x[a-fA-F0-9]{40}$')
    is_eth_address = eth_pattern.match(eth_address)

    if eth_address.lower() == "skip":
        bot.send_message(
            chat_id=update.message.chat_id,
            text="Process skipped"
        )
        return ConversationHandler.END

    if is_eth_address:
        # update db
        cursor.execute("""
        UPDATE participants SET eth_address=%s WHERE telegram_id=%s
        """, (eth_address, telegram_id))
        cursor.close()
        conn.commit()
        conn.close()
        bot.send_message(
            chat_id=update.message.chat_id,
            text="Wallet address saved",
            disable_web_page_preview=True,
            parse_mode="Markdown"
        )

        bot.send_message(
            chat_id=update.message.chat_id,
            text="Complete a task to earn {} tokens".format(config['ticker']),
        )
        return ConversationHandler.END
    else:
        bot.send_message(
            chat_id=update.message.chat_id,
            text="Invalid erc20 address. Please send me a valid one or send 'skip' to end process.",
            parse_mode="Markdown"
        )
        return "receive_eth_address"


def ask_twitter_username(bot, update):
    """
    Ask twitter name
    """
    """ ask eth address """
    bot.send_message(
        chat_id=update.effective_user.id,
        text=config['messages']['twitter_task'].format(
            config['social']['twitter'],
        ),
        parse_mode='Markdown',
        disable_web_page_preview=True,
    )
    return "receive_twitter_username"


def receive_twitter_username(bot, update):
    """
    Recieve twitter username
    """
    conn = connect_db()
    cursor = conn.cursor()

    telegram_id = update.message.from_user.id
    twitter_username = update.message.text.lower()

    # Cancel step
    if twitter_username == "skip":
        bot.send_message(
            chat_id=update.message.chat_id,
            text="Process skipped"
        )
        return ConversationHandler.END

    # verify if username starts with @
    if twitter_username[0] is not '@':
        bot.send_message(
            chat_id=update.message.chat_id,
            text="Invalid. Please start with '@' or type 'skip' to end this process."
        )
        return "receive_twitter_username"

    # get gains
    cursor.execute("""
    SELECT gains FROM participants WHERE telegram_id=%s
    """, (telegram_id,))
    gains = cursor.fetchone()[0]

    # get twitter_username
    cursor.execute("""
    SELECT twitter_username FROM participants WHERE telegram_id=%s
    """, (telegram_id,))
    old_twitter_username = cursor.fetchone()[0]

    if old_twitter_username == 'n/a':
        # update db
        cursor.execute("""
        UPDATE participants SET twitter_username=%s, gains=%s WHERE telegram_id=%s
        """, (twitter_username, gains + config['rewards']['twitter'], telegram_id))
    else:
        cursor.execute("""
        UPDATE participants SET twitter_username=%s WHERE telegram_id=%s
        """, (twitter_username, telegram_id))
    cursor.close()
    conn.commit()
    conn.close()

    bot.send_message(
        chat_id=update.message.chat_id,
        text=config['messages']['done_msg'].format(
            config['social']['telegram_group'],
            config['social']['telegram_channel'],
        ),
        parse_mode='Markdown',
        disable_web_page_preview=True,
    )
    # return 'receive_facebook_link'
    return ConversationHandler.END


def ask_facebook_name(bot, update, user_data=None):
    """
    Ask facebook username
    """

    try:
        bot.send_message(
            chat_id=update.effective_user.id,
            text=config['messages']['facebook_task'].format(
                config['social']['facebook'],
            ),
            parse_mode='Markdown',
            disable_web_page_preview=True,
        )
        return "receive_facebook_name"
    except:
        pass


def receive_facebook_name(bot, update):
    """
    Receive facebook link
    """
    try:
        conn = connect_db()
        cursor = conn.cursor()

        telegram_id = update.message.from_user.id
        facebook_name = update.message.text

        if facebook_name.lower() == "skip":
            bot.send_message(
                chat_id=update.message.chat_id,
                text="Process skipped"
            )
            return ConversationHandler.END

        # get gains
        cursor.execute("""
        SELECT gains FROM participants WHERE telegram_id=%s
        """, (telegram_id,))
        gains = cursor.fetchone()[0]

        # get twitter_username
        cursor.execute("""
        SELECT facebook_name FROM participants WHERE telegram_id=%s
        """, (telegram_id,))
        old_facebook_name = cursor.fetchone()[0]

        if old_facebook_name == 'n/a':
            # update db
            cursor.execute("""
            UPDATE participants SET facebook_name=%s, gains=%s WHERE telegram_id=%s
            """, (facebook_name, gains + config['rewards']['facebook'], telegram_id))
        else:
            cursor.execute("""
            UPDATE participants SET facebook_name=%s WHERE telegram_id=%s
            """, (facebook_name, telegram_id))
        cursor.close()
        conn.commit()
        conn.close()

        bot.send_message(
            chat_id=update.message.chat_id,
            text=config['messages']['done_msg'],
            disable_web_page_preview=True,
        )
        return ConversationHandler.END
    except:
        pass


def ask_youtube_name(bot, update, user_data=None):
    """
    Ask youtube name
    """
    print('youtube called')
    try:
        bot.send_message(
            chat_id=update.effective_user.id,
            text=config['messages']['youtube_task'].format(
                config['social']['youtube'],
            ),
            parse_mode='Markdown',
            disable_web_page_preview=True,
        )
        return "receive_youtube_name"
    except:
        print('error thrown')


def receive_youtube_name(bot, update):
    """
    Receive youtube name
    """
    try:
        conn = connect_db()
        cursor = conn.cursor()

        telegram_id = update.message.from_user.id
        youtube_name = update.message.text

        if youtube_name.lower() == "skip":
            bot.send_message(
                chat_id=update.message.chat_id,
                text="Process skipped"
            )
            return ConversationHandler.END

        # get gains
        cursor.execute("""
        SELECT gains FROM participants WHERE telegram_id=%s
        """, (telegram_id,))
        gains = cursor.fetchone()[0]

        # get twitter_username
        cursor.execute("""
        SELECT youtube_name FROM participants WHERE telegram_id=%s
        """, (telegram_id,))
        old_youtube_name = cursor.fetchone()[0]
        print(old_youtube_name)
        if old_youtube_name is None:
            # update db
            cursor.execute("""
            UPDATE participants SET youtube_name=%s, gains=%s WHERE telegram_id=%s
            """, (youtube_name, gains + config['rewards']['youtube'], telegram_id))
        else:
            cursor.execute("""
            UPDATE participants SET youtube_name=%s WHERE telegram_id=%s
            """, (youtube_name, telegram_id))
        cursor.close()
        conn.commit()
        conn.close()

        bot.send_message(
            chat_id=update.message.chat_id,
            text=config['messages']['done_msg'],
            disable_web_page_preview=True,
        )
        return ConversationHandler.END
    except psycopg2.Error as e:
        print(e.pgerror)


def list_rules(bot, update):
    """ send rules of the bounty """
    try:
        bot.send_message(
            chat_id=update.message.chat_id,
            text=config['messages']['rules_msg'],
            disable_web_page_preview=True,
        )
    except:
        pass


def get_gains(bot, update):
    """
    Displays reward earned by participant
    """
    conn = connect_db()
    cursor = conn.cursor()

    telegram_id = update.message.from_user.id

    try:
        # gains total
        cursor.execute("""
        SELECT gains FROM participants WHERE telegram_id=%s
        """, (telegram_id, ))
        gains = cursor.fetchone()[0]

        if gains:
            # get total referred
            cursor.execute("""
            SELECT referred_no FROM participants WHERE telegram_id=%s
            """, (telegram_id,))
            referred_no = cursor.fetchone()[0]

            bot.send_message(
                chat_id=update.message.chat_id,
                text=config['messages']['gains_msg'].format(
                    gains,
                    config['ticker'],
                    referred_no),
                display_web_page_preview=True,
            )
            cursor.close()
            conn.commit()
            conn.close()
    except:
        bot.send_message(
            chat_id=update.message.chat_id,
            text='- Your info not available\n- Use /start to register'
        )


def get_referral_link(bot, update):
    """
    Displays referral link of user
    """
    conn = connect_db()
    cursor = conn.cursor()

    telegram_id = update.message.from_user.id

    try:
        cursor.execute("""
        SELECT ref_code FROM participants WHERE telegram_id=%s
        """, (telegram_id, ))
        ref_code = cursor.fetchone()[0]

        if ref_code:
            reflink = "https://t.me/{}?start=".format(config['bot_uname']) + ref_code

            bot.send_message(
                chat_id=update.message.chat_id,
                text=config['messages']['invite_msg'].format(
                    config['ICO_name'],
                    reflink
                    )
            )
            bot.send_message(
                chat_id=update.message.chat_id,
                text=config['messages']['fwd_invite_msg'].format(
                    config['rewards']['referral'],
                    config['ticker'],
                ),
                disable_web_page_preview=True,
            )
    except:
        bot.send_message(
            chat_id=update.message.chat_id,
            text='- Your info not available\n- Use /start to register'
        )


def ask_share_link(bot, update):
    """
    ask users to share a a message
    and send back the link to the shared message
    """
    bot.send_message(
        chat_id=update.effective_user.id,
        text=config['messages']['share_task']
    )

    bot.send_message(
        chat_id=update.effective_user.id,
        text=config['messages']['share_msg'],
        disable_web_page_preview=True
    )

    return "receive_share_link"


def receive_share_link(bot, update):
    """
    receive new link and save to db
    """
    share_link = update.message.text
    telegram_id = update.message.from_user.id

    conn = connect_db()
    cursor = conn.cursor()

    if share_link.lower() == 'skip':
        bot.send_message(
            chat_id=update.message.chat_id,
            text='Process skipped'
        )
        return ConversationHandler.END
    
        # update db
        cursor.execute("""
        UPDATE participants SET share_link=%s WHERE telegram_id=%s 
        """, (share_link, telegram_id))
        cursor.close()
        conn.commit()
        conn.close()

        bot.send_message(
            chat_id=update.message.chat_id,
            text=config['messages']['done_msg']
        )
        return ConversationHandler.END


def purchase(bot, update):
    bot.send_message(
        chat_id=update.message.chat_id,
        text=config['messages']['purchase_msg'].format(
            config['ticker'],
            config['website'],
        ),
        disable_web_page_preview=True,
    )


def help_info(bot, update):
    """ displays help info """
    bot.send_message(
        chat_id=update.message.chat_id,
        text=config['messages']['help_msg'],
        disable_web_page_preview=True
    )


def cancel(bot, update):
    pass


reg_convo_handler = ConversationHandler(
    entry_points=[
        CommandHandler('start', start, pass_args=True),
        CommandHandler('Wallet', ask_eth_address),
        # CommandHandler('update', edit_details),
        CallbackQueryHandler(
            pattern='twitter',
            callback=ask_twitter_username,
            ),
        CallbackQueryHandler(
            pattern='facebook',
            callback=ask_facebook_name,
            ),
        CallbackQueryHandler(
            pattern='share',
            callback=ask_share_link,
        ),
        CallbackQueryHandler(
            pattern='youtube',
            callback=ask_youtube_name,
        ),
        ],
    states={
        'receive_eth_address': [
            MessageHandler(Filters.text, receive_eth_address)
            ],
        'receive_twitter_username': [
            MessageHandler(Filters.text, receive_twitter_username)
            ],
        'receive_facebook_name': [
            MessageHandler(Filters.text, receive_facebook_name)
        ],
        'receive_youtube_name': [
            MessageHandler(Filters.text, receive_youtube_name)
        ]
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)

# register handlers
menu_relayer_handler = MessageHandler(Filters.text, menu_relayer)

handlers = [
    reg_convo_handler,
    menu_relayer_handler,
    ]

for handler in handlers:
    dispatcher.add_handler(handler)


def main():
    updater.start_polling()
    print("airdropkingbot started :::: running {} campaign".format(
        config['ICO_name'])
        )
    updater.idle()


if __name__ == '__main__':
    main()
