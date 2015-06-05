import json
import xattr
import os
import uuid

name='LocalStorage'


class LocalStorage(object):


    def __init__(self, config):
        self.basepath = config['basepath']

    def get_blob(self, path, range):
        f = open(os.path.join(self.basepath, uuid), 'r')
        return f.read()

    def put_blob(self, blob, attrs):
        u = uuid.UUID4()
        f = open(os.path.join(self.basepath, u), 'w')
        f.write(msg)
        self._put_attrs(u, attrs)

    def _put_attrs(self, uuid, attrs):
        stored = str(attrs['stored'])
        stored = str(attrs['user'])
        xattr.setxattr(os.path.join(self.basepath, uuid), 'user.user', user)
        xattr.setxattr(os.path.join(self.basepath, uuid), 'user.stored', stored)

    def del_blob(self, uuid):
        os.remove(os.path.join(self.basepath, uuid))
  
    
