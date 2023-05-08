
import os

import pymysql

import tornado.web
import tornado.ioloop
import tornado.options
import tornado.httpserver
import tornado.httpclient
import tornado.gen
import tornado.escape
import tornado.websocket

MYSQL_HOST = os.getenv('MYSQL_HOST', '127.0.0.1')
MYSQL_USER = os.getenv('MYSQL_USER', 'root')
MYSQL_PASS = os.getenv('MYSQL_PASS', 'root')
MYSQL_DB = os.getenv('MYSQL_DB', 'yestr')

db_connection = None
def get_db_cursor():
    global db_connection
    if not db_connection or db_connection._closed:
        db_connection = pymysql.connect(charset='utf8mb4',
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASS,
            database=MYSQL_DB,
        )
    db_connection.ping()
    db_connection.begin()
    return db_connection.cursor()


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
            cursor = get_db_cursor()
            cursor.execute('SELECT * FROM events')
            event_rows = cursor.fetchall()
            for event_row in event_rows:
                event = tornado.escape.json_decode(event_row[4])
                rsp = ["EVENT", subscription_id, event]
                rsp_json = tornado.escape.json_encode(rsp)
                self.write_message(rsp_json)

        elif seq[0] == 'EVENT':
            kind = seq[1]['kind']
            event_id = seq[1]['id']
            addr = seq[1]['pubkey']
            content = seq[1]['content']
            timestamp = seq[1]['created_at']
            data = tornado.escape.json_encode(seq[1])

            cursor = get_db_cursor()
            cursor.execute('INSERT INTO events (event_id, kind, addr, data, timestamp) VALUES (%s, %s, %s, %s, %s)', (event_id, kind, addr, data, timestamp))
            db_connection.commit()

        elif seq[0] == 'CLOSE':
            pass



class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.redirect('/dashboard')

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
                (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": './'}),
                (r"/relay", RelayHandler),
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

