# -*- coding: utf-8 -*-
import sys
import time

import calendar
import feedparser
import json
import logging
import os
import twx.botapi
from datetime import datetime
from lxml.html import fragment_fromstring
from twx.botapi import TelegramBot

import settings


def remove_tags(text):
    """
    This function remove all html tags from string.
    <br/> tags are replaced by newline. 

    """
    root = fragment_fromstring(text, create_parent='div')
    for br in root.xpath("br"):
        br.tail = "\n" + br.tail if br.tail else "\n"
    return root.text_content()


def load_settings():
    if os.path.isfile('db.json'):
        with open('db.json', encoding='utf-8') as f:
            tgm_data = json.load(f)

        last_post_date = datetime.strptime(tgm_data['last_post_date'],
                                           '%Y-%m-%dT%H:%M:%S')
    else:
        last_post_date = datetime(1, 1, 1, 0, 0, 0)
        tgm_data = {}

    return last_post_date, tgm_data


def save_settings(date):
    tgm_data = {'last_post_date': date}
    with open('db.json', 'w', encoding='utf-8') as f:
        json.dump(tgm_data, f)


def main():
    last_post_date, tgm_data = load_settings()

    rss = feedparser.parse(settings.RSS_URL)

    logging.debug("last_post_date: %s", last_post_date.isoformat())
    # find new entries in feed
    new_entries = []
    for entry in rss.entries:
        try:
            entry_published = datetime.utcfromtimestamp(
                calendar.timegm(entry.published_parsed))
            if entry_published > last_post_date:
                new_entries.append(entry)
        except AttributeError as e:
            logging.error("%s\n%s", e, entry)

    logging.info('The number of new entries: %s\nEntries: %s',
                 len(new_entries),
                 [(item.get('id'), item.get('published_parsed')) for item in
                  new_entries])

    date = datetime.now()
    if not new_entries:
        logging.info('New entries are not found')
        save_settings(date.isoformat())
        return

    # sort new entries by published date
    new_entries.sort(key=lambda item: item.published_parsed)

    # send to telegram channel
    tgm_bot = TelegramBot(settings.TGM_BOT_ACCESS_TOKEN)
    for entry in new_entries:
        try:

            logging.debug("Raw message:\n%s\n", entry.description)
            message = remove_tags(entry.description)
            logging.debug("message:\n%s\n", message)
        except AttributeError as e:
            logging.error("%s\n%s", e, entry)
            continue

        answer = tgm_bot.send_message(settings.TGM_CHANNEL, message).wait()
        if isinstance(answer, twx.botapi.Error):
            logging.error("error code: %s\nerror description: %s\n",
                          answer.error_code,
                          answer.description)
            break
        else:
            date = max(
                datetime.utcfromtimestamp(
                    calendar.timegm(entry.published_parsed)),
                date
            )

        time.sleep(1)

    save_settings(date.isoformat())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s:%(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S %Z')
    try:
        logging.debug("Start parse")
        main()
    except Exception as e:
        logging.critical(e)
        sys.exit()
