# -*- coding: utf-8 -*-

"""
.menu
-----

This module provides menu elements and 
functions for the bot to execute from the
menu context
"""
import json

from telegram import (
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from db import (
    get_user_rewards,
    get_user_referred_no,
    get_user_referral_code,
    get_user_task_reward,
)
from tasks import (
    tasks_markup,
)

# get config
with open(r'config.json', 'r') as file:
    config = json.loads(file.read())

# menu keyboard
menu_keyboard = [
    ['/Wallet', '💎 Balance', '💬 Invite'],
    ['❓ Help', '🔨 Tasks', '👏 Purchase {}'.format(config['ticker'])]
]

menu_markup = ReplyKeyboardMarkup(
    menu_keyboard,
    resize_keyboard=True,
    one_time_keyboard=False
)


def menu_relayer(bot, update):
    option = update.message.text

    if option == '🔨 Tasks':
        send_task_list(bot, update)
    elif option == '💎 Balance':
        send_user_rewards_info(bot, update)
    elif option == '💬 Invite':
        send_user_referral_link(bot, update)
    elif option == '👏 Purchase {}'.format(config['ticker']):
        send_purchase_info(bot, update)
    elif option == '❓ Help':
        send_help_info(bot, update)
    else:
        reply_unknown_text(bot, update)


def send_task_list(bot, update):
    """ show tasks to complete """
    print("task list accessed")
    bot.send_message(
        chat_id=update.message.chat_id,
        text="Complete the following tasks",
        reply_markup=tasks_markup
    )


def send_help_info(bot, update):
    """ displays help info """
    bot.send_message(
        chat_id=update.message.chat_id,
        text=config['messages']['help_msg'].format(
            config['FAQ'], config['whitepaper'],
        ),
        disable_web_page_preview=True,
        parse_mode="Markdown"
    )


def send_purchase_info(bot, update):
    bot.send_message(
        chat_id=update.message.chat_id,
        text=config['messages']['purchase_msg'].format(
            config['ticker'],
            config['signup'],
        ),
        disable_web_page_preview=True,
    )


def send_user_rewards_info(bot, update):
    """
    Displays reward earned by participant
    """
    telegram_id = update.message.from_user.id



    telegram_channel, telegram_group, twitter, facebook, referrals, total = get_user_rewards(telegram_id)
       
       # get total referred
    referred_no = get_user_referred_no(telegram_id)

    bot.send_message(
                chat_id=update.message.chat_id,
                text=config['messages']['gains_msg'].format(
                    telegram_channel,
                    telegram_group,
                    twitter,
                    facebook,
                    referrals,
                    referred_no,
                    total,
                    ticker=config['ticker']),
                display_web_page_preview=True,
                parse_mode='Markdown'
            )
    

def send_user_referral_link(bot, update):
    """
    Sends user's referral link
    """
    telegram_id = update.message.from_user.id

    referral_code = get_user_referral_code(telegram_id)

    if referral_code:
        reflink = "https://t.me/{}?start=".format(config['bot_username']) + referral_code

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


def reply_unknown_text(bot, update):
    """ Replies to unknown menu command """
    bot.send_message(
        chat_id=update.effective_user.id,
        text="Unknown text. Please use the menu buttons"
    )