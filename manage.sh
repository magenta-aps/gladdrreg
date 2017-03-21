#!/bin/sh

set -e

dir=$(cd $(dirname $0); pwd)

os=$(uname -s | tr A-Z a-z)
env=$dir/pyenv-$os

if ! test -d $env
then
   python2.7 -m virtualenv $env
fi

. $env/bin/activate

pip install -qr $dir/requirements.txt

exec $dir/manage.py "$@"
