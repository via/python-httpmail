import ConfigParser

class SiteConfig(object):

    def __init__(self, configfile):
        self.parser = ConfigParser.SafeConfigParser()
        self.parser.read(configfile)

        storage_backend = self.parser.get('storage', 'backend')
        self.storage_backend_config = {}
        for (key, val) in self.parser.items("storage:{0}".format(storage_backend)):
            self.storage_backend_config[key] = val
        storage_backend_module = __import__(storage_backend, locals(), globals(), ['name'])
        classname = storage_backend_module.name
        self.storage_backend = getattr(storage_backend_module, classname)

        index_backend = self.parser.get('index', 'backend')
        self.index_backend_config = {}
        for (key, val) in self.parser.items("index:{0}".format(index_backend)):
            self.index_backend_config[key] = val
        index_backend_module = __import__(index_backend, locals(), globals(), ['name'])
        classname = index_backend_module.name
        self.index_backend = getattr(index_backend_module, classname)

    def index(self, user, readonly=False):
        index = self.index_backend(self.index_backend_config, user, readonly)
        return index

    def storage(self, user):
        storage = self.storage_backend(self.storage_backend_config, user)
        return storage

    def api(self):
        for (key, val) in self.parser.items('api'):
            config[key] = val
        return config
