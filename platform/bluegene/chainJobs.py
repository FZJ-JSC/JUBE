#!/usr/bin/env python
from __future__ import print_function
import sys
import os
import re
import datetime 

maxSpaceDim = 15 # max No. of steps in one JUQUEEN job
defaultmaxWallclock=datetime.datetime.strptime("06:00:00","%H:%M:%S") # max Wallclock time for 1 step
smallmaxWallclock=datetime.datetime.strptime("00:30:00","%H:%M:%S") # max Wallclock time for 1 step (node <=64)
class Job:
    globalJobSpec = []
    def __init__(self,jubeStep,pwd):
        submitFile=os.path.join("..",jubeStep,"work","submit.job")
        try:
            f=open(submitFile,"r")
        except IOError:
            print('ERROR: unable to open submit script "{0}"'.format(submitFile), 
                  file=sys.stderr)  
            raise
        self.name=jubeStep
        self.pwd=pwd
        self._parseJobscript(f)
        f.close()

    def _parseJobscript(self,fptr):
        globalJobSpec=[]
        specificJobSpec=[]
        jobCommands=[]
        stdoutfile="stdout"
        errorfile="stderr"
        walltime="00:01:00"  
        for line in fptr:
            if re.findall(r"^#\s?@\s*(shell|job_name|notification|class|notify_user)",line):
                globalJobSpec.append(line)
            elif re.findall(r"^#\s?@\s*output\s*",line):
                stdoutfile=re.findall(r"^#\s?@\s*output\s*=\s*(\S+)\s*$",line)[0]
            elif re.findall(r"^#\s?@\s*error\s*",line):
                errorfile=re.findall(r"^#\s?@\s*error\s*=\s*(\S+)\s*$",line)[0]
            elif re.findall(r"^#\s?@\s*wall_clock_limit\s*",line):
                walltime=re.findall(r"^#\s?@\s*wall_clock_limit\s*=\s*(\S+)\s*$",line)[0]
            elif re.findall(r"^#+\s?@\s*",line):
                specificJobSpec.append(line)
            elif re.findall(r"^[ #\n\t\r\f]*$",line):
                continue
            else:
                jobCommands.append(line)
        self.__class__.globalJobSpec=globalJobSpec
        self.specificJobSpec=specificJobSpec
        self.jobCommands=jobCommands
        self.stdout=stdoutfile
        self.stderr=errorfile
        self.walltime=datetime.datetime.strptime(walltime,"%H:%M:%S")
        return 

def writeJobHead():
    return [ "#@ output = $(job_name).$(step_name).$(jobid)\n",
             "#@ error = $(output)\n",
             "#@ environment = COPY_ALL\n"
         ]

def initJobStep(step):
    return [ "#=== Step {0:d} directives ===\n".format(step),
             "#@ step_name = step_{0:d}\n".format(step),
             "#@ dependency = (step_{0:d} >= 0)\n".format(step-1) if step > 0 else ""
         ]
 
def writeJobCommands(job,cwd):
    stdout = os.path.join(job.pwd,job.stdout)
    stderr = os.path.join(job.pwd,job.stderr)
    output  = [ '(cd {0}\n'.format(job.pwd) ]
    output += job.jobCommands
    output += [ 'cd {0}\n'.format(cwd) ]
    output += [ ') > {0} 2> {1}\n'.format(stdout,stderr) ]
    return output
    

################################
#   MAIN
################################

filename = sys.argv[1]

f=open(filename,"r")
SystemParameterSpace={}
for line in f:
    lineArray=line.split(':')
    jubeStep = lineArray[0]
    jubeStepPWD = lineArray[3]
    SystemParameter=(lineArray[1],lineArray[2]) # nodes,topology
    if SystemParameter in SystemParameterSpace:
        SystemParameterSpace[SystemParameter].append(Job(jubeStep,jubeStepPWD))
    else:
        SystemParameterSpace[SystemParameter]=[Job(jubeStep,jubeStepPWD)]

# Abort if it is not possible to create the chained jobs
if len(SystemParameterSpace) > maxSpaceDim:
    print('ERROR: system specific parameter space to big', file=sys.stderr)  
    print('       allowed dimension: {0:3d}'.format(maxSpaceDim), file=sys.stderr)  
    print('       used dimension:    {0:3d}'.format(len(SystemParameterSpace)), file=sys.stderr)  
    for (index,parameter) in enumerate(SystemParameterSpace.keys()):
        print('       {0:d}. {1}'.format(index+1,str(parameter)), file=sys.stderr)
    exit(1)
f.close()
        
zeroTime=datetime.datetime.strptime("00:00:00","%H:%M:%S") 
commandlines=["case $LOADL_STEP_NAME in\n"]
cwd = os.environ['PWD']
step = 0
fptr = open("submit.job","w")
fptr.writelines(Job.globalJobSpec)
fptr.writelines(writeJobHead())
for SystemParameter in SystemParameterSpace.keys():
    substep=0
    maxWallclock = defaultmaxWallclock if int(SystemParameter[0])>64 else smallmaxWallclock
    stepWalltime=datetime.timedelta(0) # init with  0
    commandlines += ['step_{0:d}) echo "Working on $LOADL_STEP_NAME"\n'.format(step)]
    for job in SystemParameterSpace[SystemParameter]:
        if job.walltime  > maxWallclock:
            print('ERROR: wall_clock_limit "{0}" exceeded by one job specification - ABORTED'.format(job.walltime), 
                  file=sys.stderr)  
            exit(2)
        elif job.walltime + stepWalltime > maxWallclock:
            fptr.writelines(initJobStep(step))
            fptr.writelines(job.specificJobSpec)
            fptr.write("#@ wall_clock_limit    = {0}\n\n".format((zeroTime + stepWalltime).strftime("%H:%M:%S"))) 
            stepWalltime = job.walltime-zeroTime
            substep = 0
            step += 1
            commandlines += [';;\n\n','step_{0:d}) echo "Working on $LOADL_STEP_NAME"\n'.format(step)]
        else:
            substep += 1
            stepWalltime += job.walltime-zeroTime
        commandlines += writeJobCommands(job,cwd)
    commandlines += [';;\n\n'] 
    fptr.writelines(initJobStep(step))
    fptr.writelines(job.specificJobSpec)
    fptr.write("#@ wall_clock_limit    = {0}\n\n".format((zeroTime + stepWalltime).strftime("%H:%M:%S")))            
    step += 1
commandlines += ["esac\n"]
fptr.writelines(commandlines)
fptr.close()

if step-1 > maxSpaceDim:
    print('ERROR: cumulated wall_clock_limit to big', file=sys.stderr)  
    print('       => exceeded max step limitation: {0:3d}'.format(maxSpaceDim), file=sys.stderr)  
    exit(3)

exit(0)
