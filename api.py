import config
import json
import uuid
import filter
import time
import datetime
from email.parser import FeedParser
from email.message import Message
from flask import Flask, request
from flask.ext.runner import Runner

app = Flask(__name__)
runner = Runner(app)

siteconfig = config.SiteConfig('httpmail.conf')
endpoint = siteconfig.api()['endpoint']

def _mailbox_url(mailbox):
    return "{0}/mailboxes/{1}".format(endpoint, mailbox)

def _message_url(mailbox, msg):
    return "{0}/mailboxes/{1}/messages/{2}".format(endpoint, mailbox, msg)

def _folder_url(mailbox, folder):
    return "{0}/mailboxes/{1}/{2}".format(endpoint, mailbox, folder)

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

@app.route('/mailboxes/<mailbox>')
def mailbox_get(mailbox):
    i = siteconfig.index()
    box = i.get_user(mailbox)
    res = { 'id': mailbox,
            'date-created': box['created'],
            'date-modified': box['modified'],
            'message-count': box['count'],
            'mailbox-size': box['size'] 
          }
    return (json.dumps(res), 200, {
               'Content-Type': 'application/json' })
    
def _format_folder(i, mailbox, folder):
    f = { 'folder': folder,
	  'message-count': int(i.get_folder(mailbox, folder)['count']),
	  'unread-count': int(i.get_folder(mailbox, folder)['unread']),
	  'created': i.get_folder(mailbox, folder)['created'],
	  'last-modified': i.get_folder(mailbox, folder)['last-modified'],
	  'mailbox-url': _mailbox_url(mailbox),
	  'url': _folder_url(mailbox, folder)
    }
    return f

@app.route('/mailboxes/<mailbox>/folders/')
def folders_get(mailbox):
    i = siteconfig.index()
    res = [ _format_folder(i, mailbox, folder) for folder in i.list_folders(mailbox) ]
    return (json.dumps(res), 200,
               {'Content-Type': 'application/json'})

@app.route('/mailboxes/<mailbox>/folders/<folder>')
def folder_get(mailbox, folder):
    i = siteconfig.index()
    if request.method == 'HEAD':
        folder = i.get_folder(mailbox, folder)
        return ("", 200, {
            'X-Total-Count': folder['count'],
            'X-Unread-Count': folder['unread']
        })
    else:
        return (json.dumps(_format_folder(i, mailbox, folder)), 200, 
                   {'Content-Type': 'application/json'})


@app.route('/mailboxes/<mailbox>/folders/<folder>', methods=['PUT'])
def folder_put(mailbox, folder):
    i = siteconfig.index()
    if folder in i.list_folders(mailbox):
        return ('Tag already exists', 409)
    i.put_folder(mailbox, folder)
    return (json.dumps(_format_folder(i, mailbox, folder)), 201,
               {'Content-Type': 'application/json'})

@app.route('/mailboxes/<mailbox>/folders/<folder>', methods=['DELETE'])
def folder_delete(mailbox, folder):
    i = siteconfig.index()
    return ("Not implemented", 501)

def _msg_from_json(js):
    msg = Message()
    fields = json.loads(js)
    for field, val in fields['headers']:
        if isinstance(val, list):
            msg[field] = ','.join(val)
        else:
            msg[field] = val
    msg.set_payload(fields['body'])
    return str(m)
    

def _msg_to_response(i, s, mailbox, msgid, get_body=False):
    res = {}
    msgi = i.get_message(mailbox, msgid)

    structure = msgi['bodystructure']
    #TODO: remove backend pointers from structure
    if get_body:
        pass
    res.update( {
        "id": msgid,
        "folder": msgi['folder'],
        "flags": msgi['flags'],
        "url": _message_url(mailbox, msgid),
        "url-mailbox": _mailbox_url(mailbox),
        "headers": {
            "subject": msgi['subject'],
            "from": msgi['from'],
            "to": msgi['to'].split(','),
            "cc": msgi['cc'].split(','),
            "bcc": msgi['bcc'].split(','),
            "date": msgi['date'] },
        "stored": msgi['stored'],
        "size": msgi['size'] ,
        "modified": msgi['modified'],
        "imap_uid": msgi['imap_uid'],
        "pop3_uidl": msgi['pop3_uidl'],
        "bodystructure": structure
        } })
        
