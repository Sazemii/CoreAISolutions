#!/bin/bash

rsync -av \
  --exclude='__pycache__' \
  --exclude='.git' \
  --exclude='*.sh' \
  --exclude='*.md' \
  /opt/docker/odoo19/ez_addons .
  /opt/docker/odoo19/ez_addons .

pyminify ez_addons/ --in-place --no-hoist-literal

find ez_addons/ -type d -exec chmod 777 {} +
rm -rf ez_addons/ez_payroll/demo

python3 -m python_minifier ez_addons/ --in-place --no-hoist-literal
