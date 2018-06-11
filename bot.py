#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright(c) 2018
# Kofi Amanfo <expl00ra@protonmail.com>

# This program is the sole property of www.airdropking.io

"""
This module is the engine of a telegram bounty and referral bot
designed to enhance visibilty for ICOs
"""

import os
import logging
import json
from datetime import date

from telegram.ext import (
    Updater,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    Filters,
    messagequeue as mq,
)
import telegram.bot
from telegram.utils.request import Request
from telegram.error import TelegramError, Unauthorized
import psycopg2
import shortuuid

import connect_db

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# get config
config = json.loads('./config.json')

class MQBot(telegram.bot.Bot):
    '''A subclass of Bot which delegates send method handling to MQ'''
    def __init__(self, *args, is_queued_def=True, mqueue=None, **kwargs):
        super(MQBot, self).__init__(*args, **kwargs)
        # below 2 attributes should be provided for decorator usage
        self._is_messages_queued_default = is_queued_def
        self._msg_queue = mqueue or mq.MessageQueue()

    def __del__(self):
        try:
            self._msg_queue.stop()
        except:
            pass
        super(MQBot, self).__del__()

    @mq.queuedmessage
    def send_message(self, *args, **kwargs):
        '''Wrapped method would accept new `queued` and `isgroup`
        OPTIONAL arguments'''
        return super(MQBot, self).send_message(*args, **kwargs)


# setup
request = Request(con_pool_size=8)
q = mq.MessageQueue()
tfb_bot = MQBot(config['access_token'], request=request, mqueue=q)
updater = Updater(bot=tfb_bot)
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

    if not participant:
        # add new participant
        cursor.execute("""
        INSERT INTO
        participants
        (date_joined, telegram_id, chat_id, ref_code, twitter_username, eth_address, gains)
        VALUES
        (%s, %s, %s, %s, %s, %s, %s)
        """, (date.today(),
              telegram_id,
              chat_id,
              shortuuid.uuid(),
              telegram_username,
              'n/a',
              0))
        print("new participant")

        # award referer
        if args:
            referral_link = args[0]
            cursor.execute("""
            SELECT gains from participants WHERE ref_code=%s
            """, (referral_link,))
            gains = cursor.fetchone()[0]

            cursor.excute("""
            UPDATE participants SET gains=%s WHERE ref_code=%s
            """, (gains + config['rewards']['referral']))

        bot.send_messsage(
            chat_id=update.message.chat_id,
            text=config['messages']['start_msg'],
            disable_web_page_preview=True,
        )
     
    else:
        bot.send_message(chat_id=update.message.chat_id,
                         text="You are already in the campaign")

    cursor.close()
    conn.commit()
    conn.close()
    return "receive_eth_address"


def receive_eth_address(bot, update):
    """ receive eth address """
    conn = connect_db()
    cursor = conn.cursor()

    telegram_id = update.message.from_user.id
    eth_address = update.message.text

    # update db
    cursor.execute("""
    UPDATE participants SET eth_address=%s WHERE telegram_id=%s
    """, (eth_address, telegram_id))
    cursor.close()
    conn.commit()
    conn.close()
    bot.send_message(
        chat_id=update.message.chat_id,
        text=config['messages']['twitter_task'],
        disable_web_page_preview=True,
    )
    return "receive_twitter_username"


def receive_twitter_username(bot, update):
    """
    Recieve twitter username
    """
    conn = connect_db()
    cursor = conn.cursor

    telegram_id = update.message.from_user.id
    twitter_username = update.message.text

    # update db
    cursor.execute("""
    UPDATE participants SET twitter_username=%s WHERE telegram_id=%s
    """, (twitter_username, telegram_id))
    cursor.close()
    conn.commit()
    conn.close()
    
    bot.send_message(
        chat_id=update.message.chat_id,
        text=config['messages']['facebook_task'],
        disable_web_page_preview-True,
    )
    return 'receive_facebook_link'


def receive_facebook_link(bot, update):
    """
    Receive facebook link
    """
    conn = connect_db()
    cursor = conn.cursor

    telegram_id = update.message.from_user.id
    facebook_username = update.message.text

    # update db
    cursor.execute("""
    UPDATE participants SET twitter_username=%s WHERE telegram_id=%s
    """, (twitter_username, telegram_id))
    cursor.close()
    conn.commit()
    conn.close()
    
    bot.send_message(
        chat_id=update.message.chat_id,
        text=config['messages']['done'],
        disable_web_page_preview-True,
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
    cursor = conn.cursor

    telegram_id = update.message.from_user.id
    cursor.execute("""
    SELECT gains FROM participants WHERE telegram_id=%s
    """, (telegram_id, ))
    gains = cursor.fetchone()[0]

    bot.send_message(
        chat_id=update.message.chat_id,
        text=config['messages']['gains_msg'],
        display_web_page_preview=True,
    )
    cursor.close()
    conn.commit()
    conn.close()


def get_referral_link(bot, update):
    """
    Displays referral link of user
    """
    conn = connect_db()
    cursor = conn.cursor()
    
    telegram_id = update.message.text
    cursor.execute("""
    SELECT ref_code FROM participants WHERE telegram_id=%s
    """, (telegram_id, ))
    ref_code = cursor.fetchone()[0]
    reflink = "https://t.me/pinktaxibounty_bot?start=" + ref_code

    bot.send_photo(
        chat_id=update.message.chat_id,
        photo="**",
        caption=config['messages']['invite_msg'].format(reflink)
    )
    bot.send_message(
        chat_id=update.message.chat_id,
        text=fwd_invite_msg,
        disable_web_page_preview=True,
    )


def purchase(bot, update):
    bot.send_message(
        chat_id=update.message.chat_id,
        text=config['messages']['purchases'],
        disable_web_page_preview=True,
    )


def cancel(bot, update):
    pass


reg_convo_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start, pass_args=True),
    states={
        'receive_eth_address': [
            MessageHandler(Filters.text, receive_eth_address)
            ],
        'receive_twitter_handle': [
            MessageHandler(Filters.text, receive_twitter_username)
            ]
    },
        fallbacks=[CommandHandler('/cancel', cancel)]
    ]
)

# register handlers
purchase_handler = CommandHandler('purchase', purchase)
gains_handler = CommandHandler('gains', get_gains)
referral_link_handler = CommandHandler('invite', get_referral_link)

handlers = [purchase_handler, gains_handler, referral_link_handler]

for handler in handlers:
    dispatcher.add(handler)


def main():
    updater.start_polling()
    print("airdropkingbot started")


if __name__ == '__main__':
    main()
