
import os

import rocksdb

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
            timestamp = seq[1]['created_at']
            data = tornado.escape.json_encode(seq[1])
            if kind == 0:
                db_conn.put(b'profile_%s' % (addr.encode('utf8')), tornado.escape.json_encode(content).encode('utf8'))

            db_conn.put(b'event_%s' % (event_id.encode('utf8'), ), data.encode('utf8'))
            db_conn.put(b'user_%s_%s' % (addr.encode('utf8'), str(timestamp).encode('utf8')), event_id.encode('utf8'))
            db_conn.put(b'timeline_%s_%s' % (str(timestamp).encode('utf8'), addr.encode('utf8')), event_id.encode('utf8'))

            if kind == 3:
                tags = seq[1]['tags']
                for tag in tags:
                    if tag[0] == 'p': # follow
                        pass
                    elif tag[0] == 'b': # block
                        pass


        elif seq[0] == 'CLOSE':
            pass


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('static/index.html')


class ProfileHandler(tornado.web.RequestHandler):
    def get(self):
        addr = self.get_argument('addr')
        content = db_conn.get(b'profile_%s' % (addr.encode('utf8')))
        self.finish(tornado.escape.json_decode(content))


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
                (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": './static/'}),
                (r"/relay", RelayHandler),
                (r"/profile", ProfileHandler),
                (r"/", MainHandler),
            ]
        settings = {"debug": True}

        tornado.web.Application.__init__(self, handlers, **settings)


def main():
    # worker_threading = threading.Thread(target=miner.worker_thread)
    # worker_threading.start()
    # chain.worker_thread_pause = False

    server = Application()
    server.listen(8010, '0.0.0.0')
    tornado.ioloop.IOLoop.instance().start()

    # worker_threading.join()

if __name__ == '__main__':
    main()

