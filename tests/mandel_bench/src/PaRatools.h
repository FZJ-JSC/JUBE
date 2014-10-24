/*
 
  declatations for functions in tools.c

*/

#define MKCONF "./mkconf.pl"

double clock_overhead(int num_loop_outer);
double zam_difftime(double t0, double t1);
double zam_esecond(void);
void sprint_date(char *text, int len);
int **alloc_2d(int n, int m);
int read_configfile(char *ini_file, int mode, int *n_print, int ***print_specs,
		    int *n_bench, int ***bench_specs,
		    double *time_unit, double *bandwidth_unit, char **comments);

struct stats {
  int n;
  double sum;
  double sum2;
  double min;
  double max;
};

void ini_stat(struct stats *stat);
void add_stat(struct stats *stat, double val);
double get_stat_min(struct stats *stat);
double get_stat_max(struct stats *stat);
double get_stat_avg(struct stats *stat);
double get_stat_dev(struct stats *stat);
int get_stat_n(struct stats *stat);
