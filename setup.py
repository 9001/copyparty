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
    from setuptools import setup, Command, find_packages

except ImportError:
    # works in a pinch
    setuptools_available = False
    from distutils.core import setup, Command

from distutils.spawn import spawn

if "bdist_wheel" in sys.argv and not setuptools_available:
    print("cannot build wheel without setuptools")
    sys.exit(1)


NAME = "copyparty"
VERSION = None
data_files = [("share/doc/copyparty", ["README.md", "LICENSE"])]
manifest = ""
for dontcare, files in data_files:
    for fn in files:
        manifest += "include {0}\n".format(fn)

manifest += "recursive-include copyparty/res *\n"
manifest += "recursive-include copyparty/web *\n"

here = os.path.abspath(os.path.dirname(__file__))

with open(here + "/MANIFEST.in", "wb") as f:
    f.write(manifest.encode("utf-8"))

with open(here + "/README.md", "rb") as f:
    txt = f.read().decode("utf-8")
    long_description = txt


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
                    fn.startswith("MANIFEST")
                    or fn.endswith(".pyc")
                    or fn.endswith(".pyo")
                    or fn.endswith(".pyd")
                ):
                    nuke.append(dirpath + "/" + fn)

        for fn in nuke:
            os.unlink(fn)


args = {
    "name": NAME,
    "version": about["__version__"],
    "description": "http file sharing hub",
    "long_description": long_description,
    "long_description_content_type": "text/markdown",
    "author": "ed",
    "author_email": "copyparty@ocv.me",
    "url": "https://github.com/9001/copyparty",
    "license": "MIT",
    "data_files": data_files,
    "classifiers": [
        "Development Status :: 3 - Alpha",
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
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Environment :: Console",
        "Environment :: No Input/Output (Daemon)",
        "Topic :: Communications :: File Sharing",
    ],
    "cmdclass": {"clean2": clean2},
}


if setuptools_available:
    args.update(
        {
            "packages": find_packages(),
            "install_requires": ["jinja2"],
            "extras_require": {"thumbnails": ["Pillow"]},
            "include_package_data": True,
            "entry_points": {
                "console_scripts": ["copyparty = copyparty.__main__:main"]
            },
            "scripts": ["bin/copyparty-fuse.py"],
        }
    )
else:
    args.update(
        {
            "packages": ["copyparty", "copyparty.stolen"],
            "scripts": ["bin/copyparty-fuse.py"],
        }
    )


# import pprint
# pprint.PrettyPrinter().pprint(args)
# sys.exit(0)

setup(**args)
