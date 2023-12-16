#!/usr/bin/bash
export SYSTEM=/etc/systemd/system
#export SYSTEM=/tmp/test
export BIN=/usr/local/bin
#export BIN=/tmp/bin
export LIB=$HOME/.local/lib/python-local
#export LIB=/tmp/lib
export SYSTEMCTL=systemctl
#export SYSTEMCTL=echo
export LOGDIR=/etc/logrotate.d
#export LOGDIR=/tmp/logdir

# Next two save the local context so running as sudo can find them
export home=$HOME
export user=$USER
pip install --upgrade -r requirements.txt

./install-db.sh

for utility in $(cat utilities)
do
    cp src/nasautils/$utility $LIB
done

for service in $(cat services)
do
    export service
    sudo -E bash -c "sed 's@USER@$user@;s@HOME@$user@' $service.service  > $SYSTEM/$service.service"
    sudo -E bash -c "[[ -f $service.timer ]] && cp $service.timer $SYSTEM"
    sudo -E cp src/$service.py $BIN
done

cp nasabot.logrotate $LOGDIR

sudo $SYSTEMCTL daemon-reload
for service in $(cat services)
do
    sudo $SYSTEMCTL enable $service
    sudo $SYSTEMCTL restart $service
done

