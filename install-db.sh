#!/bin/bash

DBDIR=$HOME/nasa
DBNAME=posts.db

if [[ ! -e $DBDIR/$DBNAME ]]; then
    mkdir -p $DBDIR
    sqlite3 $DBDIR/$DBNAME < posts.sql
fi