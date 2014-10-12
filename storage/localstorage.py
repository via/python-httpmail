import json
import xattr
import os

name='LocalStorage'


class LocalStorage(object):

    def _msgid_valid(self, msgid):
        return True

    def __init__(self, config, user):
        self.basepath = os.path.join(config['basepath'], user)

    def list(self):
        msgs = os.listdir(self.basepath)
        msgs = filter(self._msgid_valid, msgs)
        return msgs

    def get_attrs(self, uuid):
        attrs = {}
        tags = xattr.getxattr(os.path.join(self.basepath, uuid), 'user.tags')
        flags = xattr.getxattr(os.path.join(self.basepath, uuid), 'user.flags')
        stored = xattr.getxattr(os.path.join(self.basepath, uuid), 'user.stored')
        attrs['tags'] = json.loads(tags)
        attrs['flags'] = json.loads(flags)
        attrs['stored'] = int(stored)
        return attrs        

    def get_message(self, uuid):
        f = open(os.path.join(self.basepath, uuid), 'r')
        return f.read()

    def put_message(self, uuid, msg, attrs):
        f = open(os.path.join(self.basepath, uuid), 'w')
        f.write(msg)
        self.put_attrs(uuid, attrs)

    def put_attrs(self, uuid, attrs):
        tags = json.dumps(attrs['tags'])
        flags = json.dumps(attrs['flags'])
        stored = str(attrs['stored'])
        print os.path.join(self.basepath, uuid)
        print tags
        xattr.setxattr(os.path.join(self.basepath, uuid), 'user.tags', tags)
        xattr.setxattr(os.path.join(self.basepath, uuid), 'user.flags', flags)
        xattr.setxattr(os.path.join(self.basepath, uuid), 'user.stored', stored)

    def del_message(self, uuid):
        os.remove(os.path.join(self.basepath, uuid))
  
    
