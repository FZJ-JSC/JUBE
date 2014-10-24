/*

  tools.c

  Th.Eickermann

  based upon Rudolf Berrendorf's 'mpi_send'

*/


/*
 *  call timing-functions 
 */

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <strings.h>
#include <assert.h>
#include <math.h>

#if defined(_SOLARIS)
#include <unistd.h>
#include <sys/times.h>
#include <limits.h>

#elif defined(_LINUX)
#include <unistd.h>
#include <sys/time.h>
#include <time.h>
#include <limits.h>

#elif defined(_CRAYT3E) || defined(_CRAYT90)
#include <unistd.h>
#include <sys/times.h>

#elif defined(_AIX) || defined(_IRIX64)
#include <time.h>
#include <sys/types.h>
#include <sys/times.h>
#include <sys/time.h>
#endif

#include "PaRatools.h"

double clock_overhead(int num_loop_outer) {
  double t0, t1, tover;
  int loop_outer;
  
  /* get clock overhead */
  tover = 0;
  for(loop_outer=0;loop_outer<num_loop_outer; ++loop_outer) {
    t0 = zam_esecond();
    t0 = zam_esecond();
    t1 = zam_esecond();
    tover += zam_difftime(t0, t1);
  }
  tover /= num_loop_outer;

  return tover;
}


double zam_difftime(double t0, double t1)
{
#if defined(_CRAYT3E_GAGA)
  return (t1 - t0) / (double) sysconf(_SC_CLK_TCK);
#else
  return t1 - t0;
#endif
}


double zam_esecond(void) {
#if defined(OSF1_ALPHA) || defined(NETBSD) || defined(_LINUX) || defined(_SOLARIS4) || defined(_IRIX64)
  {
    struct timeval tp;
    struct timezone tzp;

    gettimeofday(&tp, &tzp);
    return tp.tv_sec + (tp.tv_usec * 1e-6);
  }


#elif defined(_SOLARIS)
  {
    hrtime_t gethrtime(void);
    return gethrtime() * 1e-9;
  }


#elif defined(BSD)
  {
    struct timeval tp;
    gettimeofday(&tp);
    return tp.tv_sec + (tp.tv_usec * 1e-6);
  }
  

#elif defined(_CRAYT3E) || defined(_CRAYT90)
  {
    static int first_esecond = 1;
    static int initial_ticks;
    static double ticks;

    if (first_esecond)
      {
	first_esecond = 0;
	ticks = 1.0 / (double) sysconf(_SC_CLK_TCK);
	initial_ticks = _rtc();
      }
    return (_rtc() - initial_ticks) * ticks;
  }


#elif defined(IRIX)
  {
#if IO4_TIMER_IS_64BIT
    typedef unsigned long long iotimer_t;
#else
    typedef unsigned int iotimer_t;
#endif
    __psunsigned_t phys_addr, raddr;
    unsigned int cycleval;
    int fd, poffmask;
    static int first_esecond = 1;
    static double ticks;
    static volatile iotimer_t *iotimer_addr;

    if(first_esecond)
      {
	first_esecond = 0;
	poffmask = getpagesize() - 1;
	phys_addr = syssgi(SGI_QUERY_CYCLECNTR, &cycleval);
	/* cycles in picoseconds */
	ticks = cycleval * 1e-12;
	raddr = phys_addr & ~poffmask;
	fd = open("/dev/mmem", O_RDONLY);
	iotimer_addr = (volatile iotimer_t *)mmap(0, poffmask, PROT_READ,
						  MAP_PRIVATE, fd,
						  (__psint_t)raddr);
	iotimer_addr = (iotimer_t *)((__psunsigned_t)iotimer_addr
				     + (phys_addr & poffmask));
      }
    return *iotimer_addr * ticks;
  }

#elif defined(_AIX)
  {
  static int first=1;
  static timebasestruct_t tstart;
  timebasestruct_t tact;

  if(first==1) {
    read_real_time(&tstart,TIMEBASE_SZ);
    time_base_to_time(&tstart,TIMEBASE_SZ);
    first=0;
  }

  read_real_time(&tact,TIMEBASE_SZ);
  time_base_to_time(&tact,TIMEBASE_SZ);

  return (double)(tact.tb_high-tstart.tb_high) + ((double)tact.tb_low-(double)tstart.tb_low) * 1.e-9;
}

#elif (defined(IPSC860) || defined(DELTA) || defined(OSF1_PARAGON))
  {
    double dclock();
    return dclock();
  }


#elif defined(KSR)
  return all_seconds();


#else
#error "something wrong"
#endif
}


/*
 * generate a string that contains the
 * current date and time
 */
void sprint_date(char *text, int len) {
  const struct tm *mytm;
  time_t clock;

  clock = time(NULL);
  mytm = localtime(&clock);
  strftime(text, len, "%x %T", mytm);
}

/*
 * allocate a 2D-array
 */
int **alloc_2d(int n, int m) {
  int i,**a;

  a = (int **)malloc(n*sizeof(int *));
  assert( a != NULL);

  a[0] = malloc(n*m*sizeof(int));
  assert( a[0] != NULL);

  for(i=1;i<n;i++)
    a[i] = a[i-1] + m;

  return a;
}

/*
 * read a config-file as created by 'mkconf.pl'
 *
 */
