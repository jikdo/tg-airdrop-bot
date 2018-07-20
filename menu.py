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
    connect_db,
    get_user_rewards,
    get_user_referred_no,
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
        send_referral_link(bot, update)
    elif option == '👏 Purchase {}'.format(config['ticker']):
        send_purchase_info(bot, update)
    elif option == '❓ Help':
        send_help_info(bot, update)
    else:
        reply_unknown_text(bot, update)


def send_task_list(bot, update):
    """ show tasks to complete """
    print("called")

    telegram_channel_button = [
        InlineKeyboardButton(
            "📢 Join our news channel",
            url="{}".format(config['social']['telegram_channel']),
        ),
    ]

    telegram_group_button = [
        InlineKeyboardButton(
            "👫 Join our community",
            url="{}".format(config['social']['telegram_group']),
        ),
    ]

    twitter_button = [
        InlineKeyboardButton(
            "🐥 Twitter Bounty",
            callback_data='twitter',
        ),
    ]

    facebook_button = [
        InlineKeyboardButton(
            "📘 Facebook Bounty",
            callback_data='facebook',
        ),
    ]

    youtube_button = [
        InlineKeyboardButton(
            "📺 Youtube Bounty",
            callback_data='youtube'
        )
    ]

    task_list_buttons = [
        telegram_channel_button,
        telegram_group_button,
        twitter_button,
        facebook_button,
        youtube_button,
    ]

    tasks_markup = InlineKeyboardMarkup(task_list_buttons)
    bot.send_message(
        chat_id=update.message.chat_id,
        text="Complete the following tasks",
        reply_markup=tasks_markup
    )


def send_help_info(bot, update):
    """ displays help info """
    bot.send_message(
        chat_id=update.message.chat_id,
        text=config['messages']['help_msg'],
        disable_web_page_preview=True
    )


def send_purchase_info(bot, update):
    bot.send_message(
        chat_id=update.message.chat_id,
        text=config['messages']['purchase_msg'].format(
            config['ticker'],
            config['website'],
        ),
        disable_web_page_preview=True,
    )


def send_user_rewards_info(bot, update):
    """
    Displays reward earned by participant
    """
    telegram_id = update.message.from_user.id



    telegram_channel, telegram_group, twitter, facebook, referrals, total = get_user_rewards(connect_db, telegram_id)
       
       # get total referred
    referred_no = get_user_referred_no(connect_db, telegram_id)

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
                    config['ticker']),
                display_web_page_preview=True,
            )
    

def send_user_referral_link(bot, update):
    """
    Sends user's referral link
    """
    conn, cursor = connect_db()
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

        
def reply_unknown_text(bot, update):
    """ Replies to unknown menu command """
    bot.send_message(
        chat_Id=update.message.chat_id,
        text="Unknown text. Please use the menu buttons"
    )