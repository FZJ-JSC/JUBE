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
    echo "sbatch --dependency=afterany:${DEPEND_JOBID} $SUBMITSCRIPT"
    JOBID=`sbatch --dependency=afterany:${DEPEND_JOBID} $SUBMITSCRIPT`
else
    echo "sbatch $SUBMITSCRIPT"
    JOBID=`sbatch $SUBMITSCRIPT`
fi

JUBE_ERR_CODE=$?
if [ $JUBE_ERR_CODE -ne 0 ]; then
    exit $JUBE_ERR_CODE
fi

echo "RETURN: $JOBID"
# the JOBID is the last field of the output line
echo ${JOBID##* } > $LOCKFILE

exit 0


