#!/usr/bin/env bash

rm -rf build/ dist/
env=$(mktemp -d)
python -m venv "$env"
source "$env"/bin/activate
pip install -r requirements.txt
cacerts=$(python -c "import site;print(site.getsitepackages()[0])")/httplib2/cacerts.txt
tmp_setup=$(mktemp)
cp setup.py "$tmp_setup"
sed -i "" "s|cacerts.txt|$cacerts|" "$tmp_setup"
python "$tmp_setup" py2app
deactivate
rm -rf "$env"
rm -f "$tmp_setup"
