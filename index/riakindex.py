from email import utils
import json
import filter
import os
import time
import uuid
import riak

name='RiakIndex'

class TagNotFound(Exception):
    pass

class MessageNotFound(Exception):
    pass

class RiakIndex():
 
    """
    tag list format:
    "tagname": { "count": 0,
                 "unread": 0,
                 "created": date int,
                 "last-modified": date int
                 }
    
    message format:
    "uuid": { "tags": []
              "flags": []
              "to": "to header",
              "from": "from header",
              "cc": "cc header",
              "bcc": "bcc header",
              "subject": subject header",
              "size": size int,
              "date": "date header",
              "stored": unix timestamp int,
            }
    The index internally stores this as is, with the addition of a 
    'date_int' field containing unixtimestamp version of the Date header
    for fast indexing, as well as json encoded versions of the tags
    and space delimited version of the flags.
    
    """

    def __init__(self, config, user, readonly):
        self.client = riak.RiakClient(protocol=config['proto'], host=config['host'], 
                                      http_port=config['port'])
        self.user = user
        self.tagbucket = 'tags'

    def _remove_suffix(self, msg):
        newmsg = {}
        newmsg['date'] = msg['date_s']
        newmsg['size'] = int(msg['size_i'])
        newmsg['stored'] = int(msg['stored_i'])
        newmsg['tags'] = msg['tags_s']
        newmsg['flags'] = msg['flags_s']
        newmsg['to'] = msg['to_s'] 
        newmsg['from'] = msg['from_s'] 
        newmsg['cc'] = msg['cc_s'] 
        newmsg['bcc'] = msg['bcc_s'] 
        newmsg['subject'] = msg['subject_s'] 
        return newmsg

    def _add_suffix(self, msg):
        newmsg = {}
        newmsg['date_int_i'] = int(utils.mktime_tz(utils.parsedate_tz(msg['date'])))
        newmsg['date_s'] = msg['date']
        newmsg['size_i'] = int(msg['size'])
        newmsg['stored_i'] = int(msg['stored'])
        newmsg['tags_s'] = msg['tags']
        newmsg['flags_s'] = msg['flags']
        newmsg['to_s'] = msg['to'] 
        newmsg['from_s'] = msg['from'] 
        newmsg['cc_s'] = msg['cc'] 
        newmsg['bcc_s'] = msg['bcc'] 
        newmsg['subject_s'] = msg['subject'] 
        return newmsg


    def list_messages(self, filterlist=[], sort=None, limit=None):
        if len(filterlist) == 0:
            query = ["*:*"]
        else:
            query = []
        for fil, verb, value in filterlist:
            if fil in ['to', 'from', 'cc', 'bcc', 'subject']:
                query.append("{0}_s:*{1}*".format(fil, value))
            if fil in ['stored', 'size']:
                if verb is filter.FilterVerb.Greater:
                    query.append("{0}_i:[{1} TO *]".format(fil, value))
                if verb is filter.FilterVerb.Less:
                    query.append("{0}_i:[0 TO {1}]".format(fil, value))
            if fil in ['tag', 'flag']:
                query.append("{0}_s:{1}".format(fil, value))
            if fil in ['date']:
               d = time.mktime(utils.parsedate(value))
               if verb is filter.FilterVerb.Greater:
                   query.append("date_int_i:[{1} TO *]".format(value))
               if verb is filter.FilterVerb.Less:
                   query.append("date_int_i:[0 TO {1}]".format(value))
               
            
        querystr = " AND ".join(query)
        print querystr
        if limit is None:
            limit = (0, 50)
        res = self.client.fulltext_search(self.user, querystr, start=limit[1], rows=limit[0])
        return [doc['_yz_rk'] for doc in res['docs']]
        

    def list_tags(self):
        tags = self.client.bucket(self.tagbucket).get(self.user).data
        return tags or []

    def get_tag(self, tag):
        if not tag in self.list_tags():
            return None
        r = {"count": self.client.fulltext_search(self.user, "tags_s:{0}".format(tag))['num_found'],
             "unread": self.client.fulltext_search(self.user, "tags_s:{0} AND NOT flags_s:\\\\Seen".format(tag))['num_found'],
             "created": 0,
             "last-modified": 0}
        return r

    def put_tag(self, tag):
        tags = self.client.bucket(self.tagbucket).get(self.user)
        newtags = set(tags.data)
        newtags.update([tag])
        tags.data = list(newtags)
        tags.store()
        
    def del_tag(self, tag):
        pass

    def get_message(self, uuid):
        msg = self.client.bucket(self.user).get(uuid).data
        del msg['date_int_i']
        msg = self._remove_suffix(msg)
        return msg

    def put_message_tags(self, uuid, newtags):
        totaltags = set(self.list_tags)
        if not set(newtags).issubset(totaltags):
            raise TagNotFound()
        msg = self.client.bucket(self.user).get(uuid)
        msg.data['tags_s'] = newtags
        msg.store()

    def put_message_flags(self, uuid, flags):
        msg = self.client.bucket(self.user).get(uuid)
        msg.data['flags_s'] = flags
        msg.store()
    
    def put_message(self, uuid, msg):
        newmsg = self._add_suffix(msg)
        bucket = self.client.bucket(self.user)
        k = bucket.new(uuid, data=newmsg)
        k.store()

    def del_message(self, uuid):
        self.table.out(str(uuid))
