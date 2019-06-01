#!/usr/bin/env python
# coding: utf-8
from __future__ import print_function

import io
import os
import sys
from glob import glob
from shutil import rmtree

setuptools_available = True
try:
    # need setuptools to build wheel
    from setuptools import setup, Command

except ImportError:
    # works in a pinch
    setuptools_available = False
    from distutils.core import setup, Command

from distutils.spawn import spawn

if "bdist_wheel" in sys.argv and not setuptools_available:
    print("cannot build wheel without setuptools")
    sys.exit(1)


def mglob(dirname, extensions):
    ret = []
    for ext in extensions:
        ret.extend(glob(dirname + "/*." + ext))
    return ret


NAME = "copyparty"
VERSION = None
data_files = [("share/doc/copyparty", ["README.rst", "README.md", "LICENSE"])]
manifest = ""
for dontcare, files in data_files:
    # print(dontcare)
    for fn in files:
        manifest += "include {0}\n".format(fn)

here = os.path.abspath(os.path.dirname(__file__))

with open(here + "/MANIFEST.in", "wb") as f:
    f.write(manifest.encode("utf-8"))


try:
    LONG_DESCRIPTION = ""
    LDCT = ""
    with open(here + "/README.rst", "rb") as f:
        txt = f.read().decode("utf-8")
        txt = txt[txt.find("`") :]
        LONG_DESCRIPTION = txt
        LDCT = "text/x-rst"
except:
    print("\n### could not open README.rst ###\n")
    with open(here + "/README.md", "rb") as f:
        txt = f.read().decode("utf-8")
        LONG_DESCRIPTION = txt
        LDCT = "text/markdown"


about = {}
if not VERSION:
    with open(os.path.join(here, NAME, "__version__.py"), "rb") as f:
        exec(f.read().decode("utf-8").split("\n\n", 1)[1], about)
else:
    about["__version__"] = VERSION


class clean2(Command):
    description = "Cleans the source tree"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        os.system("{0} setup.py clean --all".format(sys.executable))

        try:
            rmtree("./dist")
        except:
            pass

        try:
            rmtree("./copyparty.egg-info")
        except:
            pass

        nuke = []
        for (dirpath, dirnames, filenames) in os.walk("."):
            for fn in filenames:
                if (
                    fn.endswith(".rst")
                    or fn.endswith(".pyc")
                    or fn.endswith(".pyo")
                    or fn.endswith(".pyd")
                    or fn.startswith("MANIFEST")
                ):
                    nuke.append(dirpath + "/" + fn)

        for fn in nuke:
            os.unlink(fn)


class rstconv(Command):
    description = "Converts markdown to rst"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        self.proc_dir(".")
        self.proc_dir("docs")

    def proc_dir(self, path):
        import m2r

        for (dirpath, dirnames, filenames) in os.walk(path):

            dirnames.sort()
            for fn in sorted(filenames):

                fn = dirpath + "/" + fn
                if not fn.endswith(".md"):
                    continue

                rst_fn = fn[:-3] + ".rst"
                with open(fn, "rb") as f:
                    md = f.read().decode("utf-8")

                md = md.replace("* **[", "* [").replace(")** <-", ") <-")
                rst = m2r.convert(md)
                rst = rst.replace(":raw-html-m2r:`<del>", ":sub:`")
                rst = rst.replace("</del>`", "`")

                with open(rst_fn, "wb") as f:
                    f.write(rst.encode("utf-8"))


args = {
    "name": NAME,
    "version": about["__version__"],
    "description": "http file sharing hub",
    "long_description": LONG_DESCRIPTION,
    "long_description_content_type": LDCT,
    "author": "ed",
    "author_email": "copyparty@ocv.me",
    "url": "https://github.com/9001/copyparty",
    "license": "MIT",
    "data_files": data_files,
    "classifiers": [
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Environment :: Console",
        "Topic :: Communications :: Chat",
    ],
    "cmdclass": {"rstconv": rstconv, "clean2": clean2},
}


if setuptools_available:
    args.update(
        {
            "install_requires": [],
            "include_package_data": True,
            "packages": ["copyparty"],
            "entry_points": {
                "console_scripts": ["copyparty = copyparty.__main__:main"]
            },
        }
    )
else:
    args.update({"packages": ["copyparty"], "scripts": ["bin/copyparty"]})


# import pprint
# pprint.PrettyPrinter().pprint(args)
# sys.exit(0)

setup(**args)
