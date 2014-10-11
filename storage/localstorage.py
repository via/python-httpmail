import json
import xattr
import os

name='LocalStorage'

class LocalStorage(object):
    def __init__(self, config, user):
        self.basepath = os.path.join(config['basepath'], user)

    def list(self):
        pass    

    def get_attrs(self, uuid):
        pass

    def get_message(self, uuid):
        pass

    def put_message(self, uuid, msg, attrs):
        pass

    def put_attrs(self, uuid, attrs):
        pass

    def del_message(self, uuid):
        pass
  
    
