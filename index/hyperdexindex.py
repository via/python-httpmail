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

    def _init_user(self):
        if not self.client.get(self.tags, self.user):
            self.client.put(self.tags, self.user, {'tags': set([]), 'created': 0})

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

    def _update_tag_count(self, tag, delta):
        self.client.map_atomic_add(self.tags, self.user, {'tag_count': {str(tag): delta}})

    def _update_tag_unread_count(self, tag, delta):
        self.client.map_atomic_add(self.tags, self.user, {'tag_unread_count': {str(tag): delta}})

    def _update_tag_modified(self, tag):
        self.client.map_add(self.tags, self.user, {'tag_modified': {str(tag): int(time.time())}})

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
 
        res = [msg['uuid'] for msg in self.client.sorted_search(self.messages, filters, sortfield, limit[0] + limit[1], sortdir)]
        return res[0:len(res) - limit[1]][::-1]

    def list_tags(self):
        self._init_user()
        tags = self.client.get(self.tags, self.user)['tags']
        return list(tags) or []

    def get_tag(self, tag):
        if not tag in self.list_tags():
            return None
        tagdata = self.client.get(self.tags, self.user)
        r = {"count": tagdata['tag_count'][tag],
             "unread": tagdata['tag_unread_count'][tag],
             "created": tagdata['tag_created'][tag],
             "last-modified": tagdata['tag_modified'][tag]}
        return r

    def put_tag(self, tag):
        if not self.client.get(self.tags, self.user):
           self._init_user()
        self.client.set_add(self.tags, self.user, {'tags': str(tag)})
        self.client.map_add(self.tags, self.user, {'tag_unread_count': {str(tag): 0}})
        self.client.map_add(self.tags, self.user, {'tag_count': {str(tag): 0}})
        self.client.map_add(self.tags, self.user, {'tag_created': {str(tag): int(time.time())}})
        self.client.map_add(self.tags, self.user, {'tag_modified': {str(tag): int(time.time())}})

    def del_tag(self, tag):
        pass

    def get_message(self, uuid):
        msg = self.client.get(self.messages, uuid)
        del msg['dateint']
        del msg['user']
        msg['tags'] = list(msg['tags'])
        msg['flags'] = list(msg['flags'])
        return msg

    def put_message_tags(self, uuid, newtags):
        totaltags = self.client.get(self.tags, self.user)['tags']
        flags = self.client.get(self.tags, self.user)['flags']
        if not set(newtags).issubset(totaltags):
            raise TagNotFound()
        for old in totaltags:
            if old not in newtags:
                self._update_tag_modified(old)
                self._update_tag_count(old, -1)
                if "\\Seen" not in flags:
                    self._update_tag_unread_count(old, -1)
        for new in newtags:
            if new not in totaltags:
                self._update_tag_unread_count(new, 1)
                self._update_tag_modified(new)
                if "\\Seen" not in flags:
                    self._update_tag_unread_count(new, 1)
        self.client.put(self.messages, str(uuid), {'tags': set(newtags)})

    def put_message_flags(self, uuid, flags):
        oldflags = self.client.get(self.tags, self.user)['flags']
        tags = self.client.get(self.tags, self.user)['tags']
        self.client.put(self.messages, str(uuid), {'flags': set([str(x) for x in flags])})
        if "\\Seen" in oldflags and "\\Seen" not in flags:
            for tag in tags:
                self._update_tag_unread_count(tag, 1)
        if "\\Seen" not in oldflags and "\\Seen" in flags:
            for tag in tags:
                self._update_tag_unread_count(tag, -1)
        for tag in tags:
            self._update_tag_modified(tag)        

    def _encode_strings(self, msg):
        for field in ['to', 'from', 'cc', 'bcc', 'subject', 'date']:
            msg[field] = msg[field].decode('iso-8859-1').encode('utf-8')
        msg['flags'] = [x.decode('iso-8859-1').encode('utf-8') for x in msg['flags']]
        msg['tags'] = [x.decode('iso-8859-1').encode('utf-8') for x in msg['tags']]
        return msg
    
    def put_message(self, uuid, msg):
        self._init_user()
        msg = self._encode_strings(msg)
        msg['tags'] = set(msg['tags'])
        msg['flags'] = set(msg['flags'])
        msg['dateint'] = self._parse_date(msg['date'])
        msg['user'] = self.user
        self.client.put(self.messages, uuid, msg)
        self._update_size(msg['size'])
        for tag in msg['tags']:
            self._update_tag_modified(tag)        
            self._update_tag_count(tag, 1)
            if '\\Seen' not in msg['flags']:
                self._update_tag_unread_count(tag, 1)
        self._update_modified()
         

    def del_message(self, uuid):
        msg = self.get_message(uuid)
        self.client.delete(self.messages, uuid)
        self._update_size(-msg['size'])
        for tag in msg['tags']:
            self._update_tag_modified(tag)        
            self._update_tag_count(tag, -1)
            if '\\Seen' in msg['flags']:
                self._update_tag_unread_count(tag, -1)
        self._update_modified()

    def get_user(self):
        self._init_user()
        row = self.client.get(self.tags, self.user)
        count = sum(row['tag_count'].values())
        u = {"user": self.user,
             "created": row['created'],
             "modified": row['modified'],
             "size": row['size'],
             "count": count
            }
        return u
