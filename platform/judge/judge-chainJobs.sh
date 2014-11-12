#!/usr/bin/env bash

if [ $# -lt 2 ]
then
    echo "$0: ERROR (MISSING ARGUMENTS)"
    exit 1
fi

LOCKFILE=$1
shift
SUBMITSCRIPT=$*


if  [ -f $LOCKFILE ]
then
    DEPEND_JOBID=`head -1 $LOCKFILE`
    JOBID=`qsub -W depend=afterany:${DEPEND_JOBID} $SUBMITSCRIPT`
else
    JOBID=`qsub $SUBMITSCRIPT`
fi

echo ${JOBID} > $LOCKFILE

exit 0


