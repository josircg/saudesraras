#!/bin/bash

if [[ -z $1 ]]; then
  PYPATH='python'
else
  PYPATH=$1'/python'
fi

$PYPATH manage.py makemessages --all --no-location
# msgattrib locale/pt_BR/LC_MESSAGES/django.po --clear-fuzzy --clear-previous -o locale/pt_BR/LC_MESSAGES/django.po
$PYPATH utilities/clean.py
$PYPATH manage.py compilemessages
$PYPATH -m flake8