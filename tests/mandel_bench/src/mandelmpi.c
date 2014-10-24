/*
 * mandelmpi.c
 *
 */
#include <stdlib.h>
#include <stdio.h>
#include "infostruct.h"
#include <PaRatools.h>

#define USE_MPI
#ifdef USE_MPI
#include <mpi.h>
#endif

#include "mandelmpi.h"
#include "sion.h"

#define FREE(ptr, null) { if (ptr) { free(ptr); ptr = null; } }

/* master-worker communication flags */
#define STATE_MASTER -1
#define STATE_IDLE   0
#define STATE_WORK   1
#define TAG_WORK     27
#define TAG_DONE     28
#define TAG_FINISH   29

/*
 * Describe usage
 */
static void usage(char* name)
{
  fprintf(stderr, "Usage: %s options\n\nwith the following optional options (default values in parathesis):\n\n", name);

  fprintf(stderr, "  [-x <x0> <x1> <y0> <y1>]  coordinates of initial area (-1.5 0.5 -1.0 1.0)\n");
  fprintf(stderr, "  [-w <width>]              image width in pixels (256)\n");
  fprintf(stderr, "  [-h <height>]             image height in pixels (256)\n");
  fprintf(stderr, "  [-i <maxiter>]            max. number of iterations per pixel (256)\n");
  fprintf(stderr, "  [-b <blocksize>]          blocksize used for strides and blockmaster\n");
  fprintf(stderr, "  [-t <type>]               0=stride, 1=stripe, 2=blockmaster\n");
  fprintf(stderr, "  [-v]                      verbose (off)\n\n");
  exit(1);
}

