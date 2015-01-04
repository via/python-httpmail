from email.parser import FeedParser
import sys
import config
import optparse
import uuid
import mailbox
import urllib
import time
from datetime import datetime
import imaplib

def msg_to_dict(rawmsg):
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

def index_message(index, uuid, rawmsg, attrs):
    msg = msg_to_dict(rawmsg)
    for tag in attrs['tags']:
        if tag not in index.list_tags():
            index.put_tag(str(tag))
    msg.update(attrs)
    print msg
    index.put_message(uuid, msg)
        

def sync_index(index, storage, full=False):
    i_list = index.list_messages([])
    s_list = storage.list()
    for uid in s_list:
        print uid
        if uid in i_list and not full:
               #check flags/tags
                pass
        else:
            index_message(index, uid, storage.get_message(uid), storage.get_attrs(uid))
    for gone_uid in set(i_list).difference(set(s_list)):
        index.del_message(gone_uid)

def import_maildir(path, storage, name):
    for msg in mailbox.Maildir(path, factory=None):
        attrs = { 'tags': [name],
                  'flags': ['\\Seen'],
                  'stored': str(int(msg.get_date())) }
        u = str(uuid.uuid4())
        storage.put_message(u, str(msg), attrs)
        print u

if __name__=="__main__":
    parser = optparse.OptionParser()
    parser.add_option("-u", "--user", dest="user", help="User to act on")
    parser.add_option("-I", "--import", dest="maildir", 
        help="Import specified maildir to storage")
    parser.add_option("-S", "--sync", dest="sync", action="store_true", 
        help="Sync index with storage")
    parser.add_option("-c", "--config", dest="config", 
        help="Path to config file", default="httpmail.conf")

    (options, args) = parser.parse_args()
    conf = config.SiteConfig(options.config)
    index = conf.index(options.user) 
    storage = conf.storage(options.user) 

    if options.maildir:
        import_maildir(options.maildir, storage, 'archive') 

    if options.sync:
        sync_index(index, storage, False)
