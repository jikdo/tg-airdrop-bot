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

from db import connect_db, create_table

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
    conn = connect_db()
    cursor = conn.cursor()
    telegram_id = update.message.from_user.id
    telegram_username = update.message.from_user.username
    chat_id = update.message.chat_id

    # check db if participant exists
    cursor.execute("""
    SELECT telegram_id FROM participants WHERE telegram_id=%s
    """, (telegram_id,))

    participant = cursor.fetchone()

    # menu keyboard
    menu_keyboard = [
        ['/Wallet', '💎 Balance', '💬 Invite'],
        ['❓ Help', '🔨 Tasks', '👏 Purchase {}'.format(config['ticker'])]
        ]
    reply_markup = ReplyKeyboardMarkup(
        menu_keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
        )

    cursor.execute("""
    SELECT SUM(gains)
        FROM participants
    """)
    total = cursor.fetchone()[0]

    if total >= 1250000:
        bot.send_message(
            chat_id=update.message.chat_id,
            text="Airdrop exhausted. Visit our community for more info {}".format(config['social']['telegram_group'])
        )
    else:
        if not participant:
            # add new participant
            cursor.execute("""
            INSERT INTO
            participants
            (date_joined,
            telegram_id,
            chat_id,
            ref_code,
            eth_address,
            telegram_username,
            twitter_username,
            facebook_name,
            gains,
            referred_no)
            VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (date.today(),
                  telegram_id,
                  chat_id,
                  shortuuid.uuid(),
                  'n/a',
                  telegram_username,
                  'n/a',
                  'n/a',
                  config['rewards']['signup'],
                  0))
            print("new participant")

            # award referer
            if args:
                referral_link = args[0]
                cursor.execute("""
                SELECT gains, referred_no from participants WHERE ref_code=%s
                """, (referral_link,))
                results = (cursor.fetchone())
                gains = results[0]
                referred_no = results[1]

                cursor.execute("""
                UPDATE participants SET gains=%s, referred_no=%s WHERE ref_code=%s
                """, (
                    gains + config['rewards']['referral'],
                    referred_no + 1,
                    referral_link)
                    )

            bot.send_message(
                chat_id=update.message.chat_id,
                text=config['messages']['start_msg'].format(config['ICO_name']),
                disable_web_page_preview=True,
                reply_markup=reply_markup
            )
            cursor.close()
            conn.commit()
            conn.close()
        else:
            bot.send_message(
                chat_id=update.message.chat_id,
                text="You are already in the campaign",
                reply_markup=reply_markup
                )
            cursor.close()
            conn.commit()
            conn.close()


def menu_relayer(bot, update):
    option = update.message.text

    if option == '🔨 Tasks':
        task_list(bot, update)
    elif option == '💎 Balance':
        get_gains(bot, update)
    elif option == '💬 Invite':
        get_referral_link(bot, update)
    elif option == '👏 Purchase {}'.format(config['ticker']):
        purchase(bot, update)
    elif option == '❓ Help':
        help_info(bot, update)


def ask_eth_address(bot, update):
    """ ask eth address """
    bot.send_message(
        chat_id=update.message.chat_id,
        text='Enter your wallet address'
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


def task_list(bot, update):
    """ show tasks to complete """
    print("called")

    header_buttons = [
            InlineKeyboardButton(
                "📢 Join our news channel",
                url="{}".format(config['social']['telegram_channel'])
                ),
            InlineKeyboardButton(
                "👫 Join our community",
                url="{}".format(config['social']['telegram_group']),
                ),
        ]

    footer_buttons = [
        InlineKeyboardButton(
                "🐥 Access Twitter Bounty",
                callback_data='twitter',
            ),
    ]

    footer2_buttons = [
        InlineKeyboardButton(
                "📘 Access Facebook Bounty",
                callback_data='facebook',
            ),
    ]

    task_list_buttons = [
       header_buttons,
       footer_buttons[0:],
       footer2_buttons[0:],
    ]
    reply_markup = InlineKeyboardMarkup(task_list_buttons)
    bot.send_message(
        chat_id=update.message.chat_id,
        text="Complete the following tasks",
        reply_markup=reply_markup
    )


def ask_twitter_username(bot, update, user_data=None):
    """
    Ask twitter name
    """
    """ ask eth address """
    print(user_data)
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
    # update db
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

    bot.send_message(
        chat_id=update.effective_user.id,
        text=config['messages']['facebook_task'].format(
            config['social']['facebook'],
        ),
        parse_mode='Markdown',
        disable_web_page_preview=True,
    )
    return "receive_facebook_name"


def receive_facebook_name(bot, update):
    """
    Receive facebook link
    """
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

    # update db
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


def list_rules(bot, update):
    """ send rules of the bounty """
    bot.send_message(
        chat_id=update.message.chat_id,
        text=config['messages']['rules_msg'],
        disable_web_page_preview=True,
    )


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
        pass


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
            reflink = "https://t.me/pinktaxibounty_bot?start=" + ref_code

            bot.send_message(
                chat_id=update.message.chat_id,
                text=config['messages']['invite_msg'].format(reflink)
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
        pass


def edit_details(bot, update):
    """ update bounty details """
    bot.send_message(
            chat_id=update.message.chat_id,
            text=config['messages']['edit_msg'],
            disable_web_page_preview=True,
        )
    return "receive_eth_address"


def purchase(bot, update):
    bot.send_message(
        chat_id=update.message.chat_id,
        text=config['messages']['purchase_msg'],
        disable_web_page_preview=True,
    )


def help_info(bot, update):
    """ displays help info """
    bot.send_message(
        chat_id=update.message.chat_id,
        text=config['messages']['help_msg'],
        disable_web_page_preview=True
    )


def rules(bot, update):
    """ displays rules """
    bot.send_message(
        chat_id=update.message.chat_id,
        text=config['messages']['rules_msg'],
        disable_web_page_preview=True
    )


def cancel(bot, update):
    pass


reg_convo_handler = ConversationHandler(
    entry_points=[
        CommandHandler('start', start, pass_args=True),
        CommandHandler('Wallet', ask_eth_address),
        CommandHandler('update', edit_details),
        CallbackQueryHandler(
            pattern='twitter',
            callback=ask_twitter_username,
            ),
        CallbackQueryHandler(
            pattern='facebook',
            callback=ask_facebook_name,
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
        ]
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)

# register handlers
start_handler = CommandHandler('start', start)
menu_relayer_handler = MessageHandler(Filters.text, menu_relayer)
purchase_handler = CommandHandler('purchase', purchase)
gains_handler = CommandHandler('balance', get_gains)
referral_link_handler = CommandHandler('invite', get_referral_link)
help_handler = CommandHandler('help', help_info)
rules_handler = CommandHandler('rules', rules)
task_handler = CommandHandler('tasks', task_list)

handlers = [
    reg_convo_handler,
    start_handler,
    purchase_handler,
    gains_handler, referral_link_handler,
    help_handler, rules_handler,
    task_handler,
    menu_relayer_handler,
    ]

for handler in handlers:
    dispatcher.add_handler(handler)


def main():
    updater.start_polling()
    print("airdropkingbot started :::: ")
    updater.idle()


if __name__ == '__main__':
    main()
