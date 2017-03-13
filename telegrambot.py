# Author: Mathias Punkenhofer
# Mail: newsgroups.mpunkenhofer@gmail.com
# Created: 13 March 2017

import logging

import telepot

logger = logging.getLogger(__name__)


class TelegramBotUserSettings:
    def __init__(self, enabled=False, notifications=False):
        self.enabled = enabled  # enable/disable irc relay
        self.notifications = notifications  # enable/disable irc notifications


class TelegramBot:
    def __init__(self, token):
        self.telegram = telepot.Bot(token)

        logger.debug('starting telegram msg loop.')
        self.telegram.message_loop(self.telegram_handle)

        self.users = {}

        self.channel = ''
        self.server = ''
        self.irc_users = []

    def telegram_handle(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)

        if content_type == 'text':
            self.handle_command(chat_id, msg['text'])

    def send_msg(self, nick, msg):
        for user, user_settings in self.users.items():
            if user_settings.enabled:
                logger.debug('send_msg user: {0:d} - {1:s}'.format(user, nick + ': ' + msg))
                self.telegram.sendMessage(user, '<{0:s}> {1:s}'.format(nick, msg))

    def send_notification(self, msg):
        for user, user_settings in self.users.items():
            if user_settings.enabled and user_settings.notifications:
                logger.debug('send_notification user: {0:d} - {1:s}'.format(user, msg))
                self.telegram.sendMessage(user, '* {1:s}'.format(msg))

    def handle_command(self, chat_id, command='no command'):
        logger.debug('user: {0:d} sent cmd: {1:s}'.format(chat_id, command))

        if chat_id not in self.users:
            logger.debug('Added user with id: {0:d}'.format(chat_id))
            self.users[chat_id] = TelegramBotUserSettings()

        if command == '/start':
            msg = ''

            if self.channel:
                msg = 'the channel ' + self.channel
            else:
                msg = 'the irc'

            self.telegram.sendMessage(chat_id, 'You will now receive messages from ' + msg + '.')
            self.users[chat_id].enabled = True
        elif command == '/stop':
            self.telegram.sendMessage(chat_id, 'You will no longer receive any messages from the irc!')
            self.users[chat_id].enabled = False
        elif command == '/channel':
            if self.channel and self.server:
                self.telegram.sendMessage(chat_id,
                                          'You are getting messages from {0:s} on {1:s}'
                                          .format(self.channel, self.server))
            else:
                self.telegram.sendMessage('I don\'t have this information currently :(')
        elif command == '/users':
            if self.irc_users:
                users = str(self.irc_users)
                self.telegram.sendMessage(chat_id, 'Users: ' + users)
            else:
                self.telegram.sendMessage('I don\'t have this information currently :(')
        elif command == '/help' or command == '/commands':
            self.telegram.sendMessage(chat_id,  '/start - enable the bot to relay messages from the irc channel\n'
                                                '/stop - stop the bot from sending you any messages\n'
                                                '(all irc conversation while disabled will be lost)\n'
                                                '/help - prints this message')
        else:
            self.telegram.sendMessage(chat_id, 'Unknown command - you might want to take a look at /help')