@app.route('/mailboxes/<mailbox>/messages/', methods=['POST'])
def put_message(mailbox):
    i = siteconfig.index()
    s = siteconfig.storage()
    u = uuid.uuid4()
    if request.headers['content-type'] == 'application/json':
        msg = _msg_from_json(request.data)
    elif request.headers['content-type'] == 'message/rfc822':
        msg = request.data
    else:
        return ("Unknown Content-Type", 400)
    attrs = { 'folder': "",
              'flags': [],
              'stored': datetime.utcnow() }
    s.put_message(u, msg, attrs)
    indexed_message = _msg_to_dict(msg) 
    indexed_message.update(attrs)
    i.put_message(mailbox, u, indexed_message)
    res = _msg_to_response(i, s, mailbox, u)
    return (json.dumps(res), 200, 
        {"Content-Type": "application/json"} )
 
@app.route('/mailboxes/<mailbox>/messages/<message>/tags/')
def get_message_tags(mailbox, message):
    i = siteconfig.index(mailbox, readonly=True)
    return (json.dumps(i.get_message(str(message))['tags']), 200,
               {'Content-Type': 'application/json'})

@app.route('/mailboxes/<mailbox>/messages/<message>/tags/<tag>', methods=['PUT', 'DELETE'])
def put_message_tags(mailbox, message, tag):
    i = siteconfig.index(mailbox)
    s = siteconfig.storage(mailbox)
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
    return ("", 200)

@app.route('/mailboxes/<mailbox>/messages/<message>/flags/')
def get_flags(mailbox, message):
    i = siteconfig.index(mailbox, readonly=True)
    return (json.dumps(i.get_message(str(message))['flags']), 200,
               {'Content-Type': 'application/json'})


@app.route('/mailboxes/<mailbox>/messages/<message>/flags/<flag>')
def get_flag_enabled(mailbox, message, flag):
    i = siteconfig.index(mailbox, readonly=True)
    if str(flag) in i.get_message(str(message))['flags']:
        return ("", 200)
    else:
        return ("Not Found", 404)

@app.route('/mailboxes/<mailbox>/messages/<message>/flags/<flag>', methods=['PUT', 'DELETE'])
def put_flag(mailbox, message, flag):
    i = siteconfig.index(mailbox)
    s = siteconfig.storage(mailbox)
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
    return ("", 200)

@app.route('/mailboxes/<mailbox>/messages/<message>')
def get_message(mailbox, message):
    s = siteconfig.storage(mailbox)
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
        return (rawmsg, 200, {"Content-Type": "application/json"})

@app.route('/mailboxes/<mailbox>/messages/<message>/meta')
def get_message_meta(mailbox, message):
    i = siteconfig.index(mailbox, readonly=True)
    return (json.dumps(i.get_message(str(message))), 200, 
               {'Content-Type': 'application/json'})

@app.route('/mailboxes/<mailbox>/messages/<message>', methods=['DELETE'])
def del_message(mailbox, message):
    i = siteconfig.index(mailbox)
    s = siteconfig.storage(mailbox)
    s.del_message(message)
    i.del_message(message)
    return ("", 204, {"Content-Type": "application/json"})

def _encode_list_filter(f):
    field = f['field']
    if f['qualifier'] == '=':
        qual = filter.FilterVerb.Contains    
    elif f['qualifier'] == '>':
        qual = filter.FilterVerb.Greater    
    elif f['qualifier'] == '<':
        qual = filter.FilterVerb.Less    
    return (field, qual, f['value'])

@app.route('/mailboxes/<mailbox>/messages/')
def list_messages(mailbox):
    i = siteconfig.index(mailbox, readonly=True)
    try:
        body = json.loads(request.data)
    except:
        body = {'filters': []}
    list_filters = []
    sort = None
    limit = (request.args.get('limit'), request.args.get('skip'))
    if limit[0] is None or limit[1] is None:
        limit = None
    else:
        limit = (int(limit[0]), int(limit[1]))
     
    for filter in body['filters']:
        if filter['field'] in ['to', 'date', 'from', 'tag', 'flag', 'bcc', 'subject', 'cc', 'size', 'sent', 'stored']:
            list_filters.append(_encode_list_filter(filter))
        elif filter['field'] in ['header']:
            pass
        elif filter['field'] in ['body', 'text']:
            pass
    if 'sort' in body:
        sort = (body['sort']['field'], False if body['sort']['reverse'] else True)
  
    return (json.dumps(i.list_messages(filterlist=list_filters, sort=sort, limit=limit)),
            200, {"Content-Type": "application/json"})
    

if __name__ == "__main__":
    runner.run()
