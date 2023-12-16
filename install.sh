#!/usr/bin/bash
export SYSTEM=/etc/systemd/system
#export SYSTEM=/tmp/test
export BIN=/usr/local/bin
#export BIN=/tmp/bin
export LIB=$HOME/.local/lib/python-local/nasautils
#export LIB=/tmp/lib
export LOGDIR=/etc/logrotate.d
#export LOGDIR=/tmp/logdir
export SYSTEMCTL=systemctl
#export SYSTEMCTL=echo

# Next two save the local context so running as sudo can find them
export home=$HOME
export user=$USER
pip install --upgrade -r requirements.txt

./install-db.sh

mkdir -p $LIB
cp -r src/nasautils/*.py $LIB

for service in $(cat services)
do
    export service
    sudo -E bash -c "sed 's@USER@$user@;s@HOME@$user@' $service.service  > $SYSTEM/$service.service"
    [[ -f $service.timer ]] && sudo cp $service.timer $SYSTEM
    sudo cp src/$service.py $BIN
done

sudo cp nasabot.logrotate $LOGDIR

sudo $SYSTEMCTL daemon-reload
for service in $(cat services)
do
    [[ -f $service.timer ]] && service = $service.timer
    sudo $SYSTEMCTL enable $service
    sudo $SYSTEMCTL restart $service
done

