# Author(s): Mathias Punkenhofer - code.mpunkenhofer@gmail.com
#            -
# Created: 13 March 2017

import logging
import json

import telepot

logger = logging.getLogger(__name__)

defaultBotUserSettings = {'enabled': True, 'notifications': True}


class TelegramBot:
    def __init__(self, token):
        self.telegram = telepot.Bot(token)

        logger.debug('starting telegram msg loop.')
        self.telegram.message_loop(self.telegram_handle)

        self.users = {}

        self.server = ''
        self.channel = ''
        self.irc_users = {}

        self.user_settings_file_name = 'telegram_bot_users.save'
        self.read_settings()

    def telegram_handle(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)

        if content_type == 'text':
            self.do_command(str(chat_id), msg['text'])

    def send_msg(self, nick, msg):
        for user, user_settings in self.users.items():
            if user_settings['enabled']:
                logger.debug('send_msg user: {0:s} - {1:s}'.format(user, nick + ': ' + msg))
                self.telegram.sendMessage(int(user), '<{0:s}> {1:s}'.format(nick, msg))

    def send_notification(self, msg):
        for user, user_settings in self.users.items():
            if user_settings['enabled'] and user_settings['notifications']:
                logger.debug('send_notification user: {0:s} - {1:s}'.format(user, msg))
                self.telegram.sendMessage(int(user), '* {0:s}'.format(msg))

    def do_command(self, id, cmd='no command'):
        logger.debug('user: {0:s} sent cmd: {1:s}'.format(id, cmd))

        if id not in self.users:
            logger.info('New bot user, id: {0:s}'.format(id))
            self.users[id] = defaultBotUserSettings
            self.write_settings()

        if cmd == '/start':
            msg = ''

            if self.channel:
                msg = 'the channel ' + self.channel
            else:
                msg = 'the irc'

            self.telegram.sendMessage(id, 'You will now receive messages from ' + msg + '.')
            self.users[id]['enabled'] = True
            self.write_settings()
        elif cmd == '/stop':
            self.telegram.sendMessage(id, 'You will no longer receive any messages from the irc!')
            self.users[id]['enabled'] = False
            self.write_settings()
        elif cmd == '/notifications':
            if self.users[id]['notifications']:
                self.telegram.sendMessage(id, 'Notifications disabled!')
                self.users[id]['notifications'] = False
            else:
                self.telegram.sendMessage(id, 'Notifications enabled!')
                self.users[id]['notifications'] = True

            self.write_settings()
        elif cmd == '/channel':
            if self.channel and self.server:
                self.telegram.sendMessage(id,
                                          'You are getting messages from {0:s} on {1:s}'
                                          .format(self.channel, self.server))
            else:
                self.telegram.sendMessage(id, 'I don\'t have this information currently :(')
        elif cmd == '/users':
            if len(self.irc_users) > 0:
                users = self.irc_users['users']
                opers = self.irc_users['opers']
                voiced = self.irc_users['voiced']

                # TODO fix users command
                '''self.telegram.sendMessage(id,
                                          (('Operators:\n' + ', '.join(opers) + '\n') if len(opers) > 0 else '') +
                                          (('Moderators:\n' + ', '.join(voiced) + '\n') if len(voiced) > 0 else '') +
                                          'Users:\n' + ', '.join(users) + '\n'
                                          )'''

                self.telegram.sendMessage(id,
                                          'Operators:\n' + ', '.join(opers) + '\n'+
                                          'Moderators:\n' + ', '.join(voiced) + '\n' +
                                          'Users:\n' + ', '.join(users) + '\n'
                                          )
            else:
                self.telegram.sendMessage(id, 'I don\'t have this information currently :(')
        elif cmd == '/help' or cmd == '/commands':
            self.telegram.sendMessage(id,
                                      '/start - enable the bot to relay messages from the irc channel\n'
                                      '/stop - stop the bot from sending you any messages\n'
                                      '(all irc conversation while disabled will be lost)\n'
                                      '/notifications - enable/disable irc notifications\n'
                                      '/channel - display basic irc channel information\n'
                                      '/users - lists all the irc users in the channel\n'
                                      '/help or /commands - prints this message\n'
                                      )
        else:
            self.telegram.sendMessage(id, 'Unknown command - you might want to take a look at /help')

    def write_settings(self):
        logger.debug('writing telegram user settings to file: {0:s}'.format(self.user_settings_file_name))
        logger.debug('users:' + json.dumps(self.users))

        with open(self.user_settings_file_name, 'w') as file:
            json.dump(self.users, file)

    def read_settings(self):
        logger.debug('reading telegram user settings to file: {0:s}'.format(self.user_settings_file_name))
        try:
            with open(self.user_settings_file_name, 'r') as file:
                self.users = json.load(file)
                logger.debug('read:' + str(self.users))
        except EnvironmentError:
            logger.debug('error reading telegram user settings file: {0:s}'.format(self.user_settings_file_name))
            self.notify_owner('Unable to open the user settings file ({0:s})'.format(self.user_settings_file_name))

    def notify_owner(self, msg):
        logger.debug('notify the bot owner about: {0:s}'.format(msg))
        pass
