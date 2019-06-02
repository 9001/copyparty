#!/usr/bin/env python
# coding: utf-8
from __future__ import print_function

import time
import socket
import threading
from datetime import datetime, timedelta
import calendar

from .__init__ import *


class TcpSrv(object):
    """
    toplevel component starting everything else,
    tcplistener which forwards clients to httpsrv
    (through mpsrv if platform provides support)
    """

    def __init__(self, args):
        self.args = args

        self.log_mutex = threading.Lock()
        self.next_day = 0

        ip = "127.0.0.1"
        if self.args.i != ip:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                s.connect(("10.255.255.255", 1))
                ip = s.getsockname()[0]
            except:
                pass
            s.close()

        self.log("root", "available @ http://{0}:{1}/".format(ip, self.args.p))

        self.srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.srv.bind((self.args.i, self.args.p))
        except OSError as ex:
            if ex.errno != 98:
                raise

            raise Exception(
                "\033[1;31mport {} is busy on interface {}\033[0m".format(
                    self.args.p, self.args.i
                )
            )

    def run(self):
        self.srv.listen(self.args.nc)

        self.log("root", "listening @ {0}:{1}".format(self.args.i, self.args.p))

        self.httpsrv = self.create_server()
        while True:
            if self.httpsrv.num_clients() >= self.args.nc:
                time.sleep(0.1)
                continue

            sck, addr = self.srv.accept()
            self.httpsrv.accept(sck, addr)

    def shutdown(self):
        self.httpsrv.shutdown()

    def check_mp_support(self):
        vmin = sys.version_info[1]
        if WINDOWS:
            if PY2:
                # py2 pickler doesn't support winsock
                return False
            elif vmin < 3:
                return False
        else:
            if not PY2 and vmin < 3:
                return False

        return True

    def create_server(self):
        if self.args.j == 0:
            self.log("root", "multiprocessing disabled by argument -j 0;")
            return self.create_threading_server()

        if not self.check_mp_support():
            if WINDOWS:
                self.log("root", "need python 3.3 or newer for multiprocessing;")
            else:
                self.log("root", "need python 2.7 or 3.3+ for multiprocessing;")

            return self.create_threading_server()

        return self.create_multiprocessing_server()

    def create_threading_server(self):
        from .httpsrv import HttpSrv

        self.log("root", "cannot efficiently use multiple CPU cores")
        return HttpSrv(self.args, self.log)

    def create_multiprocessing_server(self):
        from .mpsrv import MpSrv

        return MpSrv(self.args, self.log)

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
