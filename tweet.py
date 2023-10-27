
import tornado.escape

def reply(root_tweet, parent_id, reply_tweet):
    if root_tweet['id'] == parent_id:
        root_tweet.setdefault('replies', [])
        root_tweet['replies'].append(reply_tweet)
        return

    tweet = _get(root_tweet['replies'], parent_id)
    #print('reply', tweet)
    tweet.setdefault('replies', [])
    tweet['replies'].append(reply_tweet)


def _get(replies, reply_id):
    for reply in replies:
        #print('reply', reply)
        if reply['id'] == reply_id:
            return reply
    for reply in replies:
        r = get(reply.get('replies', []), reply_id)
        if r:
            return r

def reply2(root_tweet, parent_id, reply_tweet):
    queue = [root_tweet]
    while queue:
        obj = queue.pop(0)
        #print(obj['id'])
        if obj['id'] == parent_id:
            obj.setdefault('replies', [])
            obj['replies'].append(reply_tweet)
            return

        for reply in obj.get('replies', []):
            queue.append(reply)

def load_content(db_conn, tweet_obj):
    queue = [tweet_obj]
    while queue:
        obj = queue.pop(0)
        print(obj['id'])
        event_json = db_conn.get(('event_%s' % obj['id']).encode('utf8'))
        event = tornado.escape.json_decode(event_json)
        obj['content'] = event['content']
        obj['author'] = event['pubkey']
        for reply in obj.get('replies', []):
            queue.append(reply)

if __name__ == '__main__':
    t = {'id': '1', 'replies': [ {'id':'11', 'replies':[ {'id':'111', 'replies':[]} ]} ]}
    print(t)

    #print(_get(t, '1'))
    #print(_get(t['replies'], '11'))
    #print(_get(t['replies'], '111'))

    reply2(t, '1', {'id':'12'})
    print(t)

    reply2(t, '12', {'id':'121'})
    print(t)

    reply2(t, '111', {'id':'1112'})
    print(t)
    #load_content(None, t)

