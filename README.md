
# API Documentation

### GET /mailboxes/`mailbox`/tags/

Returns a JSON list of tags for the mailbox.

### HEAD /mailboxes/`mailbox`/tags/`tag`/

The headers `X-Total-Count` and `X-Unread-Count` contain the number of total
messages in the directory and the number of unread messages with the
tag, respectively.

### PUT /mailboxes/`mailbox`/tags/`tag`

Create a new tag.

### DELETE /mailboxes/`mailbox`/tags/`tag`

Deletes the tag, and any messages that are associated only with the one
tag.

### POST /mailboxes/`mailbox`/messages/

Adds a new message to the directory.  The provided body should be of
content-type `message/rfc822`.  Returns the message UUID as the body.

### GET /mailboxes/`mailbox`/messages/

Returns a JSON list of all messages in the mailbox.  Result paging can
be used by specifying `limit` and `skip` in the query string,
representing how many messages to return and how far into the source
list the results should start from.

The parameters for filtering and sorting are provided in a JSON dictionary.
Message filters can be added in a json list under the "filters" element:
"filters": [{ "field": ...,
  "qualifier":  ...,
  "value": ...
}]

Field can be any of:
```
tag
flag
bcc
body
subject
text
to
from
cc
size 
date
stored
```

Each filter requires a qualifier, `>`, `<`, `=`, expressing
larger/later, smaller/earlier, and contains/equal, respectively

In addition, the `Header` field may be used to match arbitrary
message headers, specified by the additional attribute 'header' in the
JSON dictionary.

Message listings can be sorted using the `sort` key in the body:
"sort": {
  "field": ...,
  "reverse": ...
}

Valid sort fields, drawn from RFC5256:
```
arrival
cc
date
from
size
subject
to
```

Specifying "reverse" as true will provide the result listing in reverse
order.

Example:
```
{
  "filters": [
    { "field": "to",
      "qualifier": "=",
      "value": "v@shitler.net"
    },
    { "field": "size",
      "qualifier": "<",
      "value": 65535
    },
    { "field": "header",
      "header": "X-Spam-Check",
      "qualifier": "=",
      "value": "Yes"
    } ],
  "sort": {
    "field": "arrival",
    "reverse": True
  }
}
```

### GET /mailboxes/`mailbox`/messages/`id`/tags

Returns a json list of tags the message is associated with.

### PUT /mailboxes/`mailbox`/messages/`id`/tags/`tag`

Sets the given tag for the message;

### DELETE /mailboxes/`mailbox`/messages/`id`/tags/`tag`

Unsets the given tag for the message.

### GET /mailboxes/`mailbox`/messages/`id`

Fetches the message from storage. The result will be `message/rfc822`
data for the raw mail message.

### HEAD /mailboxes/`mailbox`/messages/`id`

Fetches the message headers from storage. The result will be `message/rfc822`
data for the headers section of the raw mail message.

### DELETE /mailboxes/`mailbox`/messages/`id`

Deletes the message from storage.

### GET /mailboxes/`mailbox`/messages/`id`/flags/

Gets all the flags associated with the message. These are the same flags
described by IMAP (`Seen`, `Answered`, `Flagged`, `Draft`, `Deleted`) and are
case-sensitive. The response is a JSON list of set flags.

### GET /mailboxes/`mailbox`/messages/`id`/flags/`flag`

Returns `200` status if the flag is set for the message, or `404` if the flag
is not set (or the flag was not recognized).

### PUT /mailboxes/`mailbox`/messages/`id`/flags/`flag`

Sets the given flag for the message.

### DELETE /mailboxes/`mailbox`/messages/`id`/flags/`flag`

Unsets the given flag for the message.

### GET /mailboxes/`mailbox`/messages/`id`/meta/

Gets all the meta information associated with the message. Currently, this will
return a JSON dictionary with two keys, `From` and `Subject`.

