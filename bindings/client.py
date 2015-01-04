import requests

class Client():
    def __init__(self, uri):
        self.uri = uri

    def get_mailbox(self, mailbox):
        r = requests.get("{0}/mailboxes/{1}".format(self.uri, mailbox))
        return r.json()

    def get_mailbox_tags(self, mailbox):
        r = requests.get("{0}/mailboxes/{1}/tags/".format(self.uri, mailbox))
        return r.json()

    def get_mailbox_tag(self, mailbox, tag):
        r = requests.get("{0}/mailboxes/{1}/tags/{2}".format(self.uri, mailbox, tag))
        return r.json()

    def create_mailbox_tag(self, mailbox, tag):
        r = requests.put("{0}/mailboxes/{1}/tags/{2}".format(self.uri, mailbox, tag))
        return r.status_code

    def delete_mailbox_tag(self, mailbox, tag):
        r = requests.delete("{0}/mailboxes/{1}/tags/{2}".format(self.uri, mailbox, tag))
        return r.status_code

    def create_message(self, mailbox, message):
        pass

    def get_message_tags(self, mailbox, message):
        r = requests.get("{0}/mailboxes/{1}/messages/{2}/tags/".format(self.uri, mailbox, message))
        return r.json()

    def set_message_tag(self, mailbox, message, tag):
        r = requests.put("{0}/mailboxes/{1}/messages/{2}/tags/{3}".format(self.uri, mailbox, message, tag))
        return r.status_code

    def delete_message_tag(self, mailbox, message, tag):
        r = requests.delete("{0}/mailboxes/{1}/messages/{2}/tags/{3}".format(self.uri, mailbox, message, tag))
        return r.status_code

    def get_message_flags(self, mailbox, message):
        r = requests.get("{0}/mailboxes/{1}/messages/{2}/flags/".format(self.uri, mailbox, message))
        return r.json()

    def get_message_flag(self, mailbox, message, flag):
        r = requests.get("{0}/mailboxes/{1}/messages/{2}/flags/{3}".format(self.uri, mailbox, message, flag))
        return r.status_code == 200

    def set_message_flag(self, mailbox, message, flag):
        r = requests.put("{0}/mailboxes/{1}/messages/{2}/flags/{3}".format(self.uri, mailbox, message, flag))
        return r.status_code

    def delete_message_flag(self, mailbox, message, flag):
        r = requests.delete("{0}/mailboxes/{1}/messages/{2}/flags/{3}".format(self.uri, mailbox, message, flag))
        return r.status_code

    def get_raw_message(self, mailbox, message):
        r = requests.get("{0}/mailboxes/{1}/messages/{2}".format(self.uri, mailbox, message))
        return r.text

    def get_json_message(self, mailbox, message):
        pass

    def get_message_meta(self, mailbox, message):
        r = requests.get("{0}/mailboxes/{1}/messages/{2}/meta".format(self.uri, mailbox, message))
        return r.json()

    def delete_message(self, mailbox, message):
        r = requests.delete("{0}/mailboxes/{1}/messages/{2}".format(self.uri, mailbox, message))
        return r.status_code

    def list_messages(self, mailbox, filters=[], sortfield=None, descending=False, skip=0, limit=50):
        payload = {"filters": filters, "sort": {"field": sortfield, "reverse": descending}}
        params = {"skip": skip, "limit": limit}
        r = requests.get("{0}/mailboxes/{1}/messages/".format(self.uri, mailbox), data=payload, params=params)
        return r.json() 