int main(int argc, char *argv[])
{
  /* default values for command line parameters */
  double xmin        = -1.5; /* coordinates of rectangle */
  double xmax        =  0.5;
  double ymin        = -1.0;
  double ymax        =  1.0;
  int    width       = 256; /* size of rectangle in pixels */
  int    height      = 256;
  int    maxiter     = 256; /* max. number of iterations */
  int    verbose     = 0;   /* per default only print error messages */
  int    type        = 0;   /* type of calculation */
  int    blocksize   = 128;
  int    *iterations;

  int    numprocs, myid;
  int    i;
  double st, sta, runtime, calctime = 0.0, commtime = 0.0,
         waittime = 0.0, iotime = 0.0;

  int    lheight, starty;
  double lymin, lymax, dy;
  int    chunksize, sid;
  int    max_array_size;

  _infostruct infostruct;

  /* parse command line */
  i = 1;
  while (i < argc) {
    if (argv[i][0] == '-') {
      switch (argv[i][1])
      {
      case 'x':
        xmin = atof(argv[++i]);
        xmax = atof(argv[++i]);
        ymin = atof(argv[++i]);
        ymax = atof(argv[++i]);
        break;
      case 'i':
        maxiter = atoi(argv[++i]);
        break;
      case 'w':
        width = atoi(argv[++i]);
        break;
      case 'h':
        height = atoi(argv[++i]);
        break;
      case 't':
        type = atoi(argv[++i]);
        break;
      case 'b':
        blocksize = atoi(argv[++i]);
        break;
      case 'v':
        verbose++;
        break;
      default:
        fprintf(stderr, "%s\n", argv[i]);
        usage(argv[0]);
      }
    }
    else {
      fprintf(stderr, "%s\n", argv[i]);
      usage(argv[0]);
    }
    i++;
  }

  /* start MPI */
#ifdef USE_MPI
  MPI_Init(&argc, &argv);
  MPI_Comm_size(MPI_COMM_WORLD, &numprocs);
  MPI_Comm_rank(MPI_COMM_WORLD, &myid);
#else
  numprocs = 1;
  myid     = 0;
#endif

  /* fill infostruct */
  infostruct.type     = type;
  infostruct.width    = width;
  infostruct.height   = height;
  infostruct.myid     = myid;
  infostruct.numprocs = numprocs;
  infostruct.xmin     = xmin;
  infostruct.xmax     = xmax;
  infostruct.ymin     = ymin;
  infostruct.ymax     = ymax;
  infostruct.maxiter  = maxiter;

  /* start calculation */
  if (myid == 0) {
    if (verbose) {
      printf("start calculation (x=%8.5g ..%8.5g,y=%10.7g ..%10.7g)\n",
             xmin, xmax, ymin, ymax);
      fflush(stdout);
    }
  }

  sta = zam_esecond();

  /* IO preparation */
  switch(type) {
    case 0: max_array_size = width * blocksize; break;
    case 1: max_array_size = width * ((height/numprocs) +
                             ((height % numprocs > myid)? 1 : 0)); break;
    case 2: max_array_size = blocksize * blocksize; break;
  }
  chunksize = max_array_size * sizeof(int) + sizeof(_pos_struct);
  if (myid == 0) {
    if (type == 2) {
      chunksize = 0;
    }
    chunksize += sizeof(infostruct);
  }

  /* initialize array */
  iterations = calloc(max_array_size, sizeof(int));

#ifdef USE_MPI
  st = zam_esecond();
  MPI_Barrier(MPI_COMM_WORLD);
  waittime += (zam_esecond() - st);
#endif


  st = zam_esecond();

  /* open SION file*/
  sid = open_sion(chunksize, myid);

  /* write global file header */
  if (myid == 0) {
    sion_fwrite(&infostruct, sizeof(infostruct), 1, sid);
  }
  iotime += (zam_esecond() - st);

  /** Type 0 Stride **********************************************/
  if (type == 0) {
    lheight = blocksize;
    dy      = (ymax - ymin) / height;
    if (verbose) {
      printf("calc_stride[%02d]: %dx%d, chunksize= %d\n",
             myid, width, lheight, chunksize);
    }
    for (starty = myid*blocksize; starty < height; starty += numprocs*blocksize) {
      lymin = ymin + starty * dy;
      if (starty + lheight > height) {
        lheight = height - starty;
      }
      lymax = lymin + lheight * dy;
      calc(iterations, width, lheight, xmin, xmax, lymin, lymax,
          maxiter, &calctime);
      write_to_sion_file(sid,iterations,width,lheight,0,starty,&iotime);
    }
  }

  /** Type 1 Stripe **********************************************/
  if (type == 1) {
    /* Calculate stripes */
    starty  = myid * (height / numprocs) +
              ((height % numprocs > myid)? myid : height % numprocs) ;
    lheight = height / numprocs + ((height % numprocs > myid)? 1 : 0);
    dy      = (ymax - ymin) / height;
    lymin   = ymin + starty * dy;
    lymax   = lymin + lheight * dy;

    /* Calculation */
    if (verbose) {
      printf("calc_stripe[%02d]: %dx%d, chunksize= %d\n",
             myid, width, lheight, chunksize);
    }
    calc(iterations, width, lheight, xmin, xmax, lymin, lymax,
        maxiter, &calctime);
    write_to_sion_file(sid,iterations,width,lheight,0,starty,&iotime);
  }

  /** Type 2 Blockmaster *****************************************/
  if (type == 2) {
    if (numprocs > 1) {
#ifdef USE_MPI
      if (myid == 0) {
        if (verbose) {
          printf("calc_master[%02d]: %dx%d, chunksize= %d\n",
                 myid, width, height, chunksize);
        }
        calc_master(width, height, numprocs, blocksize, &calctime, &commtime);
      }
      else {
        if (verbose) {
          printf("calc_worker[%02d]: %dx%d, chunksize= %d\n",
                 myid, blocksize, blocksize, chunksize);
        }
        calc_worker(iterations, width, height,
                    xmin, xmax, ymin, ymax, maxiter, sid,
                    &iotime, &calctime, &commtime);
      }
#endif
    }
    else {
      fprintf(stderr, "ERROR: type 'blockmaster' needs at least two processes\n");
    }
  }

#ifdef USE_MPI
  st = zam_esecond();
  MPI_Barrier(MPI_COMM_WORLD);
  waittime += (zam_esecond() - st);
#endif

  /* close SION file */
  st = zam_esecond();
  close_sion(sid);
  iotime += (zam_esecond() - st);

  runtime = zam_esecond() - sta;

  if (verbose) {
    printf("PE %02d of %02d: t= %1d %d x %d bs= %d calc= %9.3f, wait= %9.3f, "
           "io= %9.3f, mpi= %9.3f, runtime= %9.3f (ms)\n",
           myid, numprocs, type, width, height, blocksize, calctime * 1000,
           waittime * 1000, iotime * 1000, commtime * 1000, runtime * 1000);
  }

#ifdef USE_MPI
  MPI_Finalize();
#endif

  FREE(iterations, NULL);

  return EXIT_SUCCESS;
}

