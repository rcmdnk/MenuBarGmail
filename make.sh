#!/usr/bin/env bash

env=$(mktemp -d)
python -m venv "$env"
source "$env"/bin/activate
pip install -r requirements.txt
cacerts=$(python -c "import site;print(site.getsitepackages()[0])")/httplib2/cacerts.txt
tmp_setup=$(mktemp)
cp setup.py "$tmp_setup"
certs.py
sed -i "" "s|cacerts.txt|$cacerts|" "$tmp_setup"
cat $tmp_setup
python "$tmp_setup" py2app
echo $cacerts
deactivate
rm -rf "$env"
rm -f "$tmp_setup"
