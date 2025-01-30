# ABTEIM is a python-based Uptime telegram bot

How to install:

mkvirtualenv abteim

mkdir ~/.abteim
# place the modified config file from abteim/data her

pip install --upgrade --extra-index-url http://etec.iv.at:8123 --trusted-host etec.iv.at abteim
# edit ~/.config/systemd/user/abteim.service according to the modified service file in abteim/data
systemctl --user daemon-reload
systemctl --user enable --now abteim

