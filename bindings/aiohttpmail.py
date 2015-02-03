import asyncio
import aiohttp

class AIOHTTPMail():
    def __init__(self, uri):
        self.uri = uri

    @asyncio.coroutine
    def get_mailbox(self, mailbox):
        r = yield from aiohttp.request("get", "{0}/mailboxes/{1}".format(self.uri, mailbox))
        return (yield from r.json())

    @asyncio.coroutine
    def get_mailbox_tags(self, mailbox):
        r = yield from aiohttp.request("get", "{0}/mailboxes/{1}/tags/".format(self.uri, mailbox))
        return (yield from r.json())

    @asyncio.coroutine
    def get_mailbox_tag(self, mailbox, tag):
        r = yield from aiohttp.request("get", "{0}/mailboxes/{1}/tags/{2}".format(self.uri, mailbox, tag))
        return (yield from r.json())

    @asyncio.coroutine
    def create_mailbox_tag(self, mailbox, tag):
        r = yield from aiohttp.request("put", "{0}/mailboxes/{1}/tags/{2}".format(self.uri, mailbox, tag))
        status = yield from r.status
        return (status == 201)

    @asyncio.coroutine
    def delete_mailbox_tag(self, mailbox, tag):
        r = yield from aiohttp.request("delete", "{0}/mailboxes/{1}/tags/{2}".format(self.uri, mailbox, tag))
        status = yield from r.status
        return (status == 204)

    @asyncio.coroutine
    def create_message(self, mailbox, message):
        headers = {'Content-type': 'application/json'}
        r = yield from aiohttp.request("post", "{0}/mailboxes/".format(self.uri),
                                       headers=headers,
                                       data=message)
        status = yield from r.status
        if status != 200:
            return None
        return (yield from r.json())

    @asyncio.coroutine
    def get_message_tags(self, mailbox, message):
        r = yield from aiohttp.request("get", "{0}/mailboxes/{1}/messages/{2}/tags/".format(self.uri, mailbox, message))
        return (yield from r.json())

    @asyncio.coroutine
    def set_message_tag(self, mailbox, message, tag):
        r = yield from aiohttp.request("put", "{0}/mailboxes/{1}/messages/{2}/tags/{3}".format(self.uri, mailbox, message, tag))
        status = yield from r.status
        return (status == 200)

    @asyncio.coroutine
    def delete_message_tag(self, mailbox, message, tag):
        r = requests.delete("{0}/mailboxes/{1}/messages/{2}/tags/{3}".format(self.uri, mailbox, message, tag))
        status = yield from r.status
        return (status == 204)

    @asyncio.coroutine
    def get_message_flags(self, mailbox, message):
        r = yield from aiohttp.request("get", "{0}/mailboxes/{1}/messages/{2}/flags/".format(self.uri, mailbox, message))
        return (yield from r.json())

    @asyncio.coroutine
    def get_message_flag(self, mailbox, message, flag):
        r = yield from aiohttp.request("get", "{0}/mailboxes/{1}/messages/{2}/flags/{3}".format(self.uri, mailbox, message, flag))
        status = yield from r.status
        return (status == 200)

    @asyncio.coroutine
    def set_message_flag(self, mailbox, message, flag):
        r = yield from aiohttp.request("put", "{0}/mailboxes/{1}/messages/{2}/flags/{3}".format(self.uri, mailbox, message, flag))
        status = yield from r.status
        return (status == 200)

    @asyncio.coroutine
    def delete_message_flag(self, mailbox, message, flag):
        r = yield from aiohttp.request("delete", "{0}/mailboxes/{1}/messages/{2}/flags/{3}".format(self.uri, mailbox, message, flag))
        status = yield from r.status
        return (status == 200)

    @asyncio.coroutine
    def get_raw_message(self, mailbox, message):
        r = yield from aiohttp.request("get", "{0}/mailboxes/{1}/messages/{2}".format(self.uri, mailbox, message))
        return (yield from r.read())

    @asyncio.coroutine
    def get_json_message(self, mailbox, message):
        pass

    @asyncio.coroutine
    def get_message_meta(self, mailbox, message):
        r = yield from aiohttp.request("get", "{0}/mailboxes/{1}/messages/{2}/meta".format(self.uri, mailbox, message))
        return (yield from r.json())

    @asyncio.coroutine
    def delete_message(self, mailbox, message):
        r = yield from aiohttp.request("delete", "{0}/mailboxes/{1}/messages/{2}".format(self.uri, mailbox, message))
        status = yield from r.status
        return (status == 204)

    @asyncio.coroutine
    def list_messages(self, mailbox, filters=[], sortfield=None, descending=False, skip=0, limit=50):
        payload = {"filters": filters, "sort": {"field": sortfield, "reverse": descending}}
        params = {"skip": skip, "limit": limit}
        r = yield from aiohttp.request("get", "{0}/mailboxes/{1}/messages/".format(self.uri, mailbox), data=payload, params=params)
        return (yield from r.json())
