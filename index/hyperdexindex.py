from email import utils
import json
import filter
import os
import time
import uuid
from datetime import datetime
from dateutil.parser import parse

from hyperdex.client import Client, Contains, Equals, LessThan, GreaterThan, Regex

name='HyperdexIndex'

class TagNotFound(Exception):
    pass

class MessageNotFound(Exception):
    pass

class HyperdexIndex():
 
    """
    tag list format:
    "user": { "tags": set of tags,
              "created": date int,
              "modified": date int
              "size": int
            }
    
    message format:
    "uuid": { "tags": set[])
              "flags": set([])
              "to": "to header",
              "from": "from header",
              "cc": "cc header",
              "bcc": "bcc header",
              "subject": subject header",
              "size": size int,
              "date": "date header",
              "dateint": date int
              "storeddate": unix timestamp int,
            }
    The index internally stores this as is, with the addition of a 
    'date_int' field containing unixtimestamp version of the Date header
    for fast indexing, as well as json encoded versions of the tags
    and space delimited version of the flags.
    
    """

    def __init__(self, config, user, readonly):
        self.client = Client(config['host'], int(config['port']))
          
        self.user = str(user)
        self.tags = config['tag_space']
        self.messages = config['message_space']

    def _parse_date(self, date):
        if date is None:
            dateint = 0
        else:
            dtime = utils.parsedate_tz(date)
            if dtime is None:
                try:
                    dtime = parse(date)
                except:
                    dtime = datetime.now()
                dtime = dtime.timetuple()+ (0,)
            dateint = int(utils.mktime_tz(dtime))
        return dateint

    def _update_size(self, delta):
        self.client.atomic_add(self.tags, self.user, {'size': delta})

    def _update_modified(self):
        self.client.put(self.tags, self.user, {'modified': int(time.time())})

    def _number_compare(self, verb, number):
        if verb is filter.FilterVerb.Contains:
            return Equals(number)
        if verb is filter.FilterVerb.Less:
            return LessThan(number)
        if verb is filter.FilterVerb.Greater:
            return GreaterThan(number)

    def list_messages(self, filterlist=[], sort=None, limit=None):
        filters = {'user': self.user}
        
        for filter, verb, value in filterlist:
            if filter in ['to', 'from', 'cc',
                    'bcc', 'subject']:
                filters[filter] = Regex(str(value))
            elif filter in ['stored', 'size']:
                filters[filter] = self._number_compare(verb, int(value))
            elif filter in ['date']:
                d = time.mktime(utils.parsedate(value))
                filters['dateint'] = self._number_compare(verb, int(d))
            elif filter in ['tag']:
                filters['tags'] = Contains(str(value))
            elif filter in ['flag']:
                filters['flags'] = Contains(str(value))
                
        if sort is None:
            sortfield = 'uuid'
        elif sort[0] == 'date':
            sortfield = 'dateint'
        else:
            sortfield = str(sort[0])
        
        if not sort or sort[1] is True:
            sortdir = 'maximize'
        else:
            sortdir = 'minimize'

        if limit is None:
            limit = (50, 0)
        return [msg['uuid'] for msg in self.client.sorted_search(self.messages, filters, sortfield, limit[0] + limit[1], sortdir)][::-1][limit[1]:]
 
        

    def list_tags(self):
        tags = self.client.get(self.tags, self.user)['tags']
        return list(tags) or []

    def get_tag(self, tag):
        if not tag in self.list_tags():
            return None
        count = self.client.count(self.messages, {'user': self.user, 'tags': Contains(str(tag))})
        r = {"count": count,
             "unread": count - self.client.count(self.messages, {'user': self.user,
                                                                 'tags': Contains(tag),
                                                                 'flags': Contains('\\Seen')}),
             "created": 0,
             "last-modified": 0}
        return r

    def put_tag(self, tag):
        if not self.client.get(self.tags, self.user):
            self.client.put(self.tags, self.user, {'tags': set([]), 'created': 0})
        self.client.set_add(self.tags, self.user, {'tags': str(tag)})

    def del_tag(self, tag):
        pass

    def get_message(self, uuid):
        msg = self.client.get(self.messages, uuid)
        del msg['dateint']
        msg['tags'] = list(msg['tags'])
        msg['flags'] = list(msg['flags'])
        return msg

    def put_message_tags(self, uuid, newtags):
        totaltags = self.client.get(self.tags, self.user)['tags']
        if not set(newtags).issubset(totaltags):
            raise TagNotFound()
        print newtags
        self.client.put(self.messages, str(uuid), {'tags': set(newtags)})

    def put_message_flags(self, uuid, flags):
        self.client.put(self.messages, str(uuid), {'flags': set([str(x) for x in flags])})

    def _encode_strings(self, msg):
        for field in ['to', 'from', 'cc', 'bcc', 'subject', 'date']:
            msg[field] = msg[field].decode('iso-8859-1').encode('utf-8')
        msg['flags'] = [x.decode('iso-8859-1').encode('utf-8') for x in msg['flags']]
        msg['tags'] = [x.decode('iso-8859-1').encode('utf-8') for x in msg['tags']]
        return msg
    
    def put_message(self, uuid, msg):
        msg = self._encode_strings(msg)
        msg['tags'] = set(msg['tags'])
        msg['flags'] = set(msg['flags'])
        msg['dateint'] = self._parse_date(msg['date'])
        msg['user'] = self.user
        self.client.put(self.messages, uuid, msg)
        self._update_size(msg['size'])
        self._update_modified()
         

    def del_message(self, uuid):
        size = self.get_message(uuid)['size']
        self.client.delete(self.messages, uuid)
        self._update_size(-size)
        self._update_modified()

    def get_user(self):
        row = self.client.get(self.tags, self.user)
        u = {"user": self.user,
             "created": row['created'],
             "modified": row['modified'],
             "size": row['size'],
             "count": self.client.count(self.messages, {'user': self.user})
            }
        return u
