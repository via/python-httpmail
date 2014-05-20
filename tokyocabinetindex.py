from tokyocabinet import table, btree
from dateutil.parser import parse
import json
import filter
import time
import uuid

class TokyoCabinetIndex():
 
    """
    tag list format:
    "tagname": { "count": 0,
                 "unread": 0}
    
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

    def __init__(self, path):
        self.table = table.Table()
        self.table.open(path, table.TDBOWRITER | table.TDBOCREAT)

        self.tags = table.Table()
        self.tags.open("{0}-tags".format(path), table.TDBOWRITER | table.TDBOCREAT)

    def _verb_to_tcfilter(self, verb):
        if verb is filter.FilterVerb.Greater: 
            return table.TDBQCNUMGT 
        if verb is filter.FilterVerb.Less: 
            return table.TDBQCNUMLT
        if verb is filter.FilterVerb.Contains: 
            return table.TDBQCNUMEQ

    def list_messages(self, filterlist=[], sortlist=[], limit=None):
        q = self.table.query()
        for filter, verb, value in filterlist:
            if filter in ['flags', 'to', 'from', 'cc',
                    'bcc', 'subject']:
                q.addcond(filter, table.TDBQCSTRINC, value)
            elif filter in ['stored', 'size']:
                q.addcond(filter, self._verb_to_tcfilter(verb), str(value))
            elif filter in ['date']:
               d = time.mktime(parse(value).timetuple())
               q.addcond('date_int', self._verb_to_tcfilter(verb), str(d))
            elif filter in ['tags']:
                q.addcond(filter, table.TDBQCSTRINC, 
                    "\"{0}\"".format(value))

        if len(sortlist) > 1:
            raise ValueError("More than one sort not supported")
        for sort, ascending in sortlist:
            if sort in ['cc', 'from', 'subject', 'to']:
                q.setorder(sort, table.TDBQOSTRASC if ascending else table.TDBQOSTRDESC)
            elif sort in ['date']:
                q.setorder('date_int', table.TDBQONUMASC if ascending else table.TDBQONUMDESC)
            elif sort in ['size', 'stored']:
                q.setorder(sort, table.TDBQONUMASC if ascending else table.TDBQONUMDESC)

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
        q = self.tags.query()
        q.addcond('name', table.TDBQCSTREQ, tag)
        tags = q.search()
        return tags[0]

    def put_tag(self, tag):
        u = str(uuid.uuid4())
        self.tags[u] = {'count': '0', 'unread': '0', 'name': str(tag)}

    def del_tag(self, tag):
        pass

    def get_message(self, uuid):
        msg = self.table[uuid]
        taguids = msg['tags'].split(' ')
        msg['tags'] = [self.tags[t]['name'] for t in taguids]
        msg['flags'] = msg['flags'].split(' ')
        msg['size'] = int(msg['size'])
        msg['stored'] = int(msg['stored'])
        del msg['date_int']
        return msg
    
    def put_message(self, uuid, msg):
        newmsg = msg
        taguids = []
        for tag in newmsg['tags']:
            q = self.tags.query()
            q.addcond('name', table.TDBQCSTREQ, tag)
            taguids += q.search()
        newmsg['tags'] = ' '.join([str(x) for x in taguids])
        newmsg['flags'] = str(' '.join(newmsg['flags']))
        newmsg['date_int'] = str(int(time.mktime(parse(msg['date'], fuzzy=True).timetuple())))
        msg['size'] = str(int(msg['size']))
        msg['stored'] = str(int(msg['stored']))
        self.table[uuid] = newmsg

    def del_message(self, uuid):
        self.table.out(uuid)