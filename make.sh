#!/usr/bin/env bash

cacerts=$(python -c "import site;print(site.getsitepackages()[0])")/httplib2/cacerts.txt
tmp_setup=$(mktemp)
cp setup.py "$tmp_setup"
sed -i "" "s|cacerts.txt|$cacerts|" "$tmp_setup"
python "$tmp_setup" py2app
rm -f $tmp_setup