#ifdef USE_MPI
/*
 * master task (type=2)
 */
void calc_master(int width, int height, int numprocs, int blocksize,
                 double *calctime, double *commtime)
{
  double     st, stc;
  int        ix, iy, i;
  int        lwidth, lheight;
  int        workeratwork = 0, numworkers = numprocs - 1;
  int        *workerstat;
  int        work[4];
  MPI_Status status;

  *commtime = 0.0;

  workerstat = malloc(numprocs * sizeof (int));

  workerstat[0] = STATE_MASTER;
  for (i = 1; i < numprocs; i++) {
    workerstat[i] = STATE_IDLE;
  }

  stc = zam_esecond();
  ix  = 0;
  iy  = 0;
  while ((iy < height) && (ix < width)) {

    /* calculate blocksize */
    lwidth = blocksize;
    lheight = blocksize;
    if (ix + lwidth > width) {
      lwidth = width - ix;
    }
    if (iy + lheight > height) {
      lheight = height - iy;
    }

    if (workeratwork < numworkers) {
      i = 0;
      while (workerstat[i] != STATE_IDLE) {
        i++;
      }
      /*  send work to worker #i */
      work[0] = ix;
      work[1] = iy;
      work[2] = lwidth;
      work[3] = lheight;
      st = zam_esecond();
      MPI_Send(work, 4, MPI_INT, i, TAG_WORK, MPI_COMM_WORLD);
      *commtime    += zam_esecond() - st;
      workerstat[i] = STATE_WORK;
      workeratwork++;

      /* calculate location of next block */
      ix += lwidth;
      if (ix >= width) {
        ix  = 0;
        iy += lheight;
      }
    }
    else {
      /*  collect result msg */
      st = zam_esecond();
      MPI_Recv(work, 4, MPI_INT, MPI_ANY_SOURCE, TAG_DONE, MPI_COMM_WORLD, &status);
      *commtime += zam_esecond() - st;
      workerstat[status.MPI_SOURCE] = STATE_IDLE;
      workeratwork--;
    }
  }
  /*  get rest of result msg */
  while (workeratwork > 0) {
    st = zam_esecond();
    MPI_Recv(work, 4, MPI_INT, MPI_ANY_SOURCE, TAG_DONE, MPI_COMM_WORLD, &status);
    *commtime += zam_esecond() - st;
    workerstat[status.MPI_SOURCE] = STATE_IDLE;
    workeratwork--;
  }

  /*  send finish message */
  for (i = 1; i < numprocs; i++) {
    work[0] = -1;
    work[1] = -1;
    work[2] = -1;
    work[3] = -1;
    st      = zam_esecond();
    MPI_Send(work, 4, MPI_INT, i, TAG_FINISH, MPI_COMM_WORLD);
    *commtime += zam_esecond() - st;
  }
  *calctime += zam_esecond() - stc - *commtime;

  FREE(workerstat, NULL);
}

/*
 * worker task (type=2)
 */
