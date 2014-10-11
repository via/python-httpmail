import boto
import boto.s3.connection
import json

class S3Storage:
  
    def __init__(self, account, host, accesskey, secretkey):
        self.conn = boto.connect_s3(accesskey, secretkey, host=host, port=443, is_secure=False,
            calling_format = boto.s3.connection.OrdinaryCallingFormat())
        self.bucket = self.conn.get_bucket(account)

    def list(self):
        return [str(x.name) for x in self.bucket.list()]

    def get_attrs(self, uuid):
        attrs = {}
        k = self.bucket.get_key(uuid)
        attrs['tags'] = json.loads(k.get_metadata('tags'))
        attrs['flags'] = json.loads(k.get_metadata('flags'))
        attrs['stored'] = int(k.get_metadata('stored'))
        return attrs

    def get_message(self, uuid):
        k = self.bucket.get_key(uuid)
        return k.get_contents_as_string()

    def put_message(self, uuid, msg, attrs):
        k = self.bucket.new_key(uuid)
        k.set_contents_from_string(msg)
        self.put_attrs(uuid, attrs)

    def put_attrs(self, uuid, attrs):
        k = self.bucket.get_key(uuid)
        newattrs = { 'tags': json.dumps(attrs['tags']),
                     'flags': json.dumps(attrs['flags']), 
                     'stored': str(attrs['stored']) }
        k = k.copy(k.bucket.name, k.name, newattrs)

    def del_message(self, uuid):
        self.bucket.delete_key(uuid)