int read_configfile(char *ini_file, int mode, int *n_print, int ***print_specs,
		    int *n_bench, int ***bench_specs,
		    double *time_unit, double *bandwidth_unit, char **comments) {

  FILE *ini;
  char line[256],*ptr,*eptr,*cptr;
  int state,i,csize,cidx,ibench;

  /* an array for comments */
  csize=1024;
  cidx=0;
  cptr = malloc(csize);
  assert(cptr != NULL);

  if( mode == 'F' ) {
    char cmd[1024];
    sprintf(cmd,"%s %s -o /tmp/pp.ini", MKCONF, ini_file);
    if( system(cmd) != 0 ) {
      fprintf(stderr, "failed to create inifile from specs-file '%s'\n",ini_file);
      return 0;
    }
    ini_file = "/tmp/pp.ini";
  }
  ini = fopen(ini_file, "r");
  if( ! ini ) {
    fprintf(stderr,"cannot open inifile: '%s'\n",ini_file);
    perror("open inifile");
    return 0;
  }

  ibench=0;
  state = 0; /* waiting for numbers */
  while( fgets(line, 256, ini) ) {
    if( strncmp(line, "#%", 2) == 0 ) {
      /* a comment that should appear in the output-file */
      if( csize - cidx < strlen(line) ) {
	cptr = realloc(cptr, csize + 1024);
	assert(cptr != NULL);
      }
      strcat(cptr,"#");
      strcat(cptr, line+2);
      cidx += strlen(line)-1;
    } else {
      /* strip comments */
      char *c;

      if( (c=index(line, '#')) ) {
	*(c--) = '\0';
	
	while( c >= line ) {
	  if( strchr(" \t\n", *c) ) {
	    *(c--) = '\0';
	  } else {
	    break;
	  }
	}
      }
      if( *line != '\0' ) {
	/* remaining line is not empty */
	switch( state ) {
	case 0:
	  /* expecting n_print, n_bench */
	  if( sscanf(line, "%d %d",n_print,n_bench) != 2 ) {
	    fprintf(stderr,"parse error in configfile, line =\n%s",line);
	    fprintf(stderr,"expecting 2 integer values\n");
	    return 0;
	  } else {
	    *print_specs = alloc_2d(*n_print, 2);
	    *bench_specs = alloc_2d(*n_bench, 6);
	    state = 1;
	  }
	  break;
	case 1:
	  /* expecting print-specs */
	  ptr = line;
	  for(i=0; i<*n_print; i++) {
	    (*print_specs)[i][0] = strtol(ptr, &eptr, 10);
	    if( eptr == ptr ) {
	      fprintf(stderr,"parse error in configfile, line =\n%s",line);
	      fprintf(stderr,"expecting 2 * %d integer values (printspecs)\n",*n_print);
	      return 0;
	    }
	    ptr=eptr;
	    (*print_specs)[i][1] = strtol(ptr, &eptr, 10);
	    if( eptr == ptr ) {
	      fprintf(stderr,"parse error in configfile, line =\n%s",line);
	      fprintf(stderr,"expecting 2 * %d integer values (printspecs)\n",*n_print);
	      return 0;
	    }
	    ptr=eptr;
	  }
	  state = 2;
	  break;
	case 2:
	  /* expecting unit-specs */
	  if( sscanf(line, "%lg %lg", time_unit, bandwidth_unit) != 2 ) {
	    fprintf(stderr,"parse error in configfile, line =\n%s",line);
	    fprintf(stderr,"expecting 2 float values (unitspecs)\n");
	    return 0;
	  }
	  state = 3;
	  break;
	case 3:
	  /* expecting benchmark-specs */
	  if( sscanf(line, "%d %d %d %d %d %d",
		    (*bench_specs)[ibench],
		    (*bench_specs)[ibench]+1,
		    (*bench_specs)[ibench]+2,
		    (*bench_specs)[ibench]+3,
		    (*bench_specs)[ibench]+4,
		    (*bench_specs)[ibench]+5) != 6 ) {
	    fprintf(stderr,"parse error in configfile, line =\n%s",line);
	    fprintf(stderr,"expecting 7 integer values (benchspecs)\n");
	    return 0;
	  }
	  ibench++;
	  if(ibench == *n_bench ) state = 4;
	  break;
	case 4:
	  fprintf(stderr,"parse error in configfile, line =\n%s",line);
	  fprintf(stderr,"extra line after complete (and valid) file\n");
	  return 0;
	}
      }
    }
  }
  *comments = cptr;

  return 1;
}

void ini_stat(struct stats *s) {
  s->n    = 0;
  s->sum  = 0.;
  s->sum2 = 0.;
  s->min  = 0.;
  s->max  = 0.;
}

void add_stat(struct stats *s, double val) {
  if( s->n == 0 ) {
    s->min = val;
    s->max = val;
  } else {
    s->min = s->min < val ? s->min : val;
    s->max = s->max > val ? s->max : val;
  }

  s->sum  += val;
  s->sum2 += val*val;

  s->n++;
}

double get_stat_min(struct stats *s) { return s->min; }
double get_stat_max(struct stats *s) { return s->max; }
double get_stat_avg(struct stats *s) { return s->n > 0 ? s->sum / s->n : 0.; }
double get_stat_dev(struct stats *s) { 
  if( s->n == 0 ) {
    return 0;
  } else {
    return sqrt((s->sum2 - s->sum*s->sum/s->n)/s->n);
  }
}
 int get_stat_n(struct stats *s) { return s->n; }

/* Fortran interfaces */
double fzam_esecond()
{
    return (zam_esecond());
}

double fzam_esecond_()
{
    return (zam_esecond());
}

double fzam_esecond__()
{
    return (zam_esecond());
}

double FZAM_ESECOND()
{
    return (zam_esecond());
}
