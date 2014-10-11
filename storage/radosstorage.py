import rados
import json

class RadosStorage:
  
    def __init__(self, account, conffile='/etc/ceph/ceph.conf'):
        self.conn = rados.Rados(conffile=conffile)
        self.conn.connect()
        self.ioctx = self.conn.open_ioctx(account)

    def list(self):
        return [x.key for x in self.ioctx.list_objects()]

    def get_attrs(self, uuid):
        attrs = {}
        attrs['tags'] = json.loads(self.ioctx.get_xattr(uuid, 'tags'))
        attrs['flags'] = json.loads(self.ioctx.get_xattr(uuid, 'flags'))
        return attrs

    def get_message(self, uuid):
        return self.ioctx.read(uuid)

    def put_message(self, uuid, msg, attrs):
        self.ioctx.write_full(uuid, msg)
        self.put_attrs(uuid, attrs)

    def put_attrs(self, uuid, attrs):
        self.ioctx.set_xattr(uuid, 'tags', json.dumps(attrs['tags']))
        self.ioctx.set_xattr(uuid, 'flags', json.dumps(attrs['flags']))

