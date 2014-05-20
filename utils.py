from email.parser import FeedParser
import sys
import s3storage
import tokyocabinetindex
import uuid
import mailbox
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
    index.put_message(uuid, msg)
        

def sync_index(index, storage, full=False):
    i_list = index.list_messages([], [])
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


if __name__=="__main__":
    s = s3storage.S3Storage('matthew.via-mailtrust.com', 'api1.cluster.matthewvia.info', 'M9S2K57Q3ECS3F3HEAN8', 'csbQniDf3klLf8AsfaZMoMNG3hQ8l69Ge3gLURlh')
    i = tokyocabinetindex.TokyoCabinetIndex('matthew.via@mailtrust.com')
    sync_index(i, s, False)
    sys.exit(0)
    mailboxname = sys.argv[1]
    maildirpath = sys.argv[2]
    for msg in mailbox.Maildir(maildirpath, factory=None):
        attrs = { 'tags': [mailboxname],
                  'flags': ['\\Seen'],
                  'stored': str(int(msg.get_date())) }
        u = str(uuid.uuid4())
        s.put_message(u, str(msg), attrs)
        print u
