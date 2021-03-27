import os
import time
import tempfile


def errdesc(errors):
    report = ["copyparty failed to add the following files to the archive:", ""]

    for fn, err in errors:
        report.extend([" file: {}".format(fn), "error: {}".format(err), ""])

    with tempfile.NamedTemporaryFile(prefix="copyparty-", delete=False) as tf:
        tf_path = tf.name
        tf.write("\r\n".join(report).encode("utf-8", "replace"))

    os.chmod(tf_path, 0o444)
    return {
        "vp": "archive-errors-{}.txt".format(int(time.time())),
        "ap": tf_path,
        "st": os.stat(tf_path),
    }
