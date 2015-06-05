
# API Documentation

### GET /mailboxes/`mailbox`/folders/

Returns a JSON list of folders for the mailbox.

### HEAD /mailboxes/`mailbox`/folder/`folder`/

The headers `X-Total-Count` and `X-Unread-Count` contain the number of total
messages in the directory and the number of unread messages with the
folder, respectively.

### PUT /mailboxes/`mailbox`/folders/`folder`

Create a new folder.

### DELETE /mailboxes/`mailbox`/folder/`folder`

Deletes the folder, and any messages that are associated only with the one
folder.

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
folder
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
modified
imap_uid
pop3_uidl
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

### GET /mailboxes/`mailbox`/messages/`id`

Fetches the message from storage. The result will be `message/rfc822`
data for the raw mail message.

### GET /mailboxes/`mailbox`/messages/`id`/parts/`part`

Fetches `part` as identified in the bodystructure dictionary returned by /meta/,
given in the format described by IMAP RFC 3501.

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

Gets all the meta information associated with the message. This is a JSON dictionary containing the following keys:
```
to
from
subject
cc
bcc
date
folder
stored
modified
size
flags
bodystructure
imap_uid
pop3_uidl
```

The `bodystructure` field is a json list of dictionaries containing body part information.
```
{ 
  "type": "multipart",
  "subtype": "mixed",
  "parameters" : {
    "boundary": "_004_1433449118796123"
  },
  "language": "en-US",
  "part-url": "http://httpmail.matthewvia.info:5000/mailboxes/1234/messages/abcd/parts/1",
  "parts": [
    {
      "type": "text",
      "subtype": "plain",
      "parameters": {
        "charset": "iso-8859-1"
      },
      "id": "1234",
      "encoding": "quoted-printable",
      "size": 387,
      "part-url": "http://httpmail.matthewvia.info:5000/mailboxes/1234/messages/abcd/parts/1.1",
      "lines": 13
    }, 
    {
      "type": "application",
      "octet-stream",
      "parameters": {
        "name": "test.txt"
      },
      "description": "test.txt",
      "encoding": "base64",
      "size": 505498,
      "md5": "36df9540a5ef4996a9737657e4a8929c",
      "part-url": "http://httpmail.matthewvia.info:5000/mailboxes/1234/messages/abcd/parts/1.2",
      "disposition": {
        "type": "attachment",
        "parameters": {
          "filename": "test.txt",
          "size": "369402",
          "creation-date": "Thu, 04 Jun 2015 20:18:17 GMT"
        }
      }
    }
  ]
}
```
      
### PATCH /mailboxes/`mailbox`/messages/`id`/meta

Allows changing of message metadata.  Pass a body containing a json dictionary
containing any of the following keys:
```
folder
flags
imap_uid
pop3_uidl
```

### GET /mailboxes/`mailbox`/messages/`id`/annotations/

Returns a JSON list of existing annotations

### PUT /mailboxes/`mailbox`/messages/`id`/annotations/`annotation`

Pass a payload to store as an annotation

### DELETE /mailboxes/`mailbox`/messages/`id`/annotations/`annotation`

Deletes a given annotation

### GET /mailboxes/`mailbox`/messages/`id`/annotations/`annotation`

Fetches an annotation
