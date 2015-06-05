from email import utils
import json
import filter
import os
import time
import uuid
from datetime import datetime
from dateutil.parser import parse

from hyperdex.client import Client, Contains, Equals, LessThan, GreaterThan, Regex, Document

name='HyperdexIndex'

class FolderNotFound(Exception):
    pass

class MessageNotFound(Exception):
    pass

class HyperdexIndex():
 
    """
    folder list format:
    "user": { "folders": set of folders,
              "created": date (timestamp),
              "modified": date (timestamp),
              "size": int,
              "folder_count": map (folder name -> message count),
              "folder_unread_count": map (folder name -> unread count),
              "folder_created": map (folder name -> created timestamp),
              "folder_modified": map (folder name -> modified timestamp)
            }
    
    message format:
    "uuid": { "folder": string)
              "flags": set([])
              "to": "to header",
              "from": "from header",
              "cc": "cc header",
              "bcc": "bcc header",
              "subject": subject header",
              "size": size int,
              "date": "date header",
              "intdate": date timestamp,
              "stored": stored timestamp,
              "last_modified": timestamp,
              "structure": json array of dicts representing body structure
              "imap_uid": imap uid int,
              "pop3_uidl": "pop3 uidl string",
              "annotations": arbitrary metadata
            }
    The index internally stores this as is, with the addition of a 
    'intdate' field containing timestamp version of the Date header
    for fast indexing.

    
    """

    def __init__(self, config):
        self.client = Client(config['host'], int(config['port']))
          
        self.folders = config['folder_space']
        self.messages = config['message_space']

    def _init_user(self, user):
        if not self.client.get(self.folders, user)
            self.client.put(self.folders, user, {'folders': set([]), 
                                                 'created': datetime.utcnow(),
                                                 'modified': datetime.utcnow()})

    def _parse_date(self, date):
        if date is None:
            dateint = datetime.utcnow()
        else:
            dtime = utils.parsedate_tz(date)
            if dtime is None:
                try:
                    dtime = parse(date)
                except:
                    dtime = datetime.now()
                dtime = dtime.timetuple()+ (0,)
            dateint = dtime
        return dateint

    def _update_size(self, user, delta):
        self.client.atomic_add(self.folders, user, {'size': delta})

    def _update_modified(self, user):
        self.client.put(self.folders, user, {'modified': datetime.utcnow()})

    def _update_folder_count(self, user, folder, delta):
        self.client.map_atomic_add(self.folders, user, {'folder_count': {str(folder): delta}})

    def _update_folder_unread_count(self, user, folder, delta):
        self.client.map_atomic_add(self.folders, user, {'folder_unread_count': {str(folder): delta}})

    def _update_message_modified(self, user, uuid):
        self.client.put(self.messages, uuid, {'last_modified': datetime.utcnow()})

    def _update_folder_modified(self, user, folder):
        self.client.map_add(self.folders, user, {'folder_modified': {str(folder): datetime.utcnow()}})

    def _number_compare(self, verb, number):
        if verb is filter.FilterVerb.Contains:
            return Equals(number)
        if verb is filter.FilterVerb.Less:
            return LessThan(number)
        if verb is filter.FilterVerb.Greater:
            return GreaterThan(number)

    def list_messages(self, user, filterlist=[], sort=None, limit=None):
        filters = {'user': user}
        
        for filter, verb, value in filterlist:
            if filter in ['to', 'from', 'cc',
                    'bcc', 'subject']:
                filters[filter] = Regex(str(value))
            elif filter in ['imap_uid', 'size']:
                filters[filter] = self._number_compare(verb, int(value))
            elif filter in ['date', 'stored', 'modified']:
                d = utils.parsedate(value)
                if filter == 'date':
                    filter = 'intdate'
                filters[filter] = self._number_compare(verb, d)
            elif filter in ['folder', 'pop3_uidl']:
                filters[filter] = Equals(str(value))
            elif filter in ['flag']:
                filters['flags'] = Contains(str(value))
                
        if sort is None or sort[0] is None:
            sortfield = 'uuid'
        elif sort[0] == 'date':
            sortfield = 'intdate'
        else:
            sortfield = str(sort[0])
        
        if not sort or sort[1] is True:
            sortdir = 'maximize'
        else:
            sortdir = 'minimize'

        if limit is None:
            limit = (5000000, 0)
 
        res = self.client.sorted_search(self.messages, filters, sortfield, limit[0] + limit[1], sortdir)
        return res[0:len(res) - limit[1]][::-1]

    def list_folders(self, user):
        self._init_user(user)
        folder = self.client.get(self.folders, user)['folders']
        return list(folders) or []

    def get_folder(self, user, folder):
        if not folder in self.list_folders(user):
            return None
        folderdata = self.client.get(self.folders, user)
        r = {"count": folderdata['folder_count'][folder],
             "unread": folderdata['folder_unread_count'][folder],
             "created": folderdata['folder_created'][folder],
             "last-modified": folderdata['folder_modified'][folder]}
        return r

    def put_folder(self, user, folder):
        if not self.client.get(self.folders, user):
           self._init_user(user)
        if folder in self.list_folders(user):
            return
        self.client.set_add(self.folders, user, {'folders': str(folder)})
        self.client.map_add(self.folders, user, {'folder_unread_count': {str(folder): 0}})
        self.client.map_add(self.folders, user, {'folder_count': {str(folder): 0}})
        self.client.map_add(self.folders, user, {'folder_created': {str(folder): datetime.utcnow()}})
        self.client.map_add(self.folders, user, {'folder_modified': {str(folder): datetime.utcnow()}})

    def del_folder(self, user, folder):
        pass

    def get_message(self, user, uuid):
        msg = self.client.get(self.messages, uuid)
        del msg['intdate']
        msg['flags'] = list(msg['flags'])
        return msg

    def put_message_folder(self, user, uuid, folder):
        uuid = str(uuid)
        folders = self.client.get(self.folders, self.user)['folders']
        oldfolder = self.client.get(self.messages, uuid)['folder']
        flags = self.client.get(self.messages, uuid)['flags']
        if folder not in folders:
            raise FolderNotFound()
        self._update_folder_modified(user, oldfolder)
        self._update_folder_count(user, oldfolder, -1)
        if "\\Seen" not in flags:
            self._update_folder_unread_count(user, oldfolder, -1)
        self._update_folder_count(user, folder, 1)
        self._update_folder_modified(user, folder)
        if "\\Seen" not in flags:
            self._update_folder_unread_count(user, folder, 1)
        self.client.put(self.messages, str(uuid), {'folder': folder)
        self._update_message_modified(user, uuid)

    def put_message_flags(self, user, uuid, flags):
        uuid = str(uuid)
        oldflags = self.client.get(self.messages, uuid)['flags']
        folder = self.client.get(self.folders, user)['folder']
        self.client.put(self.messages, str(uuid), {'flags': set([str(x) for x in flags])})
        if "\\Seen" in oldflags and "\\Seen" not in flags:
            self._update_folder_unread_count(user, folder, 1)
        if "\\Seen" not in oldflags and "\\Seen" in flags:
            self._update_folder_unread_count(user, folder, -1)
        self._update_folder_modified(user, folder)        
        self._update_message_modified(user, uuid)

    def _encode_strings(self, msg):
        for field in ['to', 'from', 'cc', 'bcc', 'subject', 'date', 'folder', 
                      'pop3_uidl']:
            msg[field] = msg[field].decode('iso-8859-1').encode('utf-8')
        msg['flags'] = [x.decode('iso-8859-1').encode('utf-8') for x in msg['flags']]
        return msg
    
    def put_message(self, user, uuid, msg):
        self._init_user()
        msg = self._encode_strings(msg)
        msg['flags'] = set(msg['flags'])
        msg['intdate'] = self._parse_date(msg['date'])
        msg['user'] = user
        msg['bodystructure'] = Document(msg['bodystructure'])
        msg['annotations'] = Document(msg['annotations'])
        folder = msg['folder']
        self.client.put(self.messages, uuid, msg)
        self._update_size(user, msg['size'])
        self._update_folder_modified(user, folder)        
        self._update_folder_count(user, folder, 1)
        if '\\Seen' not in msg['flags']:
            self._update_folder_unread_count(user, folder, 1)
        self._update_modified(user)
        self._update_message_modified(user, uuid)
         

    def del_message(self, user, uuid):
        msg = self.get_message(user, uuid)
        self.client.delete(self.messages, uuid)
        self._update_size(user, -msg['size'])
        self._update_folder_modified(user, msg['folder'])        
        self._update_folder(user, msg['folder'], -1)
        if '\\Seen' in msg['flags']:
            self._update_folder_unread_count(user, msg['folder'], -1)
        self._update_modified(user)

    def get_user(self, user):
        self._init_user(user)
        row = self.client.get(self.folders, user)
        count = sum(row['row_count'].values())
        u = {"user": user,
             "created": row['created'],
             "modified": row['modified'],
             "size": row['size'],
             "count": count
            }
        return u
