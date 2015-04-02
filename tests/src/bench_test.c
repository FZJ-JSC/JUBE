#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
  printf("%s: %02d\n","Hello World",atoi(argv[1]));
  printf("%s: %02d\n","Hello World",atoi(argv[1])+1);
  printf("%s: %02d\n","Hello World",atoi(argv[1])+2);
  return EXIT_SUCCESS;
}

