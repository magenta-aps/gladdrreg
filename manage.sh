#!/bin/sh

set -e

unset PYTHONPATH

if test -z "$PYTHON"
then
   PYTHON=python3.6
fi

dir=$(cd $(dirname $0); pwd)
env=$($PYTHON <<EOF
import sys, platform
sys.stdout.write(("$dir/pyenv-%s-%s-%s.%s" % (
    (platform.system(),
     platform.python_implementation()) +
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

if ! test -d "$env"
then
    $PYTHON -m $virtualenv_module $env
fi

. $env/bin/activate

pip install -qr $dir/requirements.txt

exec $dir/manage.py "$@"
