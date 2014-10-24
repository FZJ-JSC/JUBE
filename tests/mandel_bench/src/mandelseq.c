/*
 * mandelseq.c
 *
 */
#include <stdlib.h>
#include <stdio.h>
#include "ppmwrite.h"
#include "infostruct.h"
#include "sion.h"

void collect(int         **iterations,
             int         **proc_distribution,
             _infostruct *info_glob);

int main(int argc, char* argv[])
{
  int         *iterations = NULL;
  int         *proc_distribution = NULL;
  _infostruct info_glob;

  /* init ppm */
  ppminitsmooth(1);

  /* read SION file */
  collect(&iterations, &proc_distribution, &info_glob);

  /* create ppm files */
  ppmwrite(iterations, info_glob.width, info_glob.height, 0,
           info_glob.maxiter, "mandelcol.ppm");
  ppmwrite(proc_distribution, info_glob.width, info_glob.height, 0,
           info_glob.numprocs, "mandelcol_procs.ppm");

  free(iterations);
  free(proc_distribution);

  return EXIT_SUCCESS;
}

/*
 * Print infostruct data
 */
void print_infostruct(const _infostruct* info)
{
  printf("type     = %d\n", info->type);
  printf("width    = %d\n", info->width);
  printf("height   = %d\n", info->height);
  printf("myid     = %d\n", info->myid);
  printf("numprocs = %d\n", info->numprocs);
  printf("xmin     = %g\n", info->xmin);
  printf("xmax     = %g\n", info->xmax);
  printf("ymin     = %g\n", info->ymin);
  printf("ymax     = %g\n", info->ymax);
  printf("maxiter  = %d\n", info->maxiter);
}

/*
 * Read SION file and store data in iterations array.
 * Processor distribution will be stored inside proc_distribution array.
 * info_glob will contain the global infostruct.
 */
void collect(int **iterations, int **proc_distribution, _infostruct *info_glob)
{
  sion_int32  fsblksize   = -1;
  sion_int64 *chunksizes  = NULL;

  int        *globalranks = NULL;
  int         ntasks      = 1;
  int         nfiles      = 1;
  int         outsid      = -1;
  FILE       *outfp       = NULL;

  int        *buffer = NULL;
  _pos_struct info;
  int         task   = 0;
  int         i      = 0;
  int         size   = -1;
  int         xpos,ypos;

  /* open SION file */
  outsid = sion_open("simple.sion", "r", &ntasks, &nfiles, &chunksizes,
                     &fsblksize, &globalranks, &outfp);

  /* read global header*/
  sion_seek(outsid, 0, SION_CURRENT_BLK, SION_CURRENT_POS);
  sion_fread(info_glob, sizeof(_infostruct), 1, outsid);
  print_infostruct(info_glob);

  size               = info_glob->width * info_glob->height;
  *iterations        = malloc(size * sizeof(int));
  *proc_distribution = malloc(size * sizeof(int));

  /* ignore Master-task when using master-worker scheme */
  if (info_glob->type == 2) {
    task = 1;
  }
  else {
    task = 0;
  }

  for (; task < ntasks; ++task) {

    /* move to task position in SION file */
    sion_seek(outsid, task, SION_CURRENT_BLK, SION_CURRENT_POS);

    while (! sion_feof(outsid)) {
      /* read info header */
      sion_fread(&info, sizeof (_pos_struct), 1, outsid);

      /* read data */
      size   = info.width * info.height;
      buffer = malloc(size * sizeof (int));
      sion_fread(buffer, sizeof (int), size, outsid);

      /* store data inside global data file */
      i = 0;
      for (ypos=info.ypos; ypos < info.ypos + info.height; ++ypos) {
        for (xpos=info.xpos; xpos < info.xpos + info.width; ++xpos) {
          (*iterations)[ypos*info_glob->width + xpos] = buffer[i++];
          (*proc_distribution)[ypos*info_glob->width + xpos] = task;
        }
      }
      free(buffer);
    }
  }

  free(chunksizes);
  free(globalranks);

  /* close SION file */
  sion_close(outsid);
}
