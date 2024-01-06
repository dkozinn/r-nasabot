#!/usr/bin/bash
export PIP=pip
export SYSTEM=/etc/systemd/system
export BIN=/usr/local/bin
export LIB=$HOME/.local/lib/python-local/nasautils
export LOGDIR=/etc/logrotate.d
export SYSTEMCTL=systemctl
# Uncomment below for debug
# export PIP=echo
# export SYSTEM=/tmp/test
# export BIN=/tmp/bin
# export LIB=/tmp/lib
# export LOGDIR=/tmp/logdir
# export SYSTEMCTL=echo

# Next two save the local context so running as sudo can find them
export home=$HOME
export user=$USER
$PIP install --upgrade -r requirements.txt

./install-db.sh

mkdir -p $LIB
cp -r src/nasautils/*.py $LIB

for service in $(cat services)
do
    export service
    sudo -E bash -c "sed 's@USER@$user@;s@HOME@$home@' $service.service  > $SYSTEM/$service.service"
    [[ -f $service.timer ]] && sudo cp $service.timer $SYSTEM
    [[ -f $service.py ]] && sudo cp src/$service.py $BIN
done

sudo cp nasabot.logrotate $LOGDIR/nasabot

sudo $SYSTEMCTL daemon-reload
for service in $(cat services)
do
    [[ -f $service.timer ]] && service=$service.timer
    if [[ $service == *"@"* ]] ; then
        for subreddit in $(cat subreddits)
        do
            sudo $SYSTEMCTL enable $service.$subreddit
            sudo $SYSTEMCTL restart $service.$subreddit
        done
    else 
        sudo $SYSTEMCTL enable $service
        sudo $SYSTEMCTL restart $service
    fi
done

