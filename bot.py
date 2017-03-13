# Author: Mathias Punkenhofer
# Mail: newsgroups.mpunkenhofer@gmail.com
# Created: 09 March 2017

import sys
import logging
import datetime
import configparser

import irc.bot
import irc.client

from telegrambot import TelegramBot

logger = logging.getLogger(__name__)


class Bot(irc.bot.SingleServerIRCBot):
    def __init__(self, token, channel, nickname, server, port=6667):
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.channel = channel

        self.telegram = TelegramBot(token)
        self.telegram.channel = channel.replace('#', '')
        self.telegram.server = server

    def on_nicknameinuse(self, c, e):
        logger.info('Nickname already in use, add an underscore')
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        # server welcome
        logger.info('Joining channel: {0:s}'.format(self.channel))
        c.join(self.channel)

    def on_privmsg(self, c, e):
        # private msg
        logger.info('We got a private msg: {0:s}'.format(e.arguments[0]))
        self.do_command(e, e.arguments[0])

    def on_pubmsg(self, c, e):
        # chan msg
        nick = e.source.split('!')[0]
        msg = e.arguments[0]
        current_time = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")

        print('[{0:s}] <{1:s}> {2:s}'.format(current_time, nick, msg))

        self.telegram.send_msg(nick, msg)

    def on_kick(self, c, e):
        # someone got kicked
        pass

    def on_join(self, c, e):
        # someone joined the channel
        pass

    def do_command(self, e, cmd):
        nick = e.source.nick
        c = self.connection

        if cmd == "disconnect":
            self.disconnect()
        elif cmd == "die":
            self.die()
        elif cmd == "stats":
            for chname, chobj in self.channels.items():
                c.notice(nick, "--- Channel statistics ---")
                c.notice(nick, "Channel: " + chname)
                users = sorted(chobj.users())
                c.notice(nick, "Users: " + ", ".join(users))
                opers = sorted(chobj.opers())
                c.notice(nick, "Opers: " + ", ".join(opers))
                voiced = sorted(chobj.voiced())
                c.notice(nick, "Voiced: " + ", ".join(voiced))
        else:
            c.notice(nick, "Not understood: " + cmd)


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

    print('Starting IRC-Telegram BOT...')
    bot = Bot(server=server, port=port, channel=channel, nickname=nickname, token=token)
    bot.start()


if __name__ == '__main__':
    main()
