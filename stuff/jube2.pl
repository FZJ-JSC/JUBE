#!/usr/bin/perl -w
#
#####################################################################################
#                                                                                   #
#        JuBE: Juelich Benchmarking Environment                                     #
#                                                                                   #
#####################################################################################


#   Copyright (C) 2010, Forschungszentrum Juelich GmbH, Federal Republic of
#   Germany. All rights reserved.
#
#   Redistribution and use in source and binary forms, with or without
#   modification, are permitted provided that the following conditions are met:
#
#   Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
#     - Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#
#     - Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#
#     - Any publications that result from the use of this software shall
#       reasonably refer to the Research Centre's development.
#
#     - All advertising materials mentioning features or use of this software
#       must display the following acknowledgement:
#
#           This product includes software developed by Forschungszentrum
#           Juelich GmbH, Federal Republic of Germany.
#
#     - Forschungszentrum Juelich GmbH is not obligated to provide the user with
#       any support, consulting, training or assistance of any kind with regard
#       to the use, operation and performance of this software or to provide
#       the user with any updates, revisions or new versions.
#
#
#   THIS SOFTWARE IS PROVIED BY FORSCHUNGSZENTRUM JUELICH GMBH "AS IS" AND ANY
#   EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#   WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#   DISCLAIMED. IN NO EVENT SHALL FORSCHUNGSZENTRUM JUELICH GMBH BE LIABLE FOR
#   ANY SPECIAL, DIRECT OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER
#   RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF
#   CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN
#   CONNECTION WITH THE ACCESS, USE OR PERFORMANCE OF THIS SOFTWARE.


use strict;
use Carp;
use FindBin;
use Data::Dumper;
my $instpath="$FindBin::RealBin";
use Getopt::Long qw(:config no_ignore_case);

use JuBE::Bench_Manager;
use JuBE::Benchmark_Manager;
use JuBE::Platform_Manager;
use JuBE::Step_Handler;
use JuBE::Logger;
use JuBE::File_Manager;
use JuBE::Substitute_Engine;

use Util::HashSearch;

my($debug)=3;

my $patint="([\\+\\-\\d]+)";    # Pattern for Integer number
my $patfp ="([\\+\\-\\d.Ee]+)"; # Pattern for Floating Point number
my $patwrd="([\^\\s]+)";        # Pattern for Work (all noblank characters)
my $patnint="[\\+\\-\\d]+";     # Pattern for Integer number, no () 
my $patnfp ="[\\+\\-\\d.Ee]+";  # Pattern for Floating Point number, no () 
my $patnwrd="[\^\\s]+";         # Pattern for Work (all noblank characters), no () 
my $patbl ="\\s+";              # Pattern for blank space (variable length)

my $pwd=`pwd`;
chomp($pwd);

my($logger_main);
my $benchxmlfile;

# Defaults
my $opt_verbose=0;
my $opt_debug=undef;
my $opt_result=undef;
my $opt_start=undef;
my $opt_configdir="$pwd/Benchmarks";

usage($0) if( ! GetOptions( 
			    'verbose=i'        => \$opt_verbose,
			    'debug'            => \$opt_debug,
			    'result'           => \$opt_result,
			    'start|submit'     => \$opt_start
			    ) );

my $platformfile="$opt_configdir/platform.xml";

# Logger
$logger_main=Logger->new();
$logger_main->log("general",{name => "benchxmlfile",  value => $benchxmlfile},"NOSUB" );
#$logger_main->readfromfile("logit.out1");
$logger_main->writetofile("logit.out1b");

# Work
if($opt_start) {
    # submit new benchmarks
    if(!$ARGV[0]) {
	if(-f "$opt_configdir/pepc.xml") {
	    $benchxmlfile="$opt_configdir/pepc.xml";
	} else {
	    usage($0);
	}
    } else {
	$benchxmlfile=$ARGV[0];
    }
} 

# Bench-XML
my $bench=Bench_Manager->new($benchxmlfile) if ($opt_start);
$bench->write_tree if ($debug>3);

# Get Platform
my $platform=$bench->get_platform;
print "$platform ist Platform!!!!!!\n" if ($debug>4);

# Substitute-Engine
my $substitute_engine=Substitute_Engine->new($platform);
$substitute_engine->print_subhash if ($debug>4);

# Platform-Definitions
my $platformmngr=Platform_Manager->new($platformfile,$platform,$substitute_engine);
print Dumper($platformmngr) if ($debug>4);    
$substitute_engine->print_subhash if ($debug>4);  
my $platformdefhash=$platformmngr->get_machine_def;
if ($debug>4) {
    foreach my $paramprint (keys %$platformdefhash) {
	print "$paramprint $platformdefhash->{$paramprint}\n";
    } 
}
my $platform_value=$platformmngr->get_make;
print "Value: $platform_value\n" if ($debug>4);

# Execute Benchmark
my $all_benchmarks=$bench->get_benchmarks;
my $benchmark;
my @active_benchmarks;
my $param_space;
foreach my $bm (@$all_benchmarks){
    $benchmark=Benchmark_Manager->new($bench,$bm,$substitute_engine);
    push (@active_benchmarks,$benchmark->get_name) if ($benchmark->is_active);
    # Build Parameterspace
    $benchmark->build_paramspace if ($benchmark->is_active);      
#    $benchmark->print_paramspace if ($benchmark->is_active);      
    $param_space=$benchmark->get_paramspace if ($benchmark->is_active);      
#    foreach my $elem (keys %{$param_space->[0]}) {
#	print ">> $param_space->[0]->{$elem}\n";
#    }
}


if (@active_benchmarks==0) {
    croak "no active benchmark\n";
} elsif (@active_benchmarks>1) {
    croak "more than one active benchmark\n";
} else {
    my $benchmark_name=shift @active_benchmarks;
    print "$benchmark_name ist aktiv!!!!!!\n" if ($debug>3);    
    # Handle Steps
    my $stephandler=Step_Handler->new($bench,"compile",$substitute_engine,$param_space);
    $stephandler->handle_actions;
} 



sub usage {
    die "Usage: $_[0] <options> <xml-file> <id-range>

                -start, -submit *  : submit new set of benchmark runs (defined in xml-file) 
                -result         +  : shows results of benchmark runs (tables) 
                -verbose level     : verbose
                -debug             : don't submit jobs
      * : needs XML top level file  <xml-file>
      + : a range of benchmark run ids can be specified <id-range>

";
}
