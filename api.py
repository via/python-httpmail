import s3storage
import tokyocabinetindex
import json
import uuid
import time
import datetime
from email.parser import FeedParser
from flask import Flask, request

app = Flask(__name__)
s3access = 'M9S2K57Q3ECS3F3HEAN8'
s3secret = 'csbQniDf3klLf8AsfaZMoMNG3hQ8l69Ge3gLURlh'
s3host = 'api1.cluster.matthewvia.info'

def _msg_to_dict(rawmsg):
    parser = FeedParser()
    parser.feed(rawmsg)
    try: 
        msg = parser.close()
    except:
        return {}
    data = {
        'to': msg['to'] if 'to' in msg else '',
        'from': msg['from'] if 'from' in msg else '',
        'bcc': msg['bcc'] if 'bcc' in msg else '',
        'subject': msg['subject'] if 'subject' in msg else '',
        'cc': msg['cc'] if 'cc' in msg else '',
        'size': len(msg.__str__()),
        'date': msg['date'] if 'date' in msg else '0'
    }
    return data

@app.route('/mailboxes/<mailbox>/tags/')
def tags_get(mailbox):
    i = tokyocabinetindex.TokyoCabinetIndex(mailbox)
    return json.dumps(i.list_tags())

@app.route('/mailboxes/<mailbox>/tags/<tag>')
def tag_get(mailbox, tag):
    i = tokyocabinetindex.TokyoCabinetIndex(mailbox)
    tag = i.get_tag(tag)
    return ("", 200, {
        "X-Total-Count": tag['count'],
        "X-Unread-Count": tag['unread']
    })


@app.route('/mailboxes/<mailbox>/tags/<tag>', methods=['PUT'])
def tag_put(mailbox, tag):
    i = tokyocabinetindex.TokyoCabinetIndex(mailbox)
    if tag in i.list_tags():
        return ("Tag already exists", 409)
    i.put_tag(tag)
    return ("", 204)

@app.route('/mailboxes/<mailbox>/tags/<tag>', methods=['DELETE'])
def tag_delete(mailbox, tag):
    i = tokyocabinetindex.TokyoCabinetIndex(mailbox)
    return ("Not implemented", 501)

@app.route('/mailboxes/<mailbox>/messages/', methods=['POST'])
def put_message(mailbox):
    i = tokyocabinetindex.TokyoCabinetIndex(mailbox)
    s = s3storage.S3Storage(mailbox, s3host, s3access, s3secret)
    u = uuid.uuid4()
    msg = request.data
    attrs = { 'tags': [],
              'flags': [],
              'stored': 999 }
    s.put_message(u, msg, attrs)
    indexed_message = _msg_to_dict(msg) 
    indexed_message.update(attrs)
    i.put_message(u, indexed_msg)
     
@app.route('/mailboxes/<mailbox>/messages/<message>/tags')
def get_message_tags(mailbox, message):
    i = tokyocabinetindex.TokyoCabinetIndex(mailbox)
    return (json.dumps(i.get_message(str(message))['tags']), 200)

@app.route('/mailboxes/<mailbox>/messages/<message>/tags/<tag>', methods=['PUT', 'DELETE'])
def put_message_tags(mailbox, message, tag):
    i = tokyocabinetindex.TokyoCabinetIndex(mailbox)
    s = s3storage.S3Storage(mailbox, s3host, s3access, s3secret)
    newtags = set([str(tag)])
    tags = set(i.get_message(str(message))['tags'])
    if request.method == 'PUT':
        if tag not in i.list_tags():
            i.put_tag(tag)
        tags = tags.union(newtags)
    elif request.method == 'DELETE':
        tags = tags.difference(newtags)
    i.put_message_tags(message, list(tags))
    attrs = s.get_attrs(str(message))
    attrs['tags'] = list(tags)
    s.put_attrs(message, attrs)
    return ""

@app.route('/mailboxes/<mailbox>/messages/<message>/flags/')
def get_flags(mailbox, message):
    i = tokyocabinetindex.TokyoCabinetIndex(mailbox)
    return json.dumps(i.get_message(str(message))['flags'])

@app.route('/mailboxes/<mailbox>/messages/<message>/flags/<flag>')
def get_flag_enabled(mailbox, message, flag):
    i = tokyocabinetindex.TokyoCabinetIndex(mailbox)
    if str(flag) in i.get_message(str(message))['flags']:
        return ("", 200)
    else:
        return ("Not Found", 404)

@app.route('/mailboxes/<mailbox>/messages/<message>/flags/<flag>', methods=['PUT', 'DELETE'])
def put_flag(mailbox, message, flag):
    i = tokyocabinetindex.TokyoCabinetIndex(mailbox)
    s = s3storage.S3Storage(mailbox, s3host, s3access, s3secret)
    newflags = set([str(flag)])
    flags = set(i.get_message(str(message))['flags'])
    if request.method == 'PUT':
        flags = flags.union(newflags)
    elif request.method == 'DELETE':
        flags = flags.difference(newflags)
    i.put_message_flags(message, list(flags))
    attrs = s.get_attrs(str(message))
    attrs['flags'] = list(flags)
    s.put_attrs(message, attrs)
    return ""

@app.route('/mailboxes/<mailbox>/messages/<message>')
def get_message(mailbox, message):
    s = s3storage.S3Storage(mailbox, s3host, s3access, s3secret)
    rawmsg = s.get_message(str(message))
    if request.method == 'HEAD':
        parser = FeedParser()
        parser.feed(rawmsg)
        try: 
            msg = parser.close()
        except:
            return ("Unable to parse message", 500)
        return ''.join(["%{0}: {1}\n".format(k, v) for (k, v) in msg.items()])
    else:
        return rawmsg     

@app.route('/mailboxes/<mailbox>/messages/<message>/meta')
def get_message_meta(mailbox, message):
    i = tokyocabinetindex.TokyoCabinetIndex(mailbox)
    return json.dumps(i.get_message(str(message)))

@app.route('/mailboxes/<mailbox>/messages/<message>', methods=['DELETE'])
def del_message(mailbox, message):
    s = s3storage.S3Storage(mailbox, s3host, s3access, s3secret)
    i = tokyocabinetindex.TokyoCabinetIndex(mailbox)
    s.del_message(message)
    i.del_message(message)

@app.route('/mailboxes/<mailbox>/messages/')
def list_messages(mailbox):
    i = tokyocabinetindex.TokyoCabinetIndex(mailbox)
    return json.dumps(i.list_messages())
    

if __name__ == "__main__":
    app.run(debug=True)
