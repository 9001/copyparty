# coding: utf-8
from __future__ import print_function, unicode_literals

import os
import time
import tempfile
from datetime import datetime


def errdesc(errors):
    report = ["copyparty failed to add the following files to the archive:", ""]

    for fn, err in errors:
        report.extend([" file: {}".format(fn), "error: {}".format(err), ""])

    with tempfile.NamedTemporaryFile(prefix="copyparty-", delete=False) as tf:
        tf_path = tf.name
        tf.write("\r\n".join(report).encode("utf-8", "replace"))

    dt = datetime.utcfromtimestamp(time.time())
    dt = dt.strftime("%Y-%m%d-%H%M%S")

    os.chmod(tf_path, 0o444)
    return {
        "vp": "archive-errors-{}.txt".format(dt),
        "ap": tf_path,
        "st": os.stat(tf_path),
    }, report
