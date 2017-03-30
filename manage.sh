#!/bin/sh

set -e

if test -z "$PYTHON"
then
   PYTHON=python3.6
fi

dir=$(cd $(dirname $0); pwd)
pyvers=$($PYTHON <<EOF
import sys, platform
sys.stdout.write(("%s-%s.%s" % (
    (platform.python_implementation(),) +
     platform.python_version_tuple()[:2]
)).lower())
EOF
)
virtualenv_module=$($PYTHON <<EOF
import sys, platform
sys.stdout.write(
  'virtualenv'
  if platform.python_version_tuple()[:2] < ('3', '3')
  else 'venv'
)
EOF
)

os=$(uname -s | tr A-Z a-z)
env=/tmp/pyenv-$(basename $dir)-$os-$pyvers

if ! test -d "$env"
then
   $PYTHON -m $virtualenv_module $env
fi

. $env/bin/activate

pip install -qr $dir/requirements.txt

exec $dir/manage.py "$@"
