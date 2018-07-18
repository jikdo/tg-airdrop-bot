# -*- coding: utf-8 -*-

"""
.menu
-----

This module provides menu elements and 
functions for the bot to execute from the
menu context
"""

# menu keyboard
menu_keyboard = [
    ['/Wallet', '💎 Balance', '💬 Invite'],
    ['❓ Help', '🔨 Tasks', '👏 Purchase {}'.format(config['ticker'])]
        ]

menu_markeup = ReplyKeyboardMarkup(
    menu_keyboard,
    resize_keyboard=True,
    one_time_keyboard=False
    )


def menu_relayer(bot, update):
    option = update.message.text

    if option == '🔨 Tasks':
        send_task_list(bot, update)
    elif option == '💎 Balance':
        send_rewards_info(bot, update)
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
        reply_markup=reply_markup
    )


def send_help_info(bot, update):
    """ displays help info """
    bot.send_message(
        chat_id=update.message.chat_id,
        text=config['messages']['help_msg'],
        disable_web_page_preview=True
    )