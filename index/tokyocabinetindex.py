from tokyocabinet import table, btree
from email import utils
import json
import filter
import os
import time
from datetime import datetime
import uuid

name='TokyoCabinetIndex'

class TagNotFound(Exception):
    pass

class MessageNotFound(Exception):
    pass

class TokyoCabinetIndex():
 
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
              "stored" unix timestamp int,
            }
    The index internally stores this as is, with the addition of a 
    'date_int' field containing unixtimestamp version of the Date header
    for fast indexing, as well as json encoded versions of the tags
    and space delimited version of the flags.
    
    """

    def __init__(self, config, user, readonly):
        path = os.path.join(config['basepath'], user)
        self.table = table.Table()
        flags = table.TDBOCREAT
        if not readonly:
            flags = flags | table.TDBOWRITER
        self.table.open(path, flags)

        self.tags = table.Table()
        self.tags.open("{0}-tags".format(path), flags)

    def _verb_to_tcfilter(self, verb):
        if verb is filter.FilterVerb.Greater: 
            return table.TDBQCNUMGT 
        if verb is filter.FilterVerb.Less: 
            return table.TDBQCNUMLT
        if verb is filter.FilterVerb.Contains: 
            return table.TDBQCNUMEQ

    def _tag_to_uuid(self, tag):
        q = self.tags.query()
        q.addcond('name', table.TDBQCSTREQ, tag)
        tags = q.search()
        if len(tags) == 0:
            return None
        else:
            return tags[0]

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

    def list_messages(self, filterlist=[], sort=None, limit=None):
        q = self.table.query()
        for filter, verb, value in filterlist:
            if filter in ['flags', 'to', 'from', 'cc',
                    'bcc', 'subject']:
                q.addcond(filter, table.TDBQCSTRINC, value)
            elif filter in ['stored', 'size']:
                q.addcond(filter, self._verb_to_tcfilter(verb), str(value))
            elif filter in ['date']:
               d = time.mktime(utils.parsedate(value))
               q.addcond('date_int', self._verb_to_tcfilter(verb), str(d))
            elif filter in ['tag']:
                t = self._tag_to_uuid(value)
                if not t:
                    raise TagNotFound()
                q.addcond('tags', table.TDBQCSTRINC, t)
                    

        if sort is not None:
            sortfield, ascending = sort
            if sortfield in ['cc', 'from', 'subject', 'to']:
                q.setorder(sortfield, table.TDBQOSTRASC if ascending else table.TDBQOSTRDESC)
            elif sortfield in ['date']:
                q.setorder('date_int', table.TDBQONUMASC if ascending else table.TDBQONUMDESC)
            elif sortfield in ['size', 'stored']:
                q.setorder(sortfield, table.TDBQONUMASC if ascending else table.TDBQONUMDESC)

        if limit:
            q.setlimit(*limit)
        
               
        return q.search()

    def list_tags(self):
        q = self.tags.query()
        tags = q.search()
        tags = [self.tags[tag]['name'] for tag in tags]
        tags.sort()
        return tags or []

    def get_tag(self, tag):
        return self.tags[self._tag_to_uuid(tag)]

    def put_tag(self, tag):
        u = str(uuid.uuid4())
        self.tags[u] = {'count': '0', 'unread': '0', 'name': str(tag),
                        'created': '0', 'last-modified': '0'}

    def del_tag(self, tag):
        pass

    def updateTagCount(self, oldtags, newtags):
        for new in set(newtags).difference(set(oldtags)):
            t = self.tags[new]
            t['count'] = str((int(t['count']) + 1))
            self.tags[new] = t
        for removed in set(oldtags).difference(set(newtags)):
            t = self.tags[removed]
            t['count'] = str((int(t['count']) - 1))
            self.tags[removed] = t

    def get_message(self, uuid):
        msg = self.table[str(uuid)]
        print uuid
        taguids = msg['tags'].split(' ') 
        msg['tags'] = [self.tags[t]['name'] for t in taguids]
        msg['flags'] = msg['flags'].split(' ') 
        msg['size'] = int(msg['size'])
        msg['stored'] = int(msg['stored'])
        del msg['date_int']
        return msg

    def put_message_tags(self, uuid, newtags):
        msg = self.table[str(uuid)]
        taguids = []
        oldtaguids = self.table[str(uuid)]['tags'].split(' ') or []
        for tag in newtags:
            newtag = self._tag_to_uuid(tag)
            if not newtag:
                raise TagNotFound() 
            taguids += [newtag]
        self.updateTagCount(oltaguids, taguids)
        msg['tags'] = ' '.join([str(x) for x in taguids]) or ''
        self.table[str(uuid)] = msg

    def put_message_flags(self, uuid, flags):
        msg = self.table[str(uuid)]
        msg['flags'] = str(' '.join(flags)) or ''
        self.table[str(uuid)] = msg
    
    def put_message(self, uuid, msg):
        newmsg = msg
        taguids = []
        for tag in newmsg['tags']:
            newtag = self._tag_to_uuid(tag)
            if not newtag:
                raise TagNotFound() 
            taguids += [newtag]
        self.updateTagCount([], taguids)
        newmsg['tags'] = ' '.join([str(x) for x in taguids]) or ''
        newmsg['flags'] = str(' '.join(newmsg['flags'])) or ''
        newmsg['date_int'] = str(self._parse_date(msg['date']))
        newmsg['size'] = str(int(msg['size']))
        newmsg['stored'] = str(int(msg['stored']))
        self.table[str(uuid)] = newmsg

    def del_message(self, uuid):
        self.table.out(str(uuid))
