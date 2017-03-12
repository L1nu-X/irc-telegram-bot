# Author: Mathias Punkenhofer
# Mail: newsgroups.mpunkenhofer@gmail.com
# Created: 09 March 2017

import sys
import logging
import irc.bot
import irc.client
import telepot

logger = logging.getLogger(__name__)


class BsBot(irc.bot.SingleServerIRCBot):
    def __init__(self, telegram, channel, nickname, server, port=6667):
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.channel = channel
        self.telegram = telegram

        logger.info('Starting Telegram msg loop.')
        self.telegram.message_loop(self.telegram_handle)

    def on_nicknameinuse(self, c, e):
        logger.info('Nickname already in use, add an underscore')
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        # server welcome
        logger.info('Joining channel: %s', self.channel)
        c.join(self.channel)

    def on_privmsg(self, c, e):
        # private msg
        logger.info('We got a private msg: ', e.arguments[0])
        self.do_command(e, e.arguments[0])

    def on_pubmsg(self, c, e):
        # chan msg
        print('<{0:s}> {1:s}'.format(e.source.split('!')[0], e.arguments[0]))

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

    def telegram_handle(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        print(content_type, chat_type, chat_id)

        if content_type == 'text':
            self.telegram.sendMessage(chat_id, msg['text'])

def main():
    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) != 5:
        print("Usage: bsbot <server[:port]> <channel> <nickname> <telegram-token>")
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

    print('Starting BS-IRC-Telegram BOT...')
    telegram = telepot.Bot(sys.argv[4])
    bot = BsBot(telegram, channel, nickname, server, port)
    bot.start()


if __name__ == '__main__':
    main()
