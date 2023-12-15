#!/usr/bin/bash
SYSTEM=/etc/systemd/system
#SYSTEM=/tmp
BIN=/usr/local/bin
#BIN=/tmp/bin
LIB=$HOME/.local/lib/python-local
#LIB=/tmp/lib
SYSTEMCTL=systemctl
#SYSTEMCTL=echo
LOGDIR=/etc/logrotate.d
#LOGDIR=/tmp/logdir

pip install --upgrade -r requirements.txt

./install-db.sh

for utility in $(cat utilities)
do
    cp src/nasautils/$utility $LIB
done

for service in $(cat services)
do
    sed "s@USER@$USER@;s@HOME@$HOME@" $service.service  > $SYSTEM/$service.service
    [[ -f "$1".timer ]] && cp "$1".timer $SYSTEM
    cp src/$service.py $BIN
done

cp nasabot.logrotate $LOGDIR

$SYSTEMCTL daemon-reload
for service in $(cat services)
do
    $SYSTEMCTL enable $service
    $SYSTEMCTL restart $service
done

