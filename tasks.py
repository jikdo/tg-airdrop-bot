# -*- coding: utf-8 -*-
"""
.tasks
--------

This module provides the necessary task functions
and attributes that users are to complete
""""
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

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