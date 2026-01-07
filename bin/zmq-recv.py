#!/usr/bin/env python3

import sys
import zmq

"""
zmq-recv.py: demo zmq receiver
2025-01-22, v1.0, ed <irc.rizon.net>, MIT-Licensed
https://github.com/9001/copyparty/blob/hovudstraum/bin/zmq-recv.py

basic zmq-server to receive events from copyparty; try one of
the below and then "send a message to serverlog" in the web-ui:

1) dumb fire-and-forget to any and all listeners;
run this script with "sub" and run copyparty with this:
  --xm zmq:pub:tcp://*:5556

2) one lucky listener gets the message, blocks if no listeners:
run this script with "pull" and run copyparty with this:
  --xm t3,zmq:push:tcp://*:5557

3) blocking syn/ack mode, client must ack each message;
run this script with "rep" and run copyparty with this:
  --xm t3,zmq:req:tcp://localhost:5555

note: to conditionally block uploads based on message contents,
use rep_server to answer with "return 1" and run copyparty with
  --xau t3,c,zmq:req:tcp://localhost:5555
"""


ctx = zmq.Context()


def sub_server():
    # PUB/SUB allows any number of servers/clients, and
    # messages are fire-and-forget
    sck = ctx.socket(zmq.SUB)
    sck.connect("tcp://localhost:5556")
    sck.setsockopt_string(zmq.SUBSCRIBE, "")
    while True:
        print("copyparty says %r" % (sck.recv_string(),))


def pull_server():
    # PUSH/PULL allows any number of servers/clients, and
    # each message is sent to a exactly one PULL client
    sck = ctx.socket(zmq.PULL)
    sck.connect("tcp://localhost:5557")
    while True:
        print("copyparty says %r" % (sck.recv_string(),))


def rep_server():
    # REP/REQ is a server/client pair where each message must be
    # acked by the other before another message can be sent, so
    # copyparty will do a blocking-wait for the ack
    sck = ctx.socket(zmq.REP)
    sck.bind("tcp://*:5555")
    while True:
        print("copyparty says %r" % (sck.recv_string(),))
        reply = b"thx"
        # reply = b"return 1"  # non-zero to block an upload
        # reply = b'{"rc":1}'  # or as json, that's fine too
        # reply = b'{"rejectmsg":"naw dude"}'  # or custom message
        sck.send(reply)


mode = sys.argv[1].lower() if len(sys.argv) > 1 else ""

if mode == "sub":
    sub_server()
elif mode == "pull":
    pull_server()
elif mode == "rep":
    rep_server()
else:
    print("specify mode as first argument:  SUB | PULL | REP")
