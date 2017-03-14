# coding: UTF-8
import tornado.escape
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
import tornado.template
from tornado.options import define, options
import os
from dotenv import load_dotenv
import tweepy
import threading
import json
from logging import getLogger
logger = getLogger(__name__)

# .env
# $ heroku config:push
if os.getenv("HEROKU") is None:
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    load_dotenv(dotenv_path)
    port = 8888
else:
    port = int(os.environ.get("PORT", 5000))

CONFIG = os.environ

define("port", default=port, help="run on the given port", type=int)


class Application(tornado.web.Application):
    def __init__(self):
        favicon_path = '/static/favicon.ico'
        handlers = [
            (r"/", MainHandler),
            (r"/ws", TrendSocketHandler),
            (r"/favicon.ico", tornado.web.StaticFileHandler,
             {'path': favicon_path}),
        ]
        settings = dict(
            cookie_secret="GENERATE_YOUR_OWN_RANDOM_VALUE_HERE",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=True,
        )
        super(Application, self).__init__(handlers, **settings)


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render(
            "index.html",
            trends25=TrendSocketHandler.cache_to25,
            trends50=TrendSocketHandler.cache_to50,
            isNone=self.isNone
        )

    def isNone(self, value):
        if value is None:
            return ''
        else:
            return value


class TrendSocketHandler(tornado.websocket.WebSocketHandler):
    waiters = set()
    cache_to25 = []
    cache_to50 = []

    def get_compression_options(self):
        return {}

    def open(self):
        TrendSocketHandler.waiters.add(self)

    def on_close(self):
        TrendSocketHandler.waiters.remove(self)

    @classmethod
    def send_updates(cls, values):
        logger.info("sending message to %d waiters", len(cls.waiters))

        for waiter in cls.waiters:
            try:
                waiter.write_message(values)
            except:
                logger.error("Error sending message", exc_info=True)


CONSUMER_KEY = CONFIG['CONSUMER_KEY']
CONSUMER_SECRET = CONFIG['CONSUMER_SECRET']
ACCESS_TOKEN = CONFIG['ACCESS_TOKEN']
ACCESS_SECRET = CONFIG['ACCESS_SECRET']

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)
api = tweepy.API(auth)

regional_id = {}
for place in api.trends_available():
    if place['countryCode'] == 'JP':
        regional_id[place['name']] = place['woeid']
JP = regional_id['Japan']


# 3 minute cycle
def send_trend():
    # logger.info("現在のスレッド数:%d", threading.active_count())
    trend_array = []
    for idx, trend in enumerate(api.trends_place(JP)[0]['trends'], 1):
        value = {
            "rank": str(idx),
            "name": trend["name"],
            "volume": trend["tweet_volume"],
            "url": trend["url"]
        }
        trend_array.append(value)
    TrendSocketHandler.cache_to25 = trend_array[:25]
    TrendSocketHandler.cache_to50 = trend_array[25:]
    json_str = json.dumps(trend_array)
    TrendSocketHandler.send_updates(json_str)
    t = threading.Timer(180, send_trend)
    t.daemon = True
    t.start()


def main():
    threading.Thread(target=send_trend).start()
    tornado.options.parse_command_line()
    app = Application()
    app.listen(options.port)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
