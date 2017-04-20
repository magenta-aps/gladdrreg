#!/bin/sh

set -e

cd $(dirname $0)

env=$(./manage.sh env)

./manage.sh makemessages --ignore pyenv-\*
./manage.sh babelcompilemessages --use-fuzzy --statistics -d i18n -D django
./manage.sh collectstatic --clear --no-input -v 0
