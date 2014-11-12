#!/usr/bin/env bash

if [ $# -lt 2 ]
then
    echo "$0: ERROR (MISSING ARGUMENTS)"
    exit 1
fi

LOCKFILE=$1
shift
COMMAND=$*


(
if  [ -f $LOCKFILE ]
then
    PRE_PID=`head -1 $LOCKFILE`
    while ps -p $PRE_PID
    do
	sleep 5
	PRE_PID=`head -1 $LOCKFILE`
    done
fi

$COMMAND&
echo $! > $LOCKFILE 
)&

exit 0


