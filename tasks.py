# -*- coding: utf-8 -*-
"""
.tasks
------
This module contains all bounty tasks related
functions and attributes
"""
import json

from telegram import (
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import ConversationHandler

from db import set_user_task_reward, connect_db

# get config
with open(r'config.json', 'r') as file:
    config = json.loads(file.read())

telegram_channel_button = [
    InlineKeyboardButton(
        "📢 Join our news channel",
        callback_data="telegram_channel_reward",
    ),
]

telegram_group_button = [
        InlineKeyboardButton(
            "👫 Join our community",
            callback_data="telegram_group_reward",
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
    ]

task_list_buttons = [
        telegram_channel_button,
        telegram_group_button,
        twitter_button,
        facebook_button,
    ]

tasks_markup = InlineKeyboardMarkup(task_list_buttons)

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

    set_user_task_reward(
       connect_db, telegram_id,
       config['rewards']['twitter'],
       'twitter_username',
       'twitter_reward',
       twitter_username
   )

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

    telegram_id = update.message.from_user.id
    facebook_name = update.message.text

    if facebook_name.lower() == "skip":
        bot.send_message(
            chat_id=update.message.chat_id,
            text="Process skipped"
        )
        return ConversationHandler.END
    print('facebook')
    set_user_task_reward(
        connect_db,
        telegram_id,
        config['rewards']['facebook'],
        'facebook_profile_link',
        'facebook_reward',
        facebook_name,
        )
    print('facebook done')

    bot.send_message(
        chat_id=update.message.chat_id,
        text=config['messages']['done_msg'],
        disable_web_page_preview=True,
        )
    return ConversationHandler.END


def ask_email_address(bot, update, user_data=None):
    """
    Ask email address
    """
    try:
        bot.send_message(
            chat_id=update.effective_user.id,
            text=config['messages']['email_task'].format(
                config['social']['email'],
            ),
            parse_mode='Markdown',
            disable_web_page_preview=True,
        )
        return "receive_facebook_name"
    except:
        pass


def receive_email_address(bot, update):
    """
    Receive email address
    """

    telegram_id = update.message.from_user.id
    email_address = update.message.text

    if email_address.lower() == "skip":
        bot.send_message(
            chat_id=update.message.chat_id,
            text="Process skipped"
        )
        return ConversationHandler.END
    print('email')
    set_user_task_reward(
        connect_db,
        telegram_id,
        config['rewards']['email'],
        'facebook_profile_link',
        'facebook_reward',
        email_address,
        )
    print('email done')

    bot.send_message(
        chat_id=update.message.chat_id,
        text=config['messages']['done_msg'],
        disable_web_page_preview=True,
        )
    return ConversationHandler.END


def reward_telegram_group(bot, update):
    """ reward for joining telegram group """
    set_user_task_reward(
        connect_db, update.effective_user.id,
        config['rewards']['telegram_group'],
        task_reward_column="telegram_group_reward"
    )
    bot.send_message(
        chat_id=update.effective_user.id,
        text="Join our [Telegram Community]({})".format(config['social']['telegram_group']),
        disable_web_page_preview=True,
        parse_mode="Markdown"
    )


def reward_telegram_channel(bot, update):
    """ reward for joining telegram channel """
    set_user_task_reward(
        connect_db, update.effective_user.id,
        config['rewards']['telegram_channel'],
        task_reward_column="telegram_channel_reward"
    )
    bot.send_message(
        chat_id=update.effective_user.id,
        text="Join our [Telegram News Channel]({})".format(config['social']['telegram_group']),
        disable_web_page_preview=True,
        parse_mode="Markdown"
    )