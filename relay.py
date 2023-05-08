
import tornado.web
import tornado.ioloop
import tornado.options
import tornado.httpserver
import tornado.httpclient
import tornado.gen
import tornado.escape
import tornado.websocket


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
        # RelayHandler ["REQ","37930892842193953",{"kinds":[0,1,2,7],"since":1683442864,"limit":450}]
        # RelayHandler ['EVENT', {'kind': 0, 'pubkey': '0xEEFb88140A1EBC85f49023bBb44BB30E36555849', 'content': '{"name":"KJJ","about":"","picture":""}', 'tags': [['nonce', '19745', '16']], 'created_at': 1683529334, 'sig': '0x47e3c560f619547f8101a91c5d0f383ed072b56c64487f3faaf1eeecad317b5a1ce70d6016b4412a93aa626dbc80b57771658d735087ee46f89f631984cffac11b', 'id': '00008f65c66c19757cf8202dc899e1276fd31c47fe18882b0eeab00fe48c9943'}]
        # RelayHandler ['REQ', '37930892842193953', {'kinds': [0, 1, 2, 7], 'since': 1683442864, 'limit': 450}]
        # RelayHandler ['REQ', 'monitor-00008', {'ids': ['00008f65c66c19757cf8202dc899e1276fd31c47fe18882b0eeab00fe48c9943']}]
        # RelayHandler ['CLOSE', 'monitor-00008']
        # RelayHandler ['EVENT', {'kind': 1, 'content': 'Hi baby', 'pubkey': '0xEEFb88140A1EBC85f49023bBb44BB30E36555849', 'tags': [], 'created_at': 1683529357, 'id': '872e001a8b79c8bce2d2be4f49afea2941991893fd2e7f21d65aa4df0b914173', 'sig': '0xd48358ae8461182dbc7905a2738fb662dace6a6a327644c29ba919c00115839c73aae1c3e8c3bc9f06d16e9a2b3348dd3fccd6a1d811e728519334071f65b9451b'}]
        # RelayHandler ['REQ', 'monitor-872e0', {'ids': ['872e001a8b79c8bce2d2be4f49afea2941991893fd2e7f21d65aa4df0b914173']}]
        # RelayHandler ['CLOSE', 'monitor-872e0']

        seq = tornado.escape.json_decode(message)
        print("RelayHandler", seq)

        if seq[0] == 'REQ':
            pass
        elif seq[0] == 'EVENT':
            pass
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
        settings = {"debug":True}

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

