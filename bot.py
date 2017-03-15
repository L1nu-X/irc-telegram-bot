# Author(s): Mathias Punkenhofer - code.mpunkenhofer@gmail.com
#            -
# Created: 09 March 2017

import sys
import logging
import datetime
import configparser

import irc.bot
import irc.client

from telegrambot import TelegramBot

logger = logging.getLogger(__name__)

# disable logging from other modules
logging.getLogger('urllib3').setLevel(level=logging.WARNING)
logging.getLogger('irc.client').setLevel(level=logging.WARNING)


class Bot(irc.bot.SingleServerIRCBot):
    def __init__(self, token, channel, nickname, server, port=6667):
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.channel = channel

        self.telegram = TelegramBot(token)
        self.telegram.channel = channel.replace('#', '')
        self.telegram.server = server

    def on_nicknameinuse(self, c, e):
        logger.info('nickname already in use, add an underscore')
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        # server welcome
        logger.info('joining channel: {0:s}'.format(self.channel))
        c.join(self.channel)

        for channel_name, channel_obj in self.channels.items():
            print(channel_name, channel_obj.users())
            self.telegram.irc_users = sorted(channel_obj.users())

    def on_privmsg(self, c, e):
        logger.debug('on private message, event: ' + str(e))
        logger.info('private msg: {0:s}'.format(e.arguments[0]))
        self.telegram.notify_owner(e.arguments[0])
        self.do_command(e, e.arguments[0])

    def on_pubmsg(self, c, e):
        logger.debug('on public message, event: ' + str(e))

        nick = e.source.split('!')[0]
        msg = e.arguments[0]
        current_time = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")

        logger.info('[{0:s}] <{1:s}> {2:s}'.format(current_time, nick, msg))

        self.telegram.send_msg(nick, msg)

    def on_kick(self, c, e):
        # arg[0] was kicked by e.source (arg[1])
        logger.debug('on kick, event: ' + str(e))

        kicked_user = e.arguments[0]
        kicked_by = self.get_nick(e.source)
        reason = e.arguments[1]

        msg = '{0:s} was kicked by {1:s} ({2:s})'.format(kicked_user, kicked_by, reason)
        logger.info('* ' + msg)

        self.telegram.send_notification(msg)

        self.update_users()

    def on_join(self, c, e):
        # e.source has joined e.target
        logger.debug('on join, event: ' + str(e))

        joined_user = self.get_nick(e.source)
        joined_user_id = self.get_id(e.source)
        channel = e.target.replace('#', '')

        msg = '{0:s} ({1:s}) has joined {2:s}'.format(joined_user, joined_user_id, channel)
        logger.info('* ' + msg)

        # avoid sending telegram users the joined msg when the bot joins the irc channel
        if joined_user != c.get_nickname():
            self.telegram.send_notification(msg)

        self.update_users()

    def on_quit(self, c, e):
        # e.source Quit (arg[0])
        logger.debug('on quit, event: ' + str(e))

        leaving_user = self.get_nick(e.source)
        leaving_user_id = self.get_id(e.source)
        quit_msg = e.arguments[0]

        msg = '{0:s} ({1:s}) Quit ({2:s})'.format(leaving_user, leaving_user_id, quit_msg)
        logger.info('* ' + msg)

        self.telegram.send_notification(msg)

        self.update_users()

    def on_part(self, c, e):
        # e.source has left e.target
        logger.debug('on part, event: ' + str(e))

        leaving_user = self.get_nick(e.source)
        leaving_user_id = self.get_id(e.source)
        channel = e.target.replace('#', '')

        msg = '{0:s} ({1:s}) has left {2:s}'.format(leaving_user, leaving_user_id, channel)
        logger.info('* ' + msg)

        self.telegram.send_notification(msg)

        self.update_users()

    def on_topic(self, c, e):
        # e.source sets topic arg[0]
        logger.debug('on topic, event: ' + str(e))

        topic_changer = self.get_nick(e.source)
        new_topic = e.arguments[0]

        msg = '{0:s} changes topic to \'{1:s}\''.format(topic_changer, new_topic)
        logger.info('* ' + msg)

        self.telegram.send_notification(msg)

    def on_nick(self, c, e):
        # e.source is now known as e.target
        logger.debug('on nick, event: ' + str(e))

        nick_changer = self.get_nick(e.source)
        new_nick = e.target

        msg = '{0:s} is now known as {1:s}'.format(nick_changer, new_nick)
        logger.info('* ' + msg)

        self.telegram.send_notification(msg)

        self.update_users()

    def on_mode(self, c, e):
        # e.source sets mode arg[0] arg[1]
        logger.debug('on mode, event: ' + str(e))

        mode_changer = self.get_nick(e.source)
        new_mode = ' '.join(e.arguments)

        msg = '{0:s} sets mode: {1:s}'.format(mode_changer, new_mode)
        logger.info('* ' + msg)

        self.telegram.send_notification(msg)

        self.update_users()

    def on_action(self, c, e):
        # no use case for now
        logger.debug('on action, event: ' + str(e))
        pass

    def do_command(self, e, cmd):
        nick = e.source.nick
        c = self.connection

        if cmd == "disconnect":
            self.disconnect()
        elif cmd == "die":
            self.die()

    def get_nick(self, full_id):
        return full_id.split('!')[0]

    def get_id(self, full_id):
        return full_id.split('!')[1]

    def update_users(self):
        logger.debug('updating channel users')
        channel_obj = self.channels[self.channel]
        self.telegram.irc_users['users'] = sorted(channel_obj.users())
        self.telegram.irc_users['opers'] = sorted(channel_obj.opers())
        self.telegram.irc_users['voiced'] = sorted(channel_obj.voiced())

def main():
    logging.basicConfig(level=logging.DEBUG)

    arguments = sys.argv[1:]

    if len(arguments) != 4:
        print("Usage: bot <server[:port]> <channel> <nickname> <telegram-token>")
        for arg in sys.argv:
            print(arg)

        sys.exit(1)

    s = sys.argv[1].split(":", 1)
    server = s[0]
    if len(s) == 2:
        try:
            port = int(s[1])
        except ValueError:
            print("Error: Erroneous port.")
            sys.exit(1)
    else:
        port = 6667
    channel = sys.argv[2]
    nickname = sys.argv[3]
    token = sys.argv[4]

    print('starting irc-telegram bot\n')
    print('server: ' + server)
    print('channel: ' + channel)
    print('nick: ' + nickname)
    print('token: ' + token)
    print('')

    bot = Bot(server=server, port=port, channel=channel, nickname=nickname, token=token)
    bot.start()


if __name__ == '__main__':
    main()
