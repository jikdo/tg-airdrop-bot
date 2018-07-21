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
    set_user_wallet_address,
)

from tasks import (
    ask_facebook_name,
    ask_twitter_username,
    receive_facebook_name,
    receive_twitter_username,
    reward_telegram_group,
    reward_telegram_channel,
    receive_email_address,
    ask_email_address,
)

from menu import (
    menu_markup,
    menu_relayer
)
from db import set_user_task_reward

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

    print('total >>>>>> ' + str(total))
    if total >= config['rewards']['cap']:
        bot.send_message(
            chat_id=update.message.chat_id,
            text="Bounty completed.\nAllocated tokens finished. Visit our community for more info {}".format(config['social']['telegram_group']),
            disable_web_page_preview=True
        )
        print('airdrop shared ::: ' + str(total))
    else:
        if  not is_participant(connect_db, telegram_id):
            # add new participant
            add_new_participant(connect_db, telegram_id, chat_id, telegram_username)
            print("new participant added")

            # award referer
            if args:
                referral_code = args[0]
                print(referral_code)

                # reward referrer
                update_user_referral_reward_and_referred_no(
                    connect_db, referral_code,
                    config['rewards']['referral'],
                )
             
            bot.send_message(
                chat_id=update.message.chat_id,
                text=config['messages']['start_msg'].format(config['ICO_name']),
                disable_web_page_preview=True,
                reply_markup=menu_markup,
                parse_mode="Markdown"
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
    telegram_id = update.message.from_user.id
    eth_address = update.message.text

    if eth_address.lower() == "skip":
        bot.send_message(
            chat_id=update.message.chat_id,
            text="Process skipped"
        )
        return ConversationHandler.END

    # update db
    set_user_wallet_address(eth_address, telegram_id)
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

def cancel(bot, update):
    pass


reg_convo_handler = ConversationHandler(
    entry_points=[
        CommandHandler('start', start, pass_args=True),
        CommandHandler('Wallet', ask_eth_address),
        CallbackQueryHandler(
            pattern="telegram_channel_reward",
            callback=reward_telegram_channel,
        ),
        CallbackQueryHandler(
            pattern="telegram_group_reward",
            callback=reward_telegram_group,
        ),
        CallbackQueryHandler(
            pattern='twitter',
            callback=ask_twitter_username,
            ),
        CallbackQueryHandler(
            pattern='facebook',
            callback=ask_facebook_name,
            ),
        CallbackQueryHandler(
            pattern='email',
            callback=ask_email_address,
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
        'receive_email_address': [
            MessageHandler(Filters.text, receive_email_address)
        ],
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
