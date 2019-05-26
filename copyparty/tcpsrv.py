#!/usr/bin/env python
# coding: utf-8
from __future__ import print_function

import time
import socket
import threading
from datetime import datetime, timedelta
import calendar

from .msgsvc import *
from .mpsrv import *


class TcpSrv(object):
    """
    toplevel component starting everything else,
    tcplistener which forwards clients to httpsrv
    (through mpsrv if platform provides support)
    """

    def __init__(self, args):
        self.log_mutex = threading.Lock()
        self.msgsvc = MsgSvc(self.log)
        self.next_day = 0

        bind_ip = args.i
        bind_port = args.p

        ip = "127.0.0.1"
        if bind_ip != ip:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                s.connect(("10.255.255.255", 1))
                ip = s.getsockname()[0]
            except:
                pass
            s.close()

        self.log("root", "available @ http://{0}:{1}/".format(ip, bind_port))

        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((bind_ip, bind_port))
        srv.listen(100)

        self.log("root", "listening @ {0}:{1}".format(bind_ip, bind_port))

        if args.j == 0:
            self.log("root", "multiprocessing disabled")
            httpsrv = HttpSrv(args, self.log)
        else:
            httpsrv = MpSrv(args, self.log)

        while True:
            if httpsrv.num_clients() >= args.nc:
                time.sleep(0.1)
                continue

            sck, addr = srv.accept()
            httpsrv.accept(sck, addr)

    def log(self, src, msg):
        now = time.time()
        if now >= self.next_day:
            dt = datetime.utcfromtimestamp(now)
            print("\033[36m{}\033[0m".format(dt.strftime("%Y-%m-%d")))

            # unix timestamp of next 00:00:00 (leap-seconds safe)
            day_now = dt.day
            while dt.day == day_now:
                dt += timedelta(hours=12)

            dt = dt.replace(hour=0, minute=0, second=0)
            self.next_day = calendar.timegm(dt.utctimetuple())

        with self.log_mutex:
            ts = datetime.utcfromtimestamp(now).strftime("%H:%M:%S")
            print("\033[36m{} \033[33m{:21} \033[0m{}".format(ts, src, msg))