void calc_worker(int* iterations, int width, int height,
                 double xmin, double xmax, double ymin, double ymax,
                 int maxiter, int sid, double *iotime, double* calctime,
                 double* commtime)
{
  double     dx, dy, st;
  int        xpos, ypos, lwidth, lheight;
  double     lxmin,lxmax,lymin,lymax;
  int        work[4];
  MPI_Status status;

  dx = (xmax - xmin) / width;
  dy = (ymax - ymin) / height;

  while (1) {
    st = zam_esecond();
    /* recv new work from master */
    MPI_Recv(work, 4, MPI_INT, 0, MPI_ANY_TAG, MPI_COMM_WORLD, &status);
    *commtime += zam_esecond() - st;
    if (status.MPI_TAG == TAG_FINISH) {
      return;
    }

    xpos    = work[0];
    ypos    = work[1];
    lwidth  = work[2];
    lheight = work[3];

    lxmin = xmin + xpos * dx;
    lxmax = lxmin + lwidth * dx;
    lymin = ymin + ypos * dy;
    lymax = lymin + lheight * dy;

    calc(iterations, lwidth, lheight, lxmin, lxmax, lymin, lymax,
         maxiter, calctime);
    write_to_sion_file(sid, iterations, lwidth, lheight, xpos, ypos, iotime);

    st = zam_esecond();
    MPI_Send(work, 4, MPI_INT, 0, TAG_DONE, MPI_COMM_WORLD);
    *commtime += zam_esecond() - st;
  }
}
#endif

/*
 * Mandelbrot calculation
 */
void calc(int *iterations, int width, int height,
          double xmin, double xmax, double ymin, double ymax,
          int maxiter, double *calctime)
{
  double      dx, dy, x, y;
  int         ix, iy;
  double      st;

  st = zam_esecond();
  dx = (xmax - xmin) / width;
  dy = (ymax - ymin) / height;

  /* calculate value in the center of the pixel */
  y = ymin + 0.5 * dy;
  for (iy = 0; iy < height; ++iy) {
    x = xmin + 0.5 * dx;
    for (ix = 0; ix < width; ++ix) {
      double zx    = 0.0, zy = 0.0, zxnew;
      int    count = 0;
      while (zx * zx + zy * zy < 16 * 16 && count < maxiter) {
        zxnew = zx * zx - zy * zy + x;
        zy    = 2 * zx * zy     + y;
        zx    = zxnew;
        ++count;
      }
      iterations[iy * width + ix] = count;
      x                          += dx;
    }
    y += dy;
  }
  *calctime += zam_esecond() - st;
}

/*
 * write block to SION file
 */
void write_to_sion_file(int sid, int *iterations, int width, int height,
                        int xpos, int ypos, double *iotime)
{
  _pos_struct pos_struct;
  double      st;

  pos_struct.width  = width;
  pos_struct.height = height;
  pos_struct.xpos   = xpos;
  pos_struct.ypos   = ypos;

  st = zam_esecond();
  sion_fwrite(&pos_struct, sizeof(pos_struct), 1, sid);
  sion_fwrite(iterations, sizeof(int), width * height, sid);
  *iotime += zam_esecond() - st;
}

/*
 * open SION file
 */
int open_sion(int length, int rank)
{
  int        numFiles  = 1;
  int        fsblksize = -1;
  int        sid       = -1;
#ifdef USE_MPI
  char*      newfname  = NULL;
  sion_int64 chunksize = length;
  MPI_Comm   lComm;
#else
  int         ntasks   = 1;
  int         *ranks;
  sion_int64  *chunksizes;
#endif

#ifdef USE_MPI
  sid = sion_paropen_mpi("simple.sion",
                         "w",
                         &numFiles,
                         MPI_COMM_WORLD,
                         &lComm,
                         &chunksize,
                         &fsblksize,
                         &rank,
                         NULL,
                         &newfname);
#else
  ranks         = (int *) malloc(sizeof(int));
  ranks[0]      = 0;
  chunksizes    = (sion_int64 *) malloc(sizeof(sion_int64));
  chunksizes[0] = length;

  sid = sion_open("simple.sion",
                  "w",
                  &ntasks,
                  &numFiles,
                  &chunksizes,
                  &fsblksize,
                  &ranks,
                  NULL);

  FREE(ranks, NULL);
  FREE(chunksizes, NULL);
#endif

  return sid;
}

/*
 * close SION file
 */
void close_sion(int sid)
{
#ifdef USE_MPI
  sion_parclose_mpi(sid);
#else
  sion_close(sid);
#endif
}
