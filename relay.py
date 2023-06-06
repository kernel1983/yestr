
import os
import json

import rocksdb
import eth_account

import tornado.web
import tornado.ioloop
import tornado.options
import tornado.httpserver
import tornado.httpclient
import tornado.gen
import tornado.escape
import tornado.websocket


db_conn = rocksdb.DB('test.db', rocksdb.Options(create_if_missing=True))

subscriptions = {}

class RelayHandler(tornado.websocket.WebSocketHandler):
    child_miners = set()

    def check_origin(self, origin):
        return True

    def open(self):
        if self not in RelayHandler.child_miners:
            RelayHandler.child_miners.add(self)

        print("RelayHandler connected")


    def on_close(self):
        if self in RelayHandler.child_miners:
            RelayHandler.child_miners.remove(self)

        print("RelayHandler disconnected")


    @tornado.gen.coroutine
    def on_message(self, message):
        seq = tornado.escape.json_decode(message)
        print("RelayHandler", seq)

        if seq[0] == 'REQ':
            subscription_id = seq[1]
            self.filters = seq[2]
            subscriptions[subscription_id] = self
            since = self.filters.get('since')
            until = self.filters.get('until')
            limit = self.filters.get('limit')
            ids = self.filters.get('limit')
            authors = self.filters.get('authors')
            kinds = self.filters.get('kinds')

            event_rows = db_conn.iteritems()
            event_rows.seek(b'timeline_')
            for event_key, event_id in event_rows:
                if not event_key.startswith(b'timeline_'):
                    break
                print(event_key, event_id)
                event_row = db_conn.get(b'event_%s' % event_id)
                event = tornado.escape.json_decode(event_row)
                rsp = ["EVENT", subscription_id, event]
                rsp_json = tornado.escape.json_encode(rsp)
                self.write_message(rsp_json)

            rsp = ["EOSE", subscription_id]
            rsp_json = tornado.escape.json_encode(rsp)
            self.write_message(rsp_json)

        elif seq[0] == 'EVENT':
            kind = seq[1]['kind']
            event_id = seq[1]['id']
            addr = seq[1]['pubkey']
            content = seq[1]['content']
            tags = seq[1]['tags']
            timestamp = seq[1]['created_at']
            data = tornado.escape.json_encode(seq[1])
            sig = seq[1]['sig']

            msg = json.dumps([0, addr, timestamp, 3, tags, ''], separators=(',', ':'))
            message = eth_account.messages.encode_defunct(text=msg)
            print(message)
            print(eth_account.Account.recover_message(message, signature=bytes.fromhex(sig[2:])))

            if kind == 0:
                db_conn.put(b'profile_%s' % (addr.encode('utf8')), tornado.escape.json_encode(content).encode('utf8'))

            db_conn.put(b'event_%s' % (event_id.encode('utf8'), ), data.encode('utf8'))
            db_conn.put(b'user_%s_%s' % (addr.encode('utf8'), str(timestamp).encode('utf8')), event_id.encode('utf8'))
            db_conn.put(b'timeline_%s_%s' % (str(timestamp).encode('utf8'), addr.encode('utf8')), event_id.encode('utf8'))

            if kind == 3:
                tags = seq[1]['tags']
                for tag in tags:
                    if tag[0] == 'follow':
                        print('follow', tag)

                    elif tag[0] == 'unfollow':
                        print('unfollow', tag)


        elif seq[0] == 'CLOSE':
            pass


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('static/index.html')

class TweetHandler(tornado.web.RequestHandler):
    def get(self):
        event = self.get_argument('event')
        self.render('static/tweet.html')

class ProfileHandler(tornado.web.RequestHandler):
    def get(self):
        addr = self.get_argument('addr')
        self.render('static/profile.html')

class ProfileAPIHandler(tornado.web.RequestHandler):
    def get(self):
        addr = self.get_argument('addr')
        content = db_conn.get(b'profile_%s' % (addr.encode('utf8')))
        self.finish(tornado.escape.json_decode(content))

class FollowingAPIHandler(tornado.web.RequestHandler):
    def get(self):
        addr = self.get_argument('addr')
        content = db_conn.get(b'profile_%s' % (addr.encode('utf8')))
        self.finish(tornado.escape.json_decode(content))

class FollowedAPIHandler(tornado.web.RequestHandler):
    def get(self):
        addr = self.get_argument('addr')
        content = db_conn.get(b'profile_%s' % (addr.encode('utf8')))
        self.finish(tornado.escape.json_decode(content))

class TestAPIHandler(tornado.web.RequestHandler):
    def post(self):
        sig = self.request.body
        print(sig)
        message = eth_account.messages.encode_defunct(text='abcd')
        print(message)
        print(eth_account.Account.recover_message(message, signature=bytes.fromhex(sig[2:].decode('utf8'))))
        # print((web3.Web3()).eth.account.recover_message(message, signature=bytes.fromhex(sig[2:].decode('utf8'))))


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
                (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": './static/'}),
                (r"/relay", RelayHandler),
                (r"/tweet", TweetHandler),
                (r"/profile", ProfileHandler),
                (r"/api/profile", ProfileAPIHandler),
                (r"/api/following", FollowingAPIHandler),
                (r"/api/followed", FollowedAPIHandler),
                (r"/api/test", TestAPIHandler),
                (r"/", MainHandler),
            ]
        settings = {"debug": True}

        tornado.web.Application.__init__(self, handlers, **settings)


def main():
    server = Application()
    server.listen(8010, '0.0.0.0')
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()

