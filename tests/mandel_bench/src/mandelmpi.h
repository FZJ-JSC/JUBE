#ifndef MANDELMPI_H
#define MANDELMPI_H

void calc(int*         iterations,
          int          width,
          int          height,
          double       xmin,
          double       xmax,
          double       ymin,
          double       ymax,
          int          maxiter,
          double*      calctime);

void write_to_sion_file(int    sid,
                        int    *iterations,
                        int    width,
                        int    height,
                        int    xpos,
                        int    ypos,
                        double *iotime);

int open_sion(int length,
              int rank);

void close_sion(int sid);

#ifdef USE_MPI
void calc_master(int     width,
                 int     height,
                 int     numprocs,
                 int     blocksize,
                 double* calctime,
                 double* commtime);

void calc_worker(int*    iterations,
                 int     width,
                 int     height,
                 double  xmin,
                 double  xmax,
                 double  ymin,
                 double  ymax,
                 int     maxiter,
                 int     sid,
                 double* iotime,
                 double* calctime,
                 double* commtime);
#endif

#endif
