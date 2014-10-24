#ifndef INFOSTRUCT_H
#define INFOSTRUCT_H

typedef struct _infostruct
{
  int    type;
  int    width;
  int    height;
  int    myid;
  int    numprocs;
  double xmin;
  double xmax;
  double ymin;
  double ymax;
  int    maxiter;
} _infostruct;

typedef struct _pos_struct
{
  int    width;
  int    height;
  int    xpos;
  int    ypos;
} _pos_struct;

#endif
