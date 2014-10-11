from swiftclient.client import Connection 
import json


class SwiftStorage(object):
    def __init__(self, account, url, user, key):
        self.conn = Connection(authurl=url, user=user, key=key)
        self.cont = self.conn.get_container(account)
        self.account = account

    def list(self):
        return [x["name"] for x in self.cont[1]]

    def get_attrs(self, uuid):
        attrs = {}
        k = self.conn.get_object(container=self.account, obj=uuid)[0]
        print k
        attrs['tags'] = json.loads(k['x-object-meta-tags'])
        attrs['flags'] = json.loads(k['x-object-meta-flags'])
        attrs['stored'] = int(k['x-object-meta-stored'])
        return attrs

    def get_message(self, uuid):
        return self.conn.get_object(container=self.account, obj=uuid)[1]

    def put_message(self, uuid, msg, attrs):
        self.conn.put_object(container=self.account, obj=uuid, contents=msg, headers=attrs)
        self.put_attrs(uuid, attrs)

    def put_attrs(self, uuid, attrs):
        newattrs = {'X-Object-Meta-Tags': json.dumps(attrs['tags']),
                    'X-Object-Meta-Flags': json.dumps(attrs['flags']),
                    'X-Object-Meta-Stored': str(attrs['stored'])}

        print newattrs
        self.conn.post_object(container=self.account, obj=uuid, headers=newattrs)

    def del_message(self, uuid):
        self.conn.delete_object(container=self.account, obj=uuid)

