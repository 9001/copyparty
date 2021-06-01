#!/bin/bash
set -ex

[ -e setup.py ] || ..
[ -e setup.py ] || {
    echo u wot
    exit 1
}

cd .git/hooks
rm -f pre-commit
ln -s ../../scripts/run-tests.sh pre-commit
