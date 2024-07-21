# coding: utf-8
from __future__ import print_function, unicode_literals

import argparse
import traceback

from queue import Queue

from .__init__ import TYPE_CHECKING
from .authsrv import AuthSrv
from .util import HMaccas, Pebkac

if True:  # pylint: disable=using-constant-test
    from typing import Any, Optional, Union

    from .util import RootLogger

if TYPE_CHECKING:
    from .httpsrv import HttpSrv


class ExceptionalQueue(Queue, object):
    def get(self, block: bool = True, timeout: Optional[float] = None) -> Any:
        rv = super(ExceptionalQueue, self).get(block, timeout)

        if isinstance(rv, list):
            if rv[0] == "exception":
                if rv[1] == "pebkac":
                    raise Pebkac(*rv[2:])
                else:
                    raise rv[2]

        return rv


class BrokerCli(object):
    """
    helps mypy understand httpsrv.broker but still fails a few levels deeper,
    for example resolving httpconn.* in httpcli -- see lines tagged #mypy404
    """

    log: "RootLogger"
    args: argparse.Namespace
    asrv: AuthSrv
    httpsrv: "HttpSrv"
    iphash: HMaccas

    def __init__(self) -> None:
        pass

    def ask(self, dest: str, *args: Any) -> ExceptionalQueue:
        return ExceptionalQueue(1)

    def say(self, dest: str, *args: Any) -> None:
        pass


def try_exec(want_retval: Union[bool, int], func: Any, *args: list[Any]) -> Any:
    try:
        return func(*args)

    except Pebkac as ex:
        if not want_retval:
            raise

        return ["exception", "pebkac", ex.code, str(ex)]

    except Exception as ex:
        if not want_retval:
            raise

        return ["exception", "stack", ex]
